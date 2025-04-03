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
locations = {}
getLocationsInterval = 0.02
# getLocationsInterval = 1

mutex = threading.Lock()

yellowZoneLockFee = 10

standardUnlockDiscount = 5
yellowZoneUnlockDiscount = 15
redZoneUnlockDiscount = 30

standardDrivingFee = 1
yellowZoneDrivingFee = 2
redZoneDrivingFee = 3
userCurrentScooter = {}
    # userID: [ScooterID, locking confirmation, current discounts]
currentRoutes = {}

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


@app.route('/getLocations')
def returnLocations():
    return jsonify(locations)


@app.route('/getZones')
def returnZones():
    return jsonify(zones)


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


def toggleScooterStatus(command, scooterID, userID, transaction_id):
    # prevent unlocking multiple scooters
    if userID in userCurrentScooter:
        if command == "unlock":
            return jsonify(["unlock_fail", 0])

    if command == "lock":
        currentCoords = locations[scooterID][0]["coordinates"]
        zone = calculateZone(currentCoords)
        fee = zoneToLockFee(zone)
        if zone != "none" and userCurrentScooter[userID][1] == False:
            if zone == "yellow":
                userCurrentScooter[userID][1] = True
            elif zone == "red":
                return jsonify(["lock_red", 0])
            return jsonify(["lock_fee", fee])
        elif userID in userCurrentScooter:
            scooterManager.on_frontend_command(command, scooterID, transaction_id, userID)
            mutex.acquire()
            fare = calculateFare(scooterID, userID)
            mutex.release()
            userCurrentScooter.pop(userID)
            currentRoutes[scooterID] = []
            return jsonify(["lock_fare", fare])

    # while(scooterManager.get_status(transaction_id) == None):
    #     sleep(0.1)

    if command == "unlock":
        currentCoords = locations[scooterID][0]["coordinates"]
        zone = calculateZone(currentCoords)
        discount = zoneToUnlockDiscount(zone)
        if userID in userCurrentScooter:
            if zone != "none" and userCurrentScooter[userID][1] == False:
                if zone == "yellow":
                    userCurrentScooter[userID][1] = True
                return jsonify(["unlock_discount", discount])
        elif userID not in userCurrentScooter:
            scooterManager.on_frontend_command(command, scooterID, transaction_id, userID)
            userCurrentScooter[userID] = [scooterID, False, discount]
            return jsonify(["unlock_success", 0])
    return jsonify(["error", 0])


def calculateFare(scooterID, userID):
    totalCost = userCurrentScooter[userID][2] # unlock discount

    for sample in currentRoutes[scooterID]:
        zone = calculateZone(sample[1])
        if zone == "yellow":
            totalCost += yellowZoneDrivingFee
        elif zone == "red":
            totalCost += redZoneDrivingFee
        else:
            totalCost += standardDrivingFee

    return totalCost


def zoneToLockFee(zone):
    if zone == "red":
        return ""
    elif zone == "yellow":
        return yellowZoneLockFee
    else:
        return 0


def zoneToUnlockDiscount(zone):
    if zone == "red":
        return -redZoneUnlockDiscount
    elif zone == "yellow":
        return -yellowZoneUnlockDiscount
    else:
        return 0
    

def calculateZone(currentCoords):
    for zone in zones:
        if zone[1][0] < currentCoords[0] and currentCoords[0] < zone[2][0]:
            if zone[1][1] < currentCoords[1] and currentCoords[1] < zone[2][1]:
                return zone[0]
    return "none"


def updateLocations():
    while True:
        global locations
        locations = scooterManager.get_data()
        print(locations)
        print(currentRoutes)
        
        mutex.acquire()

        for key in locations:
            if locations[key][0]["locked"] == False:
                coordinates = locations[key][0]["coordinates"]
                timestamp = locations[key][1]
                if key in currentRoutes:
                    if (timestamp, coordinates) not in currentRoutes[key]: # don't add duplicates
                        currentRoutes[key].append((timestamp, coordinates))
                else:
                    currentRoutes[key] = [(timestamp, coordinates)]

        mutex.release()

        sleep(getLocationsInterval)
        

if __name__ == '__main__':

    locationsThread = threading.Thread(target=updateLocations)
    locationsThread.start()

    app.run(host='0.0.0.0', port=3000, debug=True, use_reloader=False)