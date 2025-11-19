from flask import Flask, render_template, request, jsonify, make_response, g
import json
from werkzeug.exceptions import NotFound

app = Flask(__name__)

PORT = 3004
HOST = '0.0.0.0'

with open('{}/databases/users.json'.format("."), "r") as jsf:
   users = json.load(jsf)["users"]

@app.before_request
def check_user():
    userid = request.headers.get("X-User")
    
    for user in users:
        if user["id"] == userid:
            g.current_user = user
            return
    return jsonify({"error": "Unauthorized"}), 401

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
    return make_response(jsonify(users),200)

@app.route("/users/<userid>", methods=['GET'])
def get_user_byid(userid):
    for user in users:
        if str(user["id"]) == str(userid):
            res = make_response(jsonify(user),200)
            return res
    return make_response(jsonify({"error":"user ID not found"}),500)

@app.route("/usersbyname", methods=['GET'])
def get_user_byname():
    json = ""
    if request.args:
        req = request.args
        for user in users:
            if str(user["name"]) == str(req["name"]):
                json = user

    if not json:
        res = make_response(jsonify({"error":"user name not found"}),500)
    else:
        res = make_response(jsonify(json),200)
    return res

@app.route("/users/<userid>", methods=['POST'])
def add_user(userid):
    if g.current_user["role"] != "admin":
        return jsonify({"error": "Unauthorized"}), 401

    req = request.get_json()

    for user in users:
        if str(user["id"]) == str(userid):
            return make_response(jsonify({"error":"user ID already exists"}),500)

    users.append(req)
    write(users)
    res = make_response(jsonify({"message":"user added"}),200)
    return res

@app.route("/users/<userid>", methods=['PUT'])
def update_user(userid):
    if g.current_user["role"] != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    
    req = request.get_json()

    for user in users:
        if str(user["id"]) == str(userid):
            user["name"] = req["name"]
            user["last_active"] = req["last_active"]
            res = make_response(jsonify(user),200)
            write(users)
            return res

    res = make_response(jsonify({"error":"user ID not found"}),500)
    return res

@app.route("/users/<userid>", methods=['DELETE'])
def del_user(userid):
    if g.current_user["role"] != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    
    for user in users:
        if str(user["id"]) == str(userid):
            users.remove(user)
            write(users)
            return make_response(jsonify(user),200)

    res = make_response(jsonify({"error":"user ID not found"}),500)
    return res

if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
