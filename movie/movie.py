from flask import Flask, request, jsonify, make_response
import requests
import json
from pymongo import MongoClient
from bson.json_util import dumps
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

PORT = 3001
HOST = '0.0.0.0'

def Initialisation():
    with open('{}/databases/movies.json'.format("."), 'r') as jsf:
        movies_json = json.load(jsf)["movies"]

    client = MongoClient(os.getenv("MONGO_" + os.getenv("MODE")))
    db = client["movies"]
    collection = db["movies"]
    if list(collection.find()) == [] :
        collection.insert_many(movies_json)
    return collection

movies = Initialisation()

def write(movies):
    with open('{}/databases/movies.json'.format("."), 'w') as f:
        full = {}
        full['movies']=movies
        json.dump(full, f)

@app.before_request
def authentification():
    if requests.get(os.getenv("USER_" + os.getenv("MODE")) + "auth",headers={'X-Token':request.headers.get("X-Token")}).status_code != 200:
        return make_response(jsonify({"error": "Unknown user"}), 401)
    return

def check_permission(permission_required):
    return requests.get(os.getenv("USER_" + os.getenv("MODE")) + "check/" + permission_required,headers={'X-Token':request.headers.get("X-Token")}).status_code == 200

# root message
@app.route("/", methods=['GET'])
def home():
    return make_response("<h1 style='color:blue'>Welcome to the Movie service!</h1>",200)


@app.route("/json", methods=['GET'])
def get_json():
    if not(check_permission("admin")):
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    
    res = list(movies.find({},{"_id":0}))
    return make_response(dumps(res),200)

@app.route("/movies/<movieid>", methods=['GET'])
def get_movie_byid(movieid):
    if not(check_permission("user")):
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    
    movie = movies.find_one({"id": movieid},{"_id":0})
    if movie:
        return make_response(dumps(movie),200)
    return make_response(jsonify({"error":"Movie ID not found"}),500)

@app.route("/moviesbytitle", methods=['GET'])
def get_movie_bytitle():
    if not(check_permission("user")):
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    
    if request.args:
        movie = movies.find_one({"title": request.args["title"]},{"_id":0})
        if movie:
            return make_response(dumps(movie),200)

    return make_response(jsonify({"error":"movie title not found"}),500)

@app.route("/movies/<movieid>", methods=['POST'])
def add_movie(movieid):
    if not(check_permission("admin")):
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    
    movie = movies.find_one({"id": movieid})
    if movie:
        return make_response(jsonify({"error":"movie ID already exists"}),500)

    movies.insert_one(request.get_json())
    return make_response(jsonify({"message":"movie added"}),200)

@app.route("/movies/<movieid>/<rate>", methods=['PUT'])
def update_movie_rating(movieid, rate):
    if not(check_permission("admin")):
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    
    movies.update_one({"id":movieid},{"$set":{"rating":rate}})
    movie = movies.find_one({"id":movieid},{"_id":0})
    if movie:
        return make_response(dumps(movie),200)

    return make_response(jsonify({"error":"movie ID not found"}),500)

@app.route("/movies/<movieid>", methods=['DELETE'])
def del_movie(movieid):
    if not(check_permission("admin")):
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    
    movie = movies.find_one({"id": movieid})
    if movie:
        movies.delete_one({"id":movieid})
        return make_response(jsonify({"message":"movie deleted"}),200)
    
    return make_response(jsonify({"error":"movie ID not found"}),500)

if __name__ == "__main__":
    #p = sys.argv[1]
    print("Server running in port %s"%(PORT))
    app.run(host=HOST, port=PORT)
