from flask import Flask, jsonify, request
import threading
import logging
from time import sleep
from ScooterManager import ScooterManagerComponent

# global variables
app = Flask(__name__)
scooterManager = ScooterManagerComponent()
locations = []
getLocationsInterval = 5

zoneMap = {
    "yellow": [
        ((10.5,4), (20,14.2)),
        ((1,4), (2,4.5))
        ],
    "red": [
        ((50,50),  (67,69))
        ],
}

@app.route('/')
def home():
    return render_template("frontend.html")

@app.route('/guiClick', methods=['POST'])
def guiClick():
    data = request.get_json()
    command = data['command']
    scooterID = data['scooterID']
    match command:
        case "getLocations":
            pass
        case "unlock":
            pass
        case "lock":
            pass
        # TODO handle button presses

@app.route('/getLocations')
def returnLocations():
    return locations

@app.route('/getCost')
def returnZoneAndCost():
    zone
    return [zone, cost]

def calculateCost(location):
    return 

def scooterHandler():
    while True:
        locations = scooterManager.get_locations()
        sleep(getLocationsInterval)

if __name__ == '__main__':

    mqttThread = threading.Thread(target=scooterHandler)
    mqttThread.start()

    print(scooterManager.get_locations())

    app.run(host='0.0.0.0', port=3000, debug=True)