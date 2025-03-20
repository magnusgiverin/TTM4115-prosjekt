import paho.mqtt.client as mqtt
import random
from stmpy import Machine, Driver
import logging
import time
import ssl
import json
from datetime import datetime
"""
from sense_hat import SenseHat
import RPi.GPIO as GPIO  # For button handling
"""
import signal
import sys

# MQTT_BROKER = 'mqtt20.iik.ntnu.no'
# MQTT_PORT = 1883

# MQTT_TOPIC_INPUT = 'ttm4115/team_4_project/command'

TOPIC_COORDINATES = 'ttm4115/team_4_project/command'

#sense = SenseHat() # må kanskje fjernes


FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60

BUTTON_PIN = 17

# Configure logging for Raspberry Pi
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class Scooter:
    def __init__(self, id: int, client: object, coordinates: (float)):
        self.id = id
        self.is_locked = True
        self.client = client
        self.coordinates = coordinates
        # self.client.on_connect = self.on_connect
        # self.client.on_disconnect = self.on_disconnect
        # self.client.on_message = self.on_message
        #self.client.connect(MQTT_BROKER, 1883, 60)
        
        #self.sense = SenseHat()
        
        self.zone = None
        """
        # Button setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=self.change_zone, bouncetime=300)
        """

        t1 = {
            "source": "initial", 
            "target": "locked", 
            'effect': "status_timer()"
        }
        
        t2 = {
            "trigger": "unlock", 
            "source": "locked", 
            "target": "unlocked",
            'effect':"unlock_scooter()"
        }
        
        t3 = {
            "trigger": "lock", 
            "source": "unlocked", 
            "target": "locked", 
            'effect':"lock_scooter()"
        }
        
        t4 = {
            "trigger": "status_timer", 
            "source": "locked", 
            "target": "locked", 
            'effect':"send_status()"
        }
        
        t5 = {
            "trigger": "status_timer", 
            "source": "unlocked", 
            "target": "unlocked", 
            'effect':"send_status()"
        }
        
        self.stm = Machine(name=f"scooter_{self.id}", transitions=[t1, t2, t3, t4, t5], obj=self)
                
        """        
        self.stm= Machine(

            name=f"scooter_{self.id}",
            
            states=[

                {"name": "locked", "entry": "lock_scooter()", "exit": "send_status()"},
                {"name": "unlocked", "entry": "unlock_scooter()", "exit": "send_status()"},

            ],
            transitions=[
                {"source": "initial", "target": "locked"},  
                {"trigger": "unlock", "source": "locked", "target": "unlocked"},
                {"trigger": "lock", "source": "unlocked", "target": "locked"},
            ],obj=self,)
        """
        
    def change_zone(self, event):
        
        if event.action == "pressed":
            if event.direction == "up":
                self.zone = (self.zone + 1) % 3  
            elif event.direction == "down":
                self.zone = (self.zone - 1) % 3  
        
        print(f"Selected Zone: {self.zone}")
        self.client.mqtt_client.publish(TOPIC_COORDINATES, str(self.zone))
    
    def status_timer(self):
        self.stm.start_timer("status_timer", 5000)
        
    def lock_scooter(self):
        try:
            logging.info("Scooter is now locked.")
            self.is_locked = True
            #self.sense.clear((255, 0, 0)) # Red for locked
            
            message = {
                "type": "response",
                "command": "lock",
                "scooter_id": self.id,
                "coordinates": self.coordinates
            }        
            
            self.client.mqtt_client.publish(TOPIC_COORDINATES, json.dumps(message))
        
        except Exception as e:
            message = {
                "type": "response",
                "command": "error",
                "crash": True,
                "crash_message": "lock",
                "scooter_id": self.id
            } 
            self.client.mqtt_client.publish(TOPIC_COORDINATES, json.dumps(message))
        
    def unlock_scooter(self):
        try:
            logging.info("Scooter is now unlocked.")
            self.is_locked = False
            #self.sense.clear((0, 255, 0))  # Green for unlocked
            
            message = {
                "type": "response",
                "command": "unlock",
                "scooter_id": self.id,
                "coordinates": self.coordinates
            }        
            
            self.client.mqtt_client.publish(TOPIC_COORDINATES, json.dumps(message))
        
        except Exception as e:
            message = {
                "type": "response",
                "command": "error",
                "crash": True,
                "crash_message": "unlock",
                "scooter_id": self.id
            } 
            self.client.mqtt_client.publish(TOPIC_COORDINATES, json.dumps(message))
#    
#     def shutdown(self, signum, frame):
#         logging.info("Shutting down gracefully...")
#         self.client.disconnect()
#         self.driver.stop()
#         #self.sense.clear()  # Turn off LED display
#         GPIO.cleanup()  # Cleanup GPIO on shutdown
#         sys.exit(0)

#     def on_connect(self, client, userdata, flags, rc):
#         logging.info(f"Connected with result code {rc}")
#         if rc == 0:
#             logging.info("Successfully connected to broker.")
#         else:
#             logging.error(f"Failed to connect. Code {rc}")
            
#         client.subscribe(TOPIC_COORDINATES)
#         client.subscribe(TOPIC_COORDINATES)
        

#     def on_disconnect(self, client, userdata, rc):
#         logging.info("Disconnected with result code: %s", rc)
#         reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
#         while reconnect_count < MAX_RECONNECT_COUNT:
#             logging.info("Reconnecting in %d seconds...", reconnect_delay)
#             time.sleep(reconnect_delay)

#             try:
#                 client.reconnect()
#                 logging.info("Reconnected successfully!")
#                 return
#             except Exception as err:
#                 logging.error("%s. Reconnect failed. Retrying...", err)

#             reconnect_delay *= RECONNECT_RATE
#             reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
#             reconnect_count += 1
#         logging.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)

# 
    
    def send_status(self):
        
        """
        Zone handling. It sends arbitrary coordinates to the server, which decides the zone.
        We use a button on the rasberry pi to simulate different areas/coordinates
        """
        
        self.stm.start_timer("status_timer", 5000)
        
        # Sense HAT color for coordinate zones
        if self.zone == 0:
            self.coordinates = (0.0,0.0)
        elif self.zone == 1:
            self.coordinates = (50.0, 50.0)
        elif self.zone == 2:
            self.coordinates = (100.0, 100.0)
            
        timestamp = int(datetime.now().timestamp())
            
        message = {
            "command": "location_ping",
            "coordinates": self.coordinates,
            "timestamp": timestamp,
            "scooter_id": self.id,
        }

        logging.info(f"Sending coordinate JSON: {message}")
        self.client.mqtt_client.publish(TOPIC_COORDINATES, json.dumps(message))