from flask import Flask, render_template, request, jsonify, make_response
import json

app = Flask(__name__)

PORT = 3003
HOST = '0.0.0.0'

with open('{}/databases/times.json'.format("."), "r") as jsf:
   schedule = json.load(jsf)["schedule"]

def write(schedule):
    with open('{}/databases/times.json'.format("."), 'w') as f:
        full = {}
        full['schedule']=schedule
        json.dump(full, f)

@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the Showtime service!</h1>"

@app.route("/json", methods=['GET'])
def get_json():
    return make_response(jsonify(schedule),200)

@app.route("/schedule/<date>", methods=['GET'])
def get_movies_bydate(date):
    for s in schedule:
        if str(s["date"]) == str(date):
            res = make_response(jsonify(s["movies"]),200)
            return res
    return make_response(jsonify({"error":"No movie found for the date"}),500)

@app.route("/scheduledate/<movieid>", methods=['GET'])
def get_dates_formovie(movieid):
    dates = []
    for s in schedule:
      for m in s["movies"]:
         if str(m) == str(movieid):
            dates.append(s["date"])
    if dates:
        res = make_response(jsonify(dates),200)
        return res
    return make_response(jsonify({"error":"No movie found"}),500)

@app.route("/schedule/<date>/<movieid>", methods=['POST'])
def add_movie(date, movieid):
   # vérifier si le film existe dans movies

    for s in schedule:
        if str(s["date"]) == str(date):
            s["movies"].append(movieid)
            write(schedule)
            res = make_response(jsonify(s),200)
            return res
    s = {
        "date": date,
        "movies":[movieid]
    }
    schedule.append(s)
    write(schedule)
    res = make_response(jsonify(s),200)
    return res

@app.route("/schedule/<date>/<movieid>", methods=['DELETE'])
def del_movie(date, movieid):
    for s in schedule:
        if str(s["date"]) == str(date):
            for m in s["movies"]:
                if str(m) == str(movieid):
                    s["movies"].remove(m)
                    if (len(s["movies"]) == 0):
                        schedule.remove(s)
                    write(schedule)
                    return make_response(jsonify(s),200)

    res = make_response(jsonify({"error":"date or movie ID not found"}),500)
    return res
   

if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
