from flask import Flask, render_template, request, jsonify, make_response
import requests
import json

app = Flask(__name__)

PORT = 3002
HOST = '0.0.0.0'

with open('{}/databases/bookings.json'.format("."), "r") as jsf:
   bookings = json.load(jsf)["bookings"]

def write(bookings):
    with open('{}/databases/bookings.json'.format("."), 'w') as f:
        full = {}
        full['bookings']=bookings
        json.dump(full, f)

@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the Booking service!</h1>"


@app.route("/json", methods=['GET'])
def get_json():
    return make_response(jsonify(bookings),200)

@app.route("/bookings/<userid>", methods=['GET'])
def get_booking_byid(userid):
    for booking in bookings:
        if str(booking["userid"]) == str(userid):
            res = make_response(jsonify(booking),200)
            return res
    return make_response(jsonify({"error":"booking ID not found"}),500)

@app.route("/bookingdetails/<userid>", methods=['GET'])
def get_booking_details(userid):
    for booking in bookings:
        if str(booking["userid"]) == str(userid):
            pre_res = {}
            pre_res["user"] = requests.get('http://localhost:3203/users/' + str(booking["userid"])).json()
            pre_res["dates"] = [{} for i in range(len(booking["dates"]))]
            print("ici : " + str(pre_res))
            for date in range(0,len(booking["dates"])):
                pre_res["dates"][date]["movies"] = ["" for i in booking["dates"][date]["movies"]]
                pre_res["dates"][date]["date"] = booking["dates"][date]["date"]
                for movie in range(0,len(booking["dates"][date]["movies"])):
                    print(pre_res)
                    pre_res["dates"][date]["movies"][movie] = requests.get('http://localhost:3200/movies/' + str(booking["dates"][date]["movies"][movie])).json()
            res = make_response(jsonify(pre_res),200)
            return res
    return make_response(jsonify({"error":"booking ID not found"}),500)

@app.route("/bookings/<userid>", methods=['POST'])
def add_booking(userid):
    req = request.get_json()

    for booking in bookings:
        if str(booking["userid"]) == str(userid):
            return make_response(jsonify({"error":"booking ID already exists"}),500)
        
    for date in req["dates"]:
        schedule = requests.get('http://localhost:3202/schedule/' + str(date["date"])).json()
        for movie in date["movies"]:
            print(movie)
            print(date["date"])
            present = False
            for schedule_movie in schedule:
                print("current_movie : " + schedule_movie)
                if schedule_movie == movie:
                    present = True
            if not(present):
                return make_response(jsonify({"error":"one of the movies is not scheduled for the date"}),500)
                

    bookings.append(req)
    write(bookings)
    res = make_response(jsonify({"message":"booking added"}),200)
    return res

@app.route("/bookings/<userid>", methods=['DELETE'])
def del_booking(userid):
    for booking in bookings:
        if str(booking["userid"]) == str(userid):
            bookings.remove(booking)
            write(bookings)
            return make_response(jsonify(booking),200)

    res = make_response(jsonify({"error":"booking ID not found"}),500)
    return res

if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
