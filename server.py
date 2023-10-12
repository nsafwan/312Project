from flask import Flask, send_from_directory, request, make_response
from pymongo import MongoClient


mongo_client = MongoClient("localhost") #This should be changed to mongo for docker
db = mongo_client["cse312"] #Creating a mongo database called cse312


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


post_collection.insert_one({"username": "Test User", "title": "Test Title", "description": "Test description", "likes": 0, "postnumber": 1})
user_collection.insert_one({"username": "Test User", "shpassword": "Test salted hashed password", "auth": "Test salted auth", "liked": [1]})



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


@app.after_request
def apply_nosniff(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

