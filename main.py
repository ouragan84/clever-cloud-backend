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
    
