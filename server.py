from flask import Flask, send_from_directory, request, redirect, url_for
from pymongo import MongoClient
import bcrypt
from uuid import uuid4  # used to generate auth token
from hashlib import sha256
import json

mongo_client = MongoClient("mongo")  # This should be changed to mongo for docker
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

"""
Only ever has a single value called unique_postnumber
"""
postnumbers_collection = db["postnumbers"]

# post_collection.insert_one(
#     {"username": "Test User", "title": "Test Title", "description": "Test description", "likes": 0, "postnumber": 1})
# user_collection.insert_one(
#     {"username": "Test User", "shpassword": "Test salted hashed password", "auth": "Test salted auth", "liked": [1]})

app = Flask(__name__)


@app.route('/')
def serve_index():
    return send_from_directory('public', 'index.html')

@app.route('/posts')
def serve_posts():
    return send_from_directory('public', 'posts.html')


@app.route('/public/<path:resource>')
def serve_file(resource):
    return send_from_directory('public', resource)

@app.route("/post-history")
def give_history():
    all_posts = list(post_collection.find({}))
    for eachpost in all_posts:
        #deleting the extraneous _id attribute.
        del eachpost['_id']
    all_posts = json.dumps(all_posts).encode()
    return all_posts



@app.route("/submit-post", methods=["POST"])
def submit_post():
    # get title and description of post
    post_data = request.data.decode()
    post_data = json.loads(post_data)
    title = post_data["title"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    description = post_data["description"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # print(post_data)

    postnumbers_list = list(postnumbers_collection.find({}))
    if not postnumbers_list:
        #if this is the first entry:
        postnumbers_collection.insert_one({"unique_postnumber": 2})
        postnumber = 1
    else:
        #getting unique_postnumber in db-> deleting all entries-> inserting the prevous unique_postnumber +1
        postnumber = postnumbers_list[0].get("unique_postnumber")
        postnumbers_collection.delete_many({})
        postnumbers_collection.insert_one({"unique_postnumber": postnumber + 1})

    # Check to see if user is authenticated
    # search for auth token cookie
    auth_token_cookie_name = "auth_token"
    if auth_token_cookie_name in request.cookies:
        request_auth_token = request.cookies.get(auth_token_cookie_name)
        # hashed_request_auth_token needs to be calculated
        hashed_request_auth_token = sha256(request_auth_token.encode()).hexdigest()
        user = user_collection.find_one({"auth": hashed_request_auth_token})
        if user:
            username = user["username"]
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
        print("Username Taken")
        return redirect(url_for('serve_index'))
    else:
        user_collection.insert_one({"username": username, "shpassword": shpassword, "auth": "", "liked": []})
        print("New User Registered")
        return redirect(url_for('serve_index'))

@app.route("/login", methods=["POST"])
def login():
    response = redirect(url_for('serve_index'))
    data = request.form
    # assuming same form input names as hw2 html (username_login and password_login)
    username = data["username_login"]
    existing_user = user_collection.find_one({"username": username})
    if existing_user and bcrypt.checkpw(data["password_login"].encode(), existing_user["shpassword"]):
        auth = str(uuid4())  # generate auth token
        response.set_cookie('auth_token', auth, httponly=True, max_age=3600)  # set cookie of un-hashed auth token
        auth = sha256(auth.encode()).hexdigest()  # hash byte string of auth token (.hexdigest() converts the hash object to a readable string of characters)
        auth = {"$set": {"auth": auth}}  # create new dict element to add to database entry
        user_collection.update_one({"username": username}, auth)  # add auth token to user entry
        print("User Logged In")
        return response
    else:
        print("Incorrect Username or Password")
        return redirect(url_for('serve_index'))

@app.after_request
def apply_nosniff(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.route("/like/<int:postnumber>", methods=["POST"])
def like_post(postnumber):
    # Check user authentication
    auth_token_name = "auth_token"
    if auth_token_name in request.cookies:
        request_auth_token = request.cookies.get(auth_token_name)
        hashed_request_auth_token = sha256(request_auth_token.encode()).hexdigest()
        user = user_collection.find_one({"auth": hashed_request_auth_token})
        if user:
            username = user["username"]
            post = post_collection.find_one({"postnumber": postnumber})
            if post:
                liked_post = user.get("liked", [])
                if postnumber in liked_post:
                    # User has already liked the post, so unlike it
                    liked_post.remove(postnumber)
                    # Updates with the postnumber of the unliked post
                    user_collection.update_one({"auth": hashed_request_auth_token}, {"$set": {"liked": liked_post}})
                    post_collection.update_one({"postnumber": postnumber}, {"$inc": {"likes": -1}})
                    return "unliked", 200
                else:
                    # Like the post
                    liked_post.append(postnumber)
                    # Updates with the postnumber of the liked post
                    user_collection.update_one({"auth": hashed_request_auth_token}, {"$set": {"liked": liked_post}})
                    post_collection.update_one({"postnumber": postnumber}, {"$inc": {"likes": 1}})
                    return "liked", 200
                
    # User not authenticated or post not found
    return "Unauthenticated or Post Not Found", 401


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
