import paho.mqtt.client as mqtt
import random
from stmpy import Machine, Driver
import logging
import time
import ssl
import json
from datetime import datetime
from sense_hat import SenseHat
import signal
import RPi.GPIO as GPIO  # For button handling
import sys


BROKER = ""
PORT = 8883 # TLS port

TOPIC_COORDINATES = "scooter/coordinates"
TOPIC_LOCK = "scooter/lock"
TOPIC_UNLOCK = "scooter/unlock"

sense= SenseHat()


FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60

BUTTON_PIN = 17

# Configure logging for Raspberry Pi
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


class Scooter:
    
    def __init__(self, id: int):
        self.id = id
        self.is_locked = True
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.connect(BROKER, 1883, 60)
        
        self.sense = SenseHat()
        
        self.zone = 0
        
         # Button setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=self.change_zone, bouncetime=300)

        
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


    def change_zone(self, event):
        if event.action == "pressed":
            if event.direction == "up":
                self.zone = (self.zone + 1) % 3  
            elif event.direction == "down":
                self.zone = (self.zone - 1) % 3  
        
        print(f"Selected Zone: {self.zone}")
        self.client.publish(TOPIC_COORDINATES, str(self.zone))

    
        
    def shutdown(self, signum, frame):
        logging.info("Shutting down gracefully...")
        self.client.disconnect()
        self.driver.stop()
        self.sense.clear()  # Turn off LED display
        GPIO.cleanup()  # Cleanup GPIO on shutdown
        sys.exit(0)

    def on_connect(self, client, userdata, flags, rc):
        logging.info(f"Connected with result code {rc}")
        if rc == 0:
            logging.info("Successfully connected to broker.")
        else:
            logging.error(f"Failed to connect. Code {rc}")
            
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
        if msg.topic == TOPIC_LOCK:
            logging.info("Scooter locked.")
            self.driver.send("lock", "scooter_machine")
            self.sense.clear((255, 0, 0))  # Red for locked
        elif msg.topic == TOPIC_UNLOCK:
            logging.info("Scooter unlocked.")
            self.driver.send("unlock", "scooter_machine")
            self.sense.clear((0, 255, 0)) # Green for unlocked

    def send_json(self):
        
        """
        Zone handling. It sends arbitrary coordinates to the server, which decides the zone.
        We use a button on the rasberry pi to simulate different areas/coordinates
        """
        # Sense HAT color for coordinate zones
        if self.zone == 0:
            coordinates = (0.0,0.0)
            self.sense.clear((255, 0, 0))  # Red for zone 0
        elif self.zone == 1:
            coordinates = (50.0, 50.0)
            self.sense.clear((255, 255, 0))  # Yellow for zone 1
        elif self.zone == 2:
            coordinates = (100.0, 100.0)
            self.sense.clear((0, 255, 0))  # Green for zone 2
            
        timestamp = datetime.now().isoformat()
            
        message = {
            "command": "location_ping",
            "coordinatess": coordinates,
            "timestamp": timestamp,
            "id": self.id
        }
        
        logging.info(f"Sending coordinate JSON: {message}")
        self.client.publish(TOPIC_COORDINATES, json.dumps(message))


        
        #coordinates = random.choice([0, 1, 2])# Random zone selection (red, yellow, green), change later
        print(f"Sending coordinates: {coordinates}")
        self.client.publish(TOPIC_COORDINATES, coordinates)    
    
    
    def run(self):
        try:
            while True:
                self.send_coordinates()
                time.sleep(5)
                for event in self.sense.stick.get_events():
                    self.change_zone(event)
        except Exception as e:
            logging.error(f"Error in run loop: {e}")
            self.shutdown(None, None)

if __name__ == "__main__":
    scooter = Scooter()
    scooter.run()
