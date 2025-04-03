import uuid
from flask import Flask, jsonify, request, render_template
import threading
import logging
from time import sleep
from Scooter import Scooter
from ScooterManager import ScooterManagerComponent

# global variables
app = Flask(__name__)
scooterManager = ScooterManagerComponent()
locations = {69: ((45.6, 60.8), 420)}
getLocationsInterval = 5
yellowZoneFee = 10
userCurrentScooter = {}
    # userID: [ScooterID, locking confirmation]

zones = [
    ["yellow", (10.5,60), (20,64)],
    ["yellow", (80,70),   (86,90)],
    ["red",    (50,50),   (67,69)]
]

@app.route('/')
def login():
    return render_template("login.html")

@app.route('/<int:userID>')
def home(userID=None):
    return render_template("index.html", userID=userID)

@app.route('/guiClick', methods=['POST'])
def guiClick():
    data = request.get_json()
    command = data['command']
    scooterID = data['scooterID']
    userID = data['userID']
    
    transaction_id = str(uuid.uuid4())
    
    match command:
        case "getLocations":
            return returnLocations()
        case "unlock":
            return toggleScooterStatus(command, scooterID, userID, transaction_id)
        case "lock":
            return toggleScooterStatus(command, scooterID, userID, transaction_id)
        case "getPrice":
            return calculateCost(scooterID)

def toggleScooterStatus(command, scooterID, userID, transaction_id):
    # prevent unlocking multiple scooters
    if userID in userCurrentScooter:
        if command == "unlock":
            return False

    scooterManager.on_frontend_command(command, scooterID, transaction_id, userID)
    
    while(scooterManager.get_status(transaction_id) == None):
        sleep(0.1)

    if command == "unlock":
        userCurrentScooter[userID] = [scooterID, False]
    elif command == "lock":
        cost = calculateCost(scooterID)
        if cost != 0 and userCurrentScooter[userID][1] == False:
            return cost
        if userID in userCurrentScooter:
            userCurrentScooter.pop(userID)
    return True

@app.route('/getLocations')
def returnLocations():
    return jsonify(locations)

@app.route('/getZones')
def returnZones():
    return jsonify(zones)

# @app.route('/getCost')
# def returnZoneAndCost():
#     pass

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
        locations = scooterManager.get_data()
        sleep(getLocationsInterval)
        
if __name__ == '__main__':

    locationsThread = threading.Thread(target=updateLocations)
    locationsThread.start()

    app.run(host='0.0.0.0', port=3000, debug=True, use_reloader=False)