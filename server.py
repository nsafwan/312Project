from flask import Flask, send_from_directory, request, make_response
from pymongo import MongoClient


mongo_client = MongoClient("localhost") #This should be changed to mongo for docker
db = mongo_client["cse312"] #Creating a mongo database called cse312
post_collection = db["posts"] #Collection of all the posts should be in the format (username, title, description). Username is entered by us through auth.
user_collection = db["users"] #Collection of all the users. Should be in the format (username, shpassword, auth)


post_collection.insert_one({"username": "Test User", "title": "Test Title", "description": "Test description"})
all_posts = post_collection.find({})
array = list(all_posts)
print(array)



# app = Flask(__name__)
#
# @app.route('/')
# def serve_index():
#    return send_from_directory('public', 'index.html')
#
# @app.route('/public/<path:resource>')
# def serve_file(resource):
#     return send_from_directory('public', resource)
#
#
# @app.after_request
# def apply_nosniff(response):
#     response.headers['X-Content-Type-Options'] = 'nosniff'
#     return response
#
#
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=8080)

