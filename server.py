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
    
    print("guiclick")
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
    # preven
    if userID in userCurrentScooter:
        if command == "unlock":
            return 0

    scooterManager.on_frontend_command(command, scooterID, transaction_id, userID)
    
    while(scooterManager.get_status(transaction_id) == None):
        sleep(0.1)

    if command == "unlock":
        userCurrentScooter[userID] = scooterID
    elif command == "lock":
        if userID in userCurrentScooter:
            userCurrentScooter.pop(userID)
    return 1

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
        print(locations)
        sleep(getLocationsInterval)
        
if __name__ == '__main__':

    locationsThread = threading.Thread(target=updateLocations)
    locationsThread.start()

    # scooter1 = Scooter()
    # scooter2 = Scooter()
    # scooter3 = Scooter()
    # scooter4 = Scooter()
    
    app.run(host='0.0.0.0', port=3000, debug=True, use_reloader=False)
    
    
# {
#     '14e1c411-9b87-41cd-98b4-e17748987a18': (
#         {'coordinates': [35, 29], 'locked': True}, 1743102141
#     ), 
#     '77afb6e5-9a43-4b58-91c7-47ed139a430e': (
#         {'coordinates': [50, 83], 'locked': True}, 1743102141
#     ), 
#     '603bc290-8cb1-41d5-ba90-f9cb5bd882dc': (
#         {'coordinates': [8, 32], 'locked': True}, 1743102141
#     ), 
#     'eb4937a3-5e12-40c7-9796-7e3ef4072e64': (
#         {'coordinates': [84, 14], 'locked': True}, 1743102141
#     )
# }

