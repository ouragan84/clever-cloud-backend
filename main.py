from flask import Flask, request, jsonify
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


app = Flask(__name__)


# Allow all origins for all routes. 
# In production, you would change this to be more restrictive.
CORS(app, resources={r"/*": {"origins": "*"}})


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
mq = marqo.Client(url=os.getenv('MARQO_URL'))

@app.route('/')
def hello():
    return 'Hello world with Flask'

@app.route('/login', methods=['POST'])
def login():
    credentials = request.get_json()
    email = credentials.get('email')
    provided_hash = credentials.get('password')  # Assuming this is the hash received from the frontend

    # Check if email and password(hash) are provided
    if not all([email, provided_hash]):
        return jsonify({"status": "error", "message": "Missing email or password."}), 400

    cur = db_connect.cursor()
    try:
        # Retrieve user by email
        cur.execute("SELECT password FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        # Check if the user was found
        if user is None:
            return jsonify({"status": "error", "message": "User not found."}), 404

        # User found, now compare the password hashes
        stored_hash = user[0]
        if stored_hash == provided_hash:
            # Hashes match, login success
            return jsonify({"status": "success", "message": "Login successful!"}), 200
        else:
            # Hashes do not match
            return jsonify({"status": "error", "message": "Invalid credentials."}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()  # Always close the cursor


@app.route('/register', methods=['POST'])
def register():
    # Get registration data from the request
    registration_data = request.get_json()

    # Extract and validate the data here...
    name = registration_data.get('name')
    email = registration_data.get('email')
    hashed_password = registration_data.get('password')  # Assuming this is already hashed by the frontend
    terms_agreed = registration_data.get('termsAgreed', False)
    
    # Check if all the fields are provided
    if not all([name, email, hashed_password, terms_agreed]):
        return jsonify({"status": "error", "message": "Missing fields or terms not agreed."}), 400

    # Insert the new user into the database
    cur = db_connect.cursor()
    try:
        # Use parameterized queries to prevent SQL injection
        cur.execute("""
            INSERT INTO users (name, email, password)
            VALUES (%s, %s, %s)
        """, (name, email, hashed_password))
        db_connect.commit()  # Commit the transaction
        return jsonify({"status": "success", "message": "Registration successful!"}), 201
    except psycopg2.IntegrityError:
        db_connect.rollback()  # Rollback the transaction on error
        return jsonify({"status": "error", "message": "This email is already registered."}), 409
    except Exception as e:
        db_connect.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()  # Close the cursor

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



@app.route('/upload-file', methods=['POST', 'OPTIONS'])
def upload_file():

    print("Uploading file...")
    # Get the file from the request
    file = request.files['file']

    if not file:
        print("No file provided.")
        return jsonify({"status": "error", "message": "No file provided."}), 400
    else:
        print("File provided:", file.filename)

    file_name = file.filename
    extention = file_name.split('.')[-1].lower()

    print("File name:", file_name)
    
    # get file type as document or image
    if extention in ['jpg', 'jpeg', 'png', 'gif']:
        file_type = 'image'
    elif extention in ['pdf', 'doc', 'docx', 'txt']:
        file_type = 'document'
    else:
        file_type = 'other'

    content_type = file.content_type

    file_size = file.content_length
    if file_size > 1024 * 1024 * 50:
        return jsonify({"status": "error", "message": "File size is too large. Max file size is 50MB."}), 400
    
    # Generate a random file name to store in MinIO
    minio_file_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

    date_uploaded = int(time.time())
    user_created = "example_user@gmail.com" # TODO: Get the user from the session

    print("Uploading file to MinIO:", minio_file_name)

    # Save the file to MinIO
    try:
        minio_client.put_object(
            bucket_name,
            minio_file_name,
            file,
            file.content_length,
            content_type
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
    # Save the file in marqo
    # TODO


# /get-file?id={file_name}
@app.route('/get-file', methods=['GET'])
def get_file():
    # Get the file name from the query parameters
    file_name = request.args.get('id')

    if not file_name:
        return jsonify({"status": "error", "message": "No file name provided."}), 400
    
    # Get the file from MinIO
    try:
        file_data = minio_client.get_object(bucket_name, file_name)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    # Return the file data as a response
    return file_data.read()


