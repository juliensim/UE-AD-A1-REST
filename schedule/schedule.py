from flask import Flask, render_template, request, jsonify, make_response
import requests
import json
from pymongo import MongoClient
from bson.json_util import dumps
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

PORT = 3003
HOST = '0.0.0.0'

def Initialisation():
    with open('{}/databases/times.json'.format("."), "r") as jsf:
        schedule_json = json.load(jsf)["schedule"]

    client = MongoClient(os.getenv("MONGO_" + os.getenv("MODE")))
    db = client["schedule"]
    collection = db["schedule"]
    if list(collection.find()) == [] :
        collection.insert_many(schedule_json)
    return collection

schedule = Initialisation()

def write(schedule):
    with open('{}/databases/times.json'.format("."), 'w') as f:
        full = {}
        full['schedule']=schedule
        json.dump(full, f)

@app.before_request
def authentification():
    if requests.get(os.getenv("USER_" + os.getenv("MODE")) + "auth",headers={'X-Token':request.headers.get("X-Token")}).status_code != 200:
        return make_response(jsonify({"error": "Unknown user"}), 401)
    return

def check_permission(permission_required):
    return requests.get(os.getenv("USER_" + os.getenv("MODE")) + "check/" + permission_required,headers={'X-Token':request.headers.get("X-Token")}).status_code == 200

@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the Showtime service!</h1>"

@app.route("/json", methods=['GET'])
def get_json():
    if not(check_permission("admin")):
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    
    res = list(schedule.find({},{"_id":0}))
    return make_response(dumps(res),200)

@app.route("/schedules/<date>", methods=['GET'])
def get_movies_bydate(date):
    if not(check_permission("user")):
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    
    date_movies = schedule.find_one({"date": date},{"_id":0})
    if date_movies:
        return make_response(dumps(date_movies["movies"]),200)
    return make_response(jsonify({"error":"No movie found for the date"}),500)

@app.route("/schedules/date/<movieid>", methods=['GET'])
def get_dates_formovie(movieid):
    if not(check_permission("user")):
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    
    dates_movie = schedule.find({"movies": movieid},{"_id":0})
    if dates_movie:
        dates = [date["date"] for date in dates_movie]
        return make_response(dumps(dates),200)
    return make_response(jsonify({"error":"No movie found"}),500)

@app.route("/schedules/<date>/<movieid>", methods=['POST'])
def add_movie(date, movieid):
    if not(check_permission("admin")):
        return make_response(jsonify({"error": "Unauthorized"}), 401)

    date_movies = schedule.find_one({"date": date})
    if date_movies:
        schedule.update_one({"date":date},{"$push":{"movies":movieid}})
        return make_response(jsonify({"message":"movie added to the date"}),200)
    
    schedule.insert_one({"date":date,"movies":[movieid]})
    return make_response(jsonify({"message":"date and movie added"}),200)

@app.route("/schedules/<date>/<movieid>", methods=['DELETE'])
def del_movie(date, movieid):
    if not(check_permission("admin")):
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    
    date_movies = schedule.find_one({"date": date, "movies":movieid})
    if date_movies:
        date_movies = schedule.find_one({"date": date})
        if len(date_movies["movies"])==1:
            schedule.delete_one({"date": date, "movies":movieid})
            return make_response(jsonify({"message":"date and movie deleted"}),200)
        else:
            schedule.update_one({"date":date},{"$pull":{"movies":movieid}})
            return make_response(jsonify({"message":"movie deleted for the date"}),200)
    
    return make_response(jsonify({"error":"date or movie ID not found"}),500)   

if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
