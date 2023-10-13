from flask import Flask, send_from_directory, request, make_response
from pymongo import MongoClient
import bcrypt
from uuid import uuid4  # used to generate auth token

mongo_client = MongoClient("localhost")  # This should be changed to mongo for docker
db = mongo_client["cse312"]  # Creating a mongo database called cse312

"""
Collection of all the users
Format: (username, shpassword, auth, liked)
shpassword is the salted hashed password of the user.
auth is the hased auth token of the user.
liked is an array of all the postnumber that the user has liked (starts off with an empty array).
"""
user_collection = db["users"]

"""
Collection of all the posts.
Format: (username, title, description, likes, postnumber)
You can assume each post has a unique postnumber.
Likes attribute stores the total number of likes this post has.
"""
post_collection = db["posts"]

post_collection.insert_one(
    {"username": "Test User", "title": "Test Title", "description": "Test description", "likes": 0, "postnumber": 1})
user_collection.insert_one(
    {"username": "Test User", "shpassword": "Test salted hashed password", "auth": "Test salted auth", "liked": [1]})

app = Flask(__name__)


@app.route('/')
def serve_index():
    return send_from_directory('public', 'index.html')


@app.route('/public/<path:resource>')
def serve_file(resource):
    return send_from_directory('public', resource)


@app.route("/submit-post", methods=["POST"])
def submit_post():
    # get title and description of post
    post_data = request.get_json()
    title = post_data["title"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    description = post_data["description"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Check to see if user is authenticated
    # search for auth token cookie
    auth_token_cookie_name = "auth-token"
    if auth_token_cookie_name in request.cookies:
        request_auth_token = request.cookies.get(auth_token_cookie_name)
        # hashed_request_auth_token needs to be calculated
        hashed_request_auth_token = request_auth_token
        user = user_collection.find_one({"auth": hashed_request_auth_token})
        if user:
            username = user["username"]
            # pstnumber needs to be calculated
            postnumber = 2
            post_collection.insert_one({
                "username": username,
                "title": title,
                "description": description,
                "likes": 0,
                "postnumber": postnumber
            })
            return "Successfully posted"

    # User not authenticated. Post not submitted. Status code 401
    return "Unauthenticated", 401


@app.route("/register", methods=["POST"])
def register():
    data = request.form
    # assuming same form input names as hw2 html (username_reg and password_reg)
    username = data["username_reg"]
    shpassword = bcrypt.hashpw(data["password_reg"].encode(), bcrypt.gensalt())
    existing_user = user_collection.find_one({"username": username})
    if existing_user:
        return "Username Taken", 400
    else:
        user_collection.insert_one({"username": username, "shpassword": shpassword})
        return "New User Registered"

@app.route("/login", methods=["POST"])
def login():
    response = make_response("User Logged In")
    data = request.form
    # assuming same form input names as hw2 html (username_login and password_login)
    username = data["username_login"]
    existing_user = user_collection.find_one({"username": username})
    if existing_user and bcrypt.checkpw(data["password_login"].encode(), existing_user["shpassword"]):
        auth = str(uuid4())  # generate auth token
        response.set_cookie('auth_token', auth, httponly=True, max_age=3600)  # set cookie of un-hashed auth token
        auth = bcrypt.hashpw(auth.encode(), bcrypt.gensalt())  # hash byte string of auth token
        auth = {"$set": {"auth": auth}}  # create new dict element to add to database entry
        user_collection.update_one({"username": username}, auth)  # add auth token to user entry
        return response
    else:
        return "Incorrect Username or Password", 400

@app.after_request
def apply_nosniff(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
