from flask import Flask, render_template, request, jsonify, make_response, g
import json
from pymongo import MongoClient
from bson.json_util import dumps
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

PORT = 3004
HOST = '0.0.0.0'

def Initialisation():
    with open('{}/databases/users.json'.format("."), "r") as jsf:
        users_json = json.load(jsf)["users"]

    client = MongoClient(os.getenv("MONGO_" + os.getenv("MODE")))
    db = client["users"]
    collection = db["users"]
    if list(collection.find()) == [] :
        collection.insert_many(users_json)
    return collection

users = Initialisation()

@app.before_request
def authentification():
    if check_user().status_code != 200:
        return make_response(jsonify({"error": "Unknown user"}), 401)
    return

@app.route("/users/auth", methods=['GET'])
def check_user():
    token = request.headers.get("X-Token")
    g.permission_level = "None"
    user = users.find_one({"access_token": token})
    if user:
        g.permission_level = user["role"]
        return make_response(jsonify({"message":"correct user"}),200)
    return make_response(jsonify({"error": "Unknown user"}), 401)

@app.route("/users/check/<permission_required>", methods=['GET'])
def check_permission_level(permission_required):
    if permission_required == "admin" and g.permission_level != "admin":
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    elif permission_required == "user" and g.permission_level != "user" and g.permission_level != "admin":
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    return make_response(jsonify({"message":"Authorized"}),200)

def write(users):
    with open('{}/databases/users.json'.format("."), 'w') as f:
        full = {}
        full['users']=users
        json.dump(full, f)

@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the User service!</h1>"

@app.route("/json", methods=['GET'])
def get_json():
    if check_permission_level("admin").status_code != 200 :
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    res = list(users.find({},{"_id":0}))
    return make_response(dumps(res),200)

@app.route("/users/<userid>", methods=['GET'])
def get_user_byid(userid):
    if check_permission_level("user").status_code != 200 :
        return make_response(jsonify({"error": "Unauthorized"}), 401)

    user = users.find_one({"id": userid},{"_id":0,"access_token":0})
    if user:
        return make_response(dumps(user),200)
    return make_response(jsonify({"error":"user ID not found"}),500)

@app.route("/users/byname", methods=['GET'])
def get_user_byname():
    if check_permission_level("user").status_code != 200 :
        return make_response(jsonify({"error": "Unauthorized"}), 401)

    if request.args:
        user = users.find_one({"name": request.args["name"]},{"_id":0,"access_token":0})
        if user:
            return make_response(dumps(user),200)

    return make_response(jsonify({"error":"user name not found"}),500)

@app.route("/users/<userid>", methods=['POST'])
def add_user(userid):
    if check_permission_level("admin").status_code != 200 :
        return make_response(jsonify({"error": "Unauthorized"}), 401)

    user = users.find_one({"id": userid})
    if user:
        return make_response(jsonify({"error":"user ID already exists"}),500)

    users.insert_one(request.get_json())
    return make_response(jsonify({"message":"user added"}),200)

@app.route("/users/<userid>", methods=['PUT'])
def update_user(userid):
    if check_permission_level("admin").status_code != 200 :
        return make_response(jsonify({"error": "Unauthorized"}), 401)

    users.update_one({"id":userid},{"$set":request.get_json()})
    user = users.find_one({"id":userid},{"_id":0})
    if user:
        return make_response(dumps(user),200)

    return make_response(jsonify({"error":"user ID not found"}),500)

@app.route("/users/<userid>", methods=['DELETE'])
def del_user(userid):
    if check_permission_level("admin").status_code != 200 :
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    
    user = users.find_one({"id": userid})
    if user:
        users.delete_one({"id":userid})
        return make_response(jsonify({"message":"user deleted"}),200)

    return make_response(jsonify({"error":"user ID not found"}),500)

if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
