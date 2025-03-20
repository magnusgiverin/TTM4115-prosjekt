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
yellowZoneFee = 10

zoneMap = [
    ["yellow", (10.5,4), (20,14.2)],
    ["yellow", (1,4),    (2,4.5)],
    ["red",    (50,50),  (67,69)]
]

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/guiClick', methods=['POST'])
def guiClick():
    data = request.get_json()
    command = data['command']
    scooterID = data['scooterID']
    match command:
        case "getLocations":
            return returnLocations()
        case "unlock":
            return scooterManager.on_frontend_command(command, scooterID)
        case "lock":
            return scooterManager.on_frontend_command(command, scooterID)
        case "getPrice":
            return calculateCost(scooterID)

@app.route('/getLocations')
def returnLocations():
    return locations

@app.route('/getCost')
def returnZoneAndCost():
    pass

def calculateCost(scooterID):
    cost = 0
    currentCoords = locations[scooterID]

    for zone in zoneMap:
        if zone[1][0] < currentCoords[0] and currentCoords[0] < zone[1][1]:
            if zone[2][0] < currentCoords[1] and currentCoords[1] < zone[2][1]:
                if zone[0] == "yellow":
                    cost = yellowZoneFee
                elif zone[0] == "red":
                    cost = -1
                break

    return cost

def updateLocations():
    while True:
        locations = scooterManager.get_locations()
        sleep(getLocationsInterval)

if __name__ == '__main__':

    locationsThread = threading.Thread(target=updateLocations)
    locationsThread.start()

    print(scooterManager.get_locations())

    app.run(host='0.0.0.0', port=3000, debug=True)