# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Simple GET endpoint
@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello from Python!'})

# POST endpoint to receive data from frontend
@app.route('/api/process', methods=['POST'])
def process_data():
    data = request.json
    # Process your data here
    result = data.get('value', 0) * 2  # Example: double the value
    return jsonify({'result': result})

if __name__ == '__main__':
    app.run(debug=True, port=5000)