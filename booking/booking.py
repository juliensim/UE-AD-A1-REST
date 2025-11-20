from flask import Flask, render_template, request, jsonify, make_response
import requests
import json
from pymongo import MongoClient
from bson.json_util import dumps
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

PORT = 3002
HOST = '0.0.0.0'

def Initialisation():
    with open('{}/databases/bookings.json'.format("."), "r") as jsf:
        bookings_json = json.load(jsf)["bookings"]

    client = MongoClient(os.getenv("MONGO_" + os.getenv("MODE")))
    db = client["bookings"]
    collection = db["bookings"]
    if list(collection.find()) == [] :
        collection.insert_many(bookings_json)
    return collection

bookings = Initialisation()

def write(bookings):
    with open('{}/databases/bookings.json'.format("."), 'w') as f:
        full = {}
        full['bookings']=bookings
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
   return "<h1 style='color:blue'>Welcome to the Booking service!</h1>"


@app.route("/json", methods=['GET'])
def get_json():
    if not(check_permission("admin")):
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    
    res = list(bookings.find({},{"_id":0}))
    return make_response(dumps(res),200)

@app.route("/bookings/<userid>", methods=['GET'])
def get_booking_byid(userid):
    if not(check_permission("user")):
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    
    booking = bookings.find_one({"userid": userid},{"_id":0})
    if booking:
        return make_response(dumps(booking),200)
    return make_response(jsonify({"error":"booking ID not found"}),500)

@app.route("/bookingdetails/<userid>", methods=['GET'])
def get_booking_details(userid):
    if not(check_permission("user")):
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    
    booking = bookings.find_one({"userid": userid})
    if booking:
        pre_res = {}
        pre_res["user"] = requests.get(os.getenv("USER_" + os.getenv("MODE")) + str(booking["userid"]),headers={'X-Token':request.headers.get("X-Token")}).json()
        pre_res["dates"] = [{} for i in range(len(booking["dates"]))]
        for date in range(0,len(booking["dates"])):
            pre_res["dates"][date]["movies"] = ["" for i in booking["dates"][date]["movies"]]
            pre_res["dates"][date]["date"] = booking["dates"][date]["date"]
            for movie in range(0,len(booking["dates"][date]["movies"])):
                pre_res["dates"][date]["movies"][movie] = requests.get(os.getenv("MOVIE_" + os.getenv("MODE")) + str(booking["dates"][date]["movies"][movie]),headers={'X-Token':request.headers.get("X-Token")}).json()
        res = make_response(jsonify(pre_res),200)
        return res
    return make_response(jsonify({"error":"booking ID not found"}),500)

@app.route("/bookings/<userid>", methods=['POST'])
def add_booking(userid):
    if not(check_permission("user")):
        return make_response(jsonify({"error": "Unauthorized"}), 401)
    
    req = request.get_json()

    booking = bookings.find_one({"userid": userid})
    if booking:
            return make_response(jsonify({"error":"booking ID already exists"}),500)
        
    for date in req["dates"]:
        schedule = requests.get(os.getenv("SCHEDULE_" + os.getenv("MODE")) + str(date["date"]),headers={'X-Token':request.headers.get("X-Token")}).json()
        for movie in date["movies"]:
            present = False
            for schedule_movie in schedule:
                if schedule_movie == movie:
                    present = True
            if not(present):
                return make_response(jsonify({"error":"one of the movies is not scheduled for the date"}),500)
    
    bookings.insert_one(req)
    return make_response(jsonify({"message":"booking added"}),200)

@app.route("/bookings/<userid>", methods=['DELETE'])
def del_booking(userid):
    if not(check_permission("user")):
        return make_response(jsonify({"error": "Unauthorized"}), 401)

    booking = bookings.find_one({"userid": userid})
    if booking:
        bookings.delete_one({"userid":userid})
        return make_response(jsonify({"message":"booking deleted"}),200)

    return make_response(jsonify({"error":"booking ID not found"}),500)

if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
