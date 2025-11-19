from flask import Flask, render_template, request, jsonify, make_response, g
import json
from pymongo import MongoClient
from bson.json_util import dumps

app = Flask(__name__)

PORT = 3004
HOST = '0.0.0.0'

with open('{}/databases/users.json'.format("."), "r") as jsf:
   users = json.load(jsf)["users"]

def init_Mongo():
    client = MongoClient("mongodb://username:password@127.0.0.1:3000/")
    db = client["users"]
    collection = db["users"]
    collection.insert_many(users)

init_Mongo()

@app.before_request
def check_user():
    token = request.headers.get("X-Token")
    g.permission_level = "None"
    for user in users:
        if user["access_token"] == token:
            g.permission_level = user["role"]
            return 
    return make_response(jsonify({"error": "Unauthorized"}), 401)

def check_permission_level(permission_required):
    if permission_required == "admin" and g.permission_level != "admin":
        return False
    elif permission_required == "user" and g.permission_level != "user" and g.permission_level != "admin":
        return False
    return True

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
    if not(check_permission_level("admin")) :
        return make_response(jsonify({"error": "Unauthorized"}), 401)

    return make_response(jsonify(users),200)

@app.route("/users/<userid>", methods=['GET'])
def get_user_byid(userid):
    if not(check_permission_level("user")) :
        return make_response(jsonify({"error": "Unauthorized"}), 401)

    for user in users:
        if str(user["id"]) == str(userid):
            return make_response(jsonify({key: user[key] for key in ["id","name","last_active","role"]}),200)
    return make_response(jsonify({"error":"user ID not found"}),500)

@app.route("/usersbyname", methods=['GET'])
def get_user_byname():
    if not(check_permission_level("user")) :
        return make_response(jsonify({"error": "Unauthorized"}), 401)

    if request.args:
        for user in users:
            if str(user["name"]) == str(request.args["name"]):
                return make_response(jsonify({key: user[key] for key in ["id","name","last_active","role"]}),200)

    return make_response(jsonify({"error":"user name not found"}),500)

@app.route("/users/<userid>", methods=['POST'])
def add_user(userid):
    if not(check_permission_level("admin")) :
        return make_response(jsonify({"error": "Unauthorized"}), 401)

    for user in users:
        if str(user["id"]) == str(userid):
            return make_response(jsonify({"error":"user ID already exists"}),500)

    users.append(request.get_json())
    write(users)
    return make_response(jsonify({"message":"user added"}),200)

@app.route("/users/<userid>", methods=['PUT'])
def update_user(userid):
    if not(check_permission_level("admin")) :
        return make_response(jsonify({"error": "Unauthorized"}), 401)

    for user in users:
        if str(user["id"]) == str(userid):
            req = request.get_json()
            for key in req.keys():
                user[key] = req[key]
            write(users)
            return make_response(jsonify(user),200)

    return make_response(jsonify({"error":"user ID not found"}),500)

@app.route("/users/<userid>", methods=['DELETE'])
def del_user(userid):
    if not(check_permission_level("admin")) :
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    
    for user in users:
        if str(user["id"]) == str(userid):
            users.remove(user)
            write(users)
            return make_response(jsonify({"message":"user deleted"}),200)

    return make_response(jsonify({"error":"user ID not found"}),500)

if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
