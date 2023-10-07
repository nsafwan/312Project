from flask import Flask, send_from_directory, request, make_response
from pymongo import MongoClient

mongo_client = MongoClient("localhost")
db = mongo_client["cse312"]
chat_collection = db["chat"]

app = Flask(__name__)

@app.route('/')
def serve_index():
   return send_from_directory('public', 'index.html')

@app.route('/public/<path:resource>')
def serve_file(resource):
    return send_from_directory('public', resource)


@app.after_request
def apply_nosniff(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

