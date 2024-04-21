from flask import Flask, request, jsonify, redirect, url_for, send_file
from flask_cors import CORS, cross_origin
import psycopg2
import json
import marqo
from minio import Minio
from dotenv import load_dotenv
import os
import random
import string
import time
from werkzeug.utils import secure_filename
import io

import torch
from PIL import Image
from transformers import AlignProcessor, AlignModel
import numpy as np
from sklearn.decomposition import PCA
from pinecone import Pinecone, ServerlessSpec

import jwt
import datetime
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

import PyPDF2



app = Flask(__name__)

# Setup JWT
app.config["JWT_SECRET_KEY"] = os.getenv('JWT_SECRET_KEY')  # Change this to a real secret in production
jwt = JWTManager(app)


# Allow all origins for all routes. 
# In production, you would change this to be more restrictive.
CORS(app, resources={r"/*": {"origins": "*"}})

# ./tmp is the folder where files will be temporarily stored before uploading to MinIO
UPLOAD_FOLDER = './tmp'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# Load environment variables from .env file
load_dotenv()

# Connect to the database
db_connect = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    database=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    port=os.getenv('POSTGRES_PORT')
)

# Connect to MinIO
minio_client = Minio(
    os.getenv('MINIO_URL'),
    access_key=os.getenv('MINIO_ACCESS_KEY'),
    secret_key=os.getenv('MINIO_SECRET_KEY'),
    secure=False 
)

# Make the bucket if it doesn't exist.
bucket_name = os.getenv('MINIO_BUCKET')
found = minio_client.bucket_exists(bucket_name)
if not found:
    minio_client.make_bucket(bucket_name)
    print("Created bucket", bucket_name)
else:
    print("Bucket", bucket_name, "already exists")

# Connect to Marqo
# mq = marqo.Client(url=os.getenv('MARQO_URL'))

# Connect to Pinecone
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

pc_index_name="clever-cloud-demo"
if not pc_index_name in pc.list_indexes().names():
    pc.create_index(
        name=pc_index_name,
        dimension=640, # Replace with your model dimensions
        metric="dotproduct", # Replace with your model metric
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        ) 
    )
else:
    print(f"Index {pc_index_name} already exists.")

pc_index = pc.Index(pc_index_name)

# Initialize processor and model
embedding_processor = AlignProcessor.from_pretrained("kakaobrain/align-base")
embedding_model = AlignModel.from_pretrained("kakaobrain/align-base")


def generate_text_embedding(text):
    text_inputs = embedding_processor(text=text, return_tensors="pt")
    text_embeds = embedding_model.get_text_features(**text_inputs).detach().numpy().tolist()[0]
    # normalize the embeddings to unit length
    text_embeds /= np.linalg.norm(text_embeds)
    # convert to list
    text_embeds = text_embeds.tolist()
    return text_embeds

def generate_image_embedding(image_path):
    image = Image.open(image_path).convert('RGB')
    image_inputs = embedding_processor(images=image, return_tensors="pt")
    image_embeds = embedding_model.get_image_features(**image_inputs).detach().numpy().tolist()[0]
    # normalize the embeddings to unit length
    image_embeds /= np.linalg.norm(image_embeds)
    # convert to list
    image_embeds = image_embeds.tolist()
    return image_embeds



# Initialize PCA
pca = PCA(n_components=3)

# Train PCA function
def train_pca():
    # Generate a set of random texts and/or images to create initial embeddings for PCA training
    sample_texts = [
        "a beige puppy sitting in the grass",
        "Movie review: The movie was a great success",
        "The cat in the hat",
        "A story about children playing in the park",
        "A dog sitting in the grass",
        "Facts about the moon",
        "History of the United States",
        "A recipe for chocolate cake",
        "The best places to visit in the world",
        "The best restaurants in New York City",
        "Physics Homework: Newton's Laws of Motion",
        "The life of Albert Einstein",
        "The history of the internet",
        "Tax summary for 2021",
        "Insurance policy for homeowners",
    ]
    embeddings = []
    for text in sample_texts:
        embeddings.append(generate_text_embedding(text))
    
    # Fit PCA on collected embeddings
    pca.fit(np.array(embeddings))

def get_pca_representation(embeddings):
    pca_rep = pca.transform(embeddings)

    # convert to list of strings ['1.234', '2.345', '3.456']
    pca_rep = [str(val) for val in pca_rep[0]]
    return pca_rep

train_pca()




@app.route('/')
def hello():
    return 'Hello world with Flask'

@app.route('/login', methods=['POST'])
def login():
    credentials = request.get_json()
    email = credentials.get('email')
    provided_hash = credentials.get('password')

    if not all([email, provided_hash]):
        return jsonify({"status": "error", "message": "Missing email or password."}), 400

    cur = db_connect.cursor()
    try:
        cur.execute("SELECT password FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        if user is None:
            return jsonify({"status": "error", "message": "User not found."}), 404

        stored_hash = user[0]
        if stored_hash == provided_hash:
            access_token = create_access_token(identity=email)
            return jsonify(access_token=access_token), 200
        else:
            return jsonify({"status": "error", "message": "Invalid credentials."}), 401
    finally:
        cur.close()
        
@app.route('/register', methods=['POST'])
def register():
    registration_data = request.get_json()
    name = registration_data.get('name')
    email = registration_data.get('email')
    hashed_password = registration_data.get('password')
    terms_agreed = registration_data.get('termsAgreed', False)

    if not all([name, email, hashed_password, terms_agreed]):
        return jsonify({"status": "error", "message": "All fields must be filled and terms agreed."}), 400

    cur = db_connect.cursor()
    try:
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                    (name, email, hashed_password))
        db_connect.commit()
        access_token = create_access_token(identity=email)
        return jsonify(access_token=access_token), 201
    except psycopg2.IntegrityError:
        db_connect.rollback()
        return jsonify({"status": "error", "message": "Email already registered."}), 409
    finally:
        cur.close()

@app.route('/print-user-columns', methods=['GET'])
def print_user_columns():
    # Define the cursor to interact with the database
    cur = db_connect.cursor()
    
    # Execute the query to get column names from the 'user' table
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'user'
    """)
    
    # Fetch all the results
    columns = cur.fetchall()
    
    # Close the cursor to avoid memory leaks
    cur.close()

    # Extract column names from the query result
    column_names = [col[0] for col in columns]

    # Print the column names to the console (or you could return them)
    print("Column names in 'user' table:", column_names)
    
    # Return the column names as a JSON response, for example
    return jsonify({"status": "success", "columns": column_names})

@app.route('/get-all-users', methods=['GET'])
def get_all_users():
    # Define the cursor to interact with the database
    cur = db_connect.cursor()
    
    try:
        # Execute the query to get all data from the 'users' table
        cur.execute("SELECT * FROM users")
        
        # Fetch all the results
        users_data = cur.fetchall()

        # Define the columns you expect (or retrieve them as in previous example)
        columns = [desc[0] for desc in cur.description]

        # Convert the data to a list of dictionaries for easier processing and reading
        users = []
        for user in users_data:
            users.append(dict(zip(columns, user)))

        # Print the users to the console (for debugging purposes - you might not want this in production)
        print("Users Data:", users)
        
    except Exception as e:
        print("An error occurred:", e)
        return jsonify({"status": "error", "message": "An error occurred while fetching the users."}), 500
    finally:
        # Make sure to close the cursor and the connection
        cur.close()
    
    # Return the users data as a JSON response
    return jsonify({"status": "success", "users": users})


@app.route('/upload-file', methods=['POST'])
# @jwt_required()
def upload_file():
    print("Uploading file...")
    file = request.files.get('file')

    if not file:
        return jsonify({"status": "error", "message": "No file part"}), 400
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    if not file or not allowed_file(file.filename):
        return jsonify({"status": "error", "message": "File extension not allowed"}), 400
    

    filename = secure_filename(file.filename)
    minio_file_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], minio_file_name)
    extension = filename.split('.')[-1].lower()
    date_uploaded = int(time.time())
    type =  'image' if extension in ['jpg', 'jpeg', 'png', 'gif'] else \
            'document' if extension in ['pdf', 'doc', 'docx', 'txt'] else \
            'other'
    
    user_created = "user@example.com" #TODO: Get the user from the session
    # user_created = get_jwt_identity()

    try:
        # Saving locally first (optional depending on your use case)
        file.save(file_path)
        # Then upload to MinIO
        with open(file_path, 'rb') as f:
            minio_client.put_object(
                bucket_name,
                minio_file_name,
                f,
                os.path.getsize(file_path),
                file.content_type
            )
    except Exception as e:
        os.remove(file_path)  # Remove the temporary file
        return jsonify({"status": "error", "message": str(e)}), 500
    

    print("File uploaded to MinIO:", minio_file_name)

    content_embedding = []
    if type == 'image':
        content_embedding = generate_image_embedding(file_path)
    if type == 'document':
        if extension == 'pdf':
            with open(file_path, 'rb') as pdf_file:
                read_pdf = PyPDF2.PdfReader(pdf_file)
                number_of_pages = len(read_pdf.pages)
                text = ""
                for page_number in range(number_of_pages):
                    page = read_pdf.pages[page_number]
                    text += page.extract_text()
                content_embedding = generate_text_embedding(text)
        else:
            with open(file_path, 'r') as f:
                text = f.read()
                content_embedding = generate_text_embedding(text)
    else:
        content_embedding = generate_text_embedding("File that is not an image or document")
        
    pca_representation = get_pca_representation([content_embedding])

    try:
        pc_index.upsert(
            vectors=[
                {
                    "id": minio_file_name,
                    "values": content_embedding, 
                    "metadata": {
                        "file_name": filename,
                        "date_uploaded": date_uploaded,
                        "type": type,
                        "user_created": user_created,
                        "pca_representation": pca_representation,
                        "date_modified": date_uploaded,
                        "id": minio_file_name,
                        "extension": extension
                    }
                }
            ],
            namespace="default"
        )
    except Exception as e:
        os.remove(file_path)
        return jsonify({"status": "error", "message": str(e)}), 500
    
    os.remove(file_path)  # Remove the temporary file
        
    return jsonify({"status": "success", "message": "File uploaded successfully"}), 201


empty_vector = [0.0] * 640

#Get all metadata
@app.route('/get-all', methods=['GET'])
def get_all():
    try:
        if pc_index is None:
            app.logger.error("pc_index is not initialized.")
            return jsonify({"status": "error", "message": "pc_index is not initialized"}), 500
        
        results = pc_index.query(vector=empty_vector, top_k=1000, namespace="default", include_metadata=True, include_values=False)
        # print(results.to_dict())
        # print(results.to_str())

        return jsonify(results.to_dict())
    except Exception as e:
        app.logger.exception("An error occurred while querying pc_index.")
        return jsonify({"status": "error", "message": str(e)}), 500



# # /get-file?id={file_name}
# @app.route('/get-file', methods=['GET'])
# def get_file():
#     # Get the file name from the query parameters
#     file_name = request.args.get('id')

#     if not file_name:
#         return jsonify({"status": "error", "message": "No file name provided."}), 400
    
#     # Get the file from MinIO
#     try:
#         file_data = minio_client.get_object(bucket_name, file_name)
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500

#     # Return the file data as a response
#     return file_data.read()

@app.route('/get-file', methods=['GET'])
def get_file():
    file_name = request.args.get('id')
    if not file_name:
        return jsonify({"status": "error", "message": "No file name provided."}), 400

    try:
        file_data = minio_client.get_object(bucket_name, file_name)
        file_stream = io.BytesIO(file_data.read())  # Read the file stream from MinIO and wrap it in a BytesIO object
        file_stream.seek(0)  # Reset stream position to the beginning
        return send_file(
            file_stream,
            as_attachment=True,
            download_name=file_name,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    # delete all the files in the tmp folder
    for file in os.listdir(UPLOAD_FOLDER):
        os.remove(os.path.join(UPLOAD_FOLDER, file))
    app.run(debug=True)

