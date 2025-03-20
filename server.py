from flask import Flask, jsonify, request, render_template
import threading
import logging
from time import sleep
from ScooterManager import ScooterManagerComponent

# global variables
app = Flask(__name__)
scooterManager = ScooterManagerComponent()
locations = {69: ((45.6, 60.8), 420)}
getLocationsInterval = 5
yellowZoneFee = 10

zones = [
    ["yellow", (10.5,60), (20,64)],
    ["yellow", (80,70),  (86,90)],
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
            scooterManager.on_frontend_command(command, scooterID)
            while True:
                result = scooterManager.get_status(scooterID, command)
                if result == True:
                    return 1
                elif result == False:
                    return 0
        case "lock":
            scooterManager.on_frontend_command(command, scooterID)
            while True:
                result = scooterManager.get_status(scooterID, command)
                if result == True:
                    return 1
                elif result == False:
                    return 0
        case "getPrice":
            return calculateCost(scooterID)

@app.route('/getLocations')
def returnLocations():
    return jsonify(locations)

@app.route('/getZones')
def returnZones():
    return jsonify(zones)

@app.route('/getCost')
def returnZoneAndCost():
    pass

def calculateCost(scooterID):
    cost = 0
    currentCoords = locations[scooterID]

    for zone in zones:
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
        global locations
        locations = scooterManager.get_locations()
        print(locations)
        sleep(getLocationsInterval)

if __name__ == '__main__':

    locationsThread = threading.Thread(target=updateLocations)
    locationsThread.start()

    app.run(host='0.0.0.0', port=3000, debug=True)