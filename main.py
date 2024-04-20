from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

app = Flask(__name__)


# Allow all origins for all routes. 
# In production, you would change this to be more restrictive.
CORS(app, resources={r"/*": {"origins": "*"}})


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
