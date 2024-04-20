from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import psycopg2
import json
import marqo
from minio import Minio
from dotenv import load_dotenv
import os

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
)

mq = marqo.Client(url=os.getenv('MARQO_URL'))

# Called with the file name from MinIO
def get_file_from_minio(file_name):
    # Get the file from MinIO
    file_data = minio_client.get_object(
        os.getenv('MINIO_BUCKET'),
        file_name
    )
    return file_data

@app.route('/')
def hello():
    return 'Hello world with Flask'

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        # The response for the 'OPTIONS' preflight request is automatically handled by flask-cors
        return {}
    elif request.method == 'POST':
        credentials = request.get_json()
        print(credentials)
        # Here, you would typically check the credentials against a database
        return jsonify({"status": "success", "message": "Login successful!"})

@app.route('/register', methods=['POST'])
def register():
    # Get registration data from the request
    registration_data = request.get_json()
    
    # Extract and validate the data here...
    name = registration_data.get('name')
    email = registration_data.get('email')
    password = registration_data.get('password')
    terms_agreed = registration_data.get('termsAgreed', False)
    
    # Check if all the fields are provided
    if not all([name, email, password, terms_agreed]):
        return jsonify({"status": "error", "message": "Missing fields or terms not agreed."}), 400
    
    # Here, you would save the user data to a database, for example:
    # new_user = User(name=name, email=email, password=hashed_password)
    # db.session.add(new_user)
    # db.session.commit()

    # Assuming everything went well:
    return jsonify({"status": "success", "message": "Registration successful!"}), 201
