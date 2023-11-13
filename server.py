from flask import Flask, send_from_directory, request, redirect, url_for, render_template
from flask_socketio import SocketIO, emit
from pymongo import MongoClient
import bcrypt
from uuid import uuid4  # used to generate auth token
from hashlib import sha256
import json
import threading
import time
#mongo_client = MongoClient("mongo")
mongo_client = MongoClient("mongo")  # This should be changed to mongo for dockerZZ
db = mongo_client["cse312"]  # Creating a mongo database called cse312

"""
Collection of all the users
Format: (username, shpassword, auth, liked)
shpassword is the salted hashed password of the user.
auth is the hased auth token of the user.
liked is an array of all the postnumber that the user has liked (starts off with an empty array).
"""
user_collection = db["users"]
question_collection = db["questions"]
answer_collection = db["answers"]
postnumbers_collection = db["postnumbers"]
# postnumbers_collection is used to store questionId

# question_collection.insert_one(
#     {
#     "username": "Asker's Username",
#     "title": "Question Title",
#     "description": "Question Content",
#     "image": "name of associated image",
#     "answers": ["Red", "53", "Left", "1040"],
#     "correctAnswer": 0,
#     "grades": [],
#     "questionID": 1
#     "timerUp" : False     This is used to know whether a question has ended or not.
#     "timer" : 120         120 seconds in the beginning, used to store the time remaining for each question.
#     })

# answer_collection.insert_one(
#     {
#     "username": "Responders Username",
#     "questionID": 1,
#     "answer": 0
#     })

# user_collection.insert_one(
#     {
#     "username": "username",
#     "shpassword": "salted hashed password",
#     "auth": "Test salted auth",
#     "AnsweredQuestionsIDs": [1, 34, 325],
#     "answers": [3, 0, 1],
#     "grades": [1, 1, 0],
#     "askedQuestions"
#     })
app = Flask(__name__)
socketio = SocketIO(app, transports=['websocket'])

client_auths = {}  #Used for storing a client auths for websocket.

@app.route('/')
def serve_index():
    return send_from_directory('public', 'index.html')

@app.route('/posts')
def serve_posts():
    return send_from_directory('public', 'posts.html')

@app.route('/grades')
def serve_grades():
    return send_from_directory('public', 'grades.html')


@app.route('/public/image/<image_name>')
def serve_image(image_name):
    image_name = image_name.replace("/", "")
    return send_from_directory('public/image', image_name)


@app.route('/public/<path:resource>')
def serve_file(resource):
    resource = resource.replace("/", "")
    return send_from_directory('public', resource)

@app.route("/post-history")
def give_history():
    all_posts = list(question_collection.find({"timerUp": False}))
    for eachpost in all_posts:
        #deleting the extraneous _id attribute.
        del eachpost['_id']
    all_posts = json.dumps(all_posts).encode()
    return all_posts

@app.route("/submit-post", methods=["POST"])
def submit_question():
    # get form fields
    title = request.form.get("title").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    description = request.form.get("description").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    answer1 = request.form.get("answer1").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    answer2 = request.form.get("answer2").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    answer3 = request.form.get("answer3").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    answer4 = request.form.get("answer4").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    correct_answer = int(request.form.get("correct_answer").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")) - 1

    # assign id for question
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

    # get uploaded image
    image, image_name = None, None
    if "image" in request.files:
        image = request.files["image"]
        if image:
            image_name = "postnumber_" + str(postnumber) + "_image" + ".jpg"

    # Check to see if user is authenticated
    # search for auth token cookie
    auth_token_cookie_name = "auth_token"
    if auth_token_cookie_name in request.cookies:
        request_auth_token = request.cookies.get(auth_token_cookie_name)
        hashed_request_auth_token = sha256(request_auth_token.encode()).hexdigest()
        user = user_collection.find_one({"auth": hashed_request_auth_token})
        if user:
            username = user["username"]

            # added for objective 3
            askedQuestions = user["askedQuestions"]
            askedQuestions.append(postnumber)
            user_collection.update_one({"username": user["username"]},
                                       {"$set": {"askedQuestions": askedQuestions}})

            question_collection.insert_one(
                {
                    "username": username,
                    "title": title,
                    "description": description,
                    "image": image_name,
                    "answers": [answer1, answer2, answer3, answer4],
                    "correctAnswer": correct_answer,
                    "grades": [],
                    "questionID": postnumber,
                    "timerUp": False,
                    "timer": 120
                })
            # save image in directory: public/image
            if image:
                image.save("public/image/" + image_name)

            thread = threading.Thread(target=timer_thread, args=(postnumber,))
            thread.start()

            return redirect(url_for('serve_posts'))

    # User not authenticated. Post not submitted. Status code 401
    return "Unauthenticated", 401

def timer_thread(questionID):
    question = question_collection.find_one({"questionID": questionID})
    timer = question["timer"]
    while timer>0:
        timer = timer -1
        question_collection.update_one({"questionID": questionID}, {"$set": {"timer": timer}})
        timer_element = "timer_"+ str(questionID)
        data = [timer_element, timer]
        time.sleep(1)
        socketio.emit('timer_update', data)

    if timer == 0:
        grade_question(questionID)
        delete_div(questionID)




def grade_question(questionID):
    question = question_collection.find_one({"questionID": questionID})
    if question and question["grades"] == []:
        answer = answer_collection.find_one({"questionID": questionID})
        while answer:
            # get user info
            user = user_collection.find_one({"username": answer["username"]})
            answeredQuestions = user["AnsweredQuestionIDs"]
            userAnswers = user["answers"]
            userGrades = user["grades"]
            questionGrades = question["grades"]

            # update user and question info
            if answer["answer"] == question["correctAnswer"]:
                grade = 100
            else:
                grade = 0
            answeredQuestions.append(questionID)
            userAnswers.append(answer["answer"])
            userGrades.append(grade)
            questionGrades.append({user["username"]: grade})

            # set updated info in database
            user_collection.update_one({"username": user["username"]},
                                       {"$set": {"AnsweredQuestionIDs": answeredQuestions}})
            user_collection.update_one({"username": user["username"]}, {"$set": {"answers": userAnswers}})
            user_collection.update_one({"username": user["username"]}, {"$set": {"grades": userGrades}})
            question_collection.update_one({"questionID": questionID}, {"$set": {"grades": questionGrades}})

            # remove user's answer from database, and get new answer to grade
            answer_collection.delete_one(answer)
            answer = answer_collection.find_one({"questionID": questionID})
    else:
        print("Invalid Question ID")


@app.route("/register", methods=["POST"])
def register():
    data = request.form
    # assuming same form input names as hw2 html (username_reg and password_reg)
    username = data["username_reg"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") #escaped when entered to db
    shpassword = bcrypt.hashpw(data["password_reg"].encode(), bcrypt.gensalt())
    existing_user = user_collection.find_one({"username": username})
    if existing_user:
        print("Username Taken")
        return redirect(url_for('serve_index'))
    else:
        user_collection.insert_one({"username": username, "shpassword": shpassword, "auth": "", "AnsweredQuestionIDs": [], "answers": [], "grades": [], "askedQuestions": []})
        print("New User Registered")
        return redirect(url_for('serve_index'))

@app.route("/login", methods=["POST"])
def login():
    response = redirect(url_for('serve_index'))
    data = request.form
    # assuming same form input names as hw2 html (username_login and password_login)
    username = data["username_login"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") #escaped in db
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
    

@app.route("/user-display", methods= ["GET"])
def serve_user():
    auth_token_name = "auth_token"
    send_message = "User Not Logged In"
    if auth_token_name in request.cookies:
        request_auth_token = request.cookies.get(auth_token_name)
        hashed_request_auth_token = sha256(request_auth_token.encode()).hexdigest()
        user = user_collection.find_one({"auth": hashed_request_auth_token})
        if user:
            send_message = "Username: " + user["username"]

    send_message = json.dumps(send_message).encode()
    return send_message


@app.route("/userGrades-display", methods=["GET"])
def serve_userGrades():
    auth_token_name = "auth_token"
    send_message = "None"
    if auth_token_name in request.cookies:
        request_auth_token = request.cookies.get(auth_token_name)
        hashed_request_auth_token = sha256(request_auth_token.encode()).hexdigest()
        user = user_collection.find_one({"auth": hashed_request_auth_token})
        if user and user["grades"] != []:
            send_message = "" # remove "None"
            for x in range(len(user["grades"])):
                question = question_collection.find_one({"questionID": user["AnsweredQuestionIDs"][x]})
                send_message += "Question: " + str(question["title"]) + "\nGrade: " + str(user["grades"][x]) + "\n\n"

    send_message = json.dumps(send_message).encode()
    return send_message

@app.route("/questionGrades-display", methods=["GET"])
def serve_questionGrades():
    auth_token_name = "auth_token"
    send_message = "None"
    if auth_token_name in request.cookies:
        request_auth_token = request.cookies.get(auth_token_name)
        hashed_request_auth_token = sha256(request_auth_token.encode()).hexdigest()
        user = user_collection.find_one({"auth": hashed_request_auth_token})
        if user and user["askedQuestions"] != []:
            send_message = ""   # remove "None"
            for x in range(len(user["askedQuestions"])):
                question = question_collection.find_one({"questionID": user["askedQuestions"][x]})
                send_message += "Question: " + str(question["title"]) + " \nGrades:\n"
                for y in question["grades"]:
                    send_message += str(y).replace("{", "").replace("}", "") + " \n"
                send_message += "\n"

    send_message = json.dumps(send_message).encode()
    return send_message

# Handles connections
@socketio.on('connect')
def connect():
    #getting auth during websocket handshake.
    client_id = request.sid #This is a unique identifier for a client.
    auth = request.cookies.get("auth_token")
    if auth:
        hashed_request_auth_token = sha256(auth.encode()).hexdigest()
        user = user_collection.find_one({"auth": hashed_request_auth_token})
        if user:
            client_auths[client_id] = auth



# Handles disconnections
@socketio.on('disconnect')
def disconnect():
    client_id = request.sid
    if client_id in client_auths:
        del client_auths[client_id]

@socketio.on('submit_answer')
def submit_answer(data):
    print(data)
    client_id = request.sid
    if client_id in client_auths:
        this_question = question_collection.find_one({"questionID": data["questionID"]})
        auth = client_auths[client_id]
        hashed_request_auth_token = sha256(auth.encode()).hexdigest()
        user = user_collection.find_one({"auth": hashed_request_auth_token})
        username = user["username"]
        if this_question['username'] == username:
            print("Creator cannot answer their own question")
        else:
            already_answer = answer_collection.find_one({"username": username, "questionID": data["questionID"]})
            if already_answer:
                print("Already Answered")
            else:
                answer_collection.insert_one(
                    {"username": username,
                    "questionID": data["questionID"],
                    "answer": int(data["answer"])-1})   # -1 b/c the front end uses answers 1-4 but the backend uses answers 0-3
    else:
        print("client not authorized")



def delete_div(questionID):
    question_collection.update_one({'questionID': questionID}, {'$set': {"timerUp": True}})
    div_id = "div_" + str(questionID)
    data = {"div_id": div_id}
    socketio.emit('div_deleted', data)


@app.after_request
def apply_nosniff(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
    socketio.run(app, debug=True)
