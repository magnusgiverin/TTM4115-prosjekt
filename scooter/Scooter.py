import paho.mqtt.client as mqtt
import random
from stmpy import Machine, Driver
import logging
import time
import ssl




BROKER = ""
PORT = 8883 # TLS port

TOPIC_COORDINATES = "scooter/coordinates"
TOPIC_LOCK = "scooter/lock"
TOPIC_UNLOCK = "scooter/unlock"

FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60


class Scooter:
    
    def __init__(self):
        self.is_locked = True
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.connect(BROKER, 1883, 60)
        
        # TLS enabled
        self.client.tls_set(cert_reqs=ssl.CERT_NONE)
        
        self.client.connect(BROKER, PORT, 60)
        """"
        self.machine = Machine(name="scooter_machine", transitions=[
            {"source": "initial", "target": "locked"},
            {"trigger": "unlock", "source": "locked", "target": "unlocked"},
            {"trigger": "lock", "source": "unlocked", "target": "locked"},
        ], obj=self)
        
        self.driver = Driver()
        self.driver.add_machine(self.machine)
        self.driver.start() 

        """

        self.machine= Machine(

            name="Scooter_machine",
            
            states=[

                {"name": "locked", "entry": "self.lock_scooter()", "exit": "self.send_status()"},
                {"name": "unlocked", "entry": "self.unlock_scooter()", "exit": "self.send_status()"},

            ],
            transitions=[
                {"source": "initial", "target": "locked"},  
                {"trigger": "unlock", "source": "locked", "target": "unlocked"},
                {"trigger": "lock", "source": "unlocked", "target": "locked"},
    ],

    obj=self,

            
    )

    def on_connect(self, client, userdata, flags, rc):
        logging.info("Connected", rc)
        client.subscribe(TOPIC_LOCK)
        client.subscribe(TOPIC_UNLOCK)
        

    def on_disconnect(self, client, userdata, rc):
        logging.info("Disconnected with result code: %s", rc)
        reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
        while reconnect_count < MAX_RECONNECT_COUNT:
            logging.info("Reconnecting in %d seconds...", reconnect_delay)
            time.sleep(reconnect_delay)

            try:
                client.reconnect()
                logging.info("Reconnected successfully!")
                return
            except Exception as err:
                logging.error("%s. Reconnect failed. Retrying...", err)

            reconnect_delay *= RECONNECT_RATE
            reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
            reconnect_count += 1
        logging.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)

    def on_message(self, client, userdata, msg):
        message = {
            "command": "location_ping",
            "type": "na",
            "coords": coordinates
        }
        if msg.topic == TOPIC_LOCK:
            print("Scooter locked.")
            self.driver.send("lock", "scooter_machine")
        elif msg.topic == TOPIC_UNLOCK:
            print("Scooter unlocked.")
            self.driver.send("unlock", "scooter_machine")

    def send_coordinates(self):
        selected_area = random.uniform()
        if selected_area > 0.2:
            coordinates = 0
        elif 0.2 <= selected_area <= 0.5:
            coordinates = 1
        else:
            coordinates = 2
        
        #coordinates = random.choice([0, 1, 2])# Random zone selection (red, yellow, green), change later
        print(f"Sending coordinates: {coordinates}")
        self.client.publish(TOPIC_COORDINATES, coordinates)    
    
    def run(self):
        try:
            while True:
                self.send_coordinates()
                time.sleep(10)
        except KeyboardInterrupt:
            print("Stopped")
            self.client.disconnect()
            self.driver.stop()
            
"""
if __name__ == '__main__':
    scooter = Scooter()
    scooter.run()
"""

{
    "command": "location_ping",
    "type": "na",
    "coords": (int, int),
}