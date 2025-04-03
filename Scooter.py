import uuid
import paho.mqtt.client as mqtt
import random
from stmpy import Machine, Driver
import logging
import time
import ssl
import json
from datetime import datetime
from sense_hat import SenseHat

# MQTT_TOPIC_INPUT = 'ttm4115/team_4_project/command'

#sense = SenseHat() # må kanskje fjernes


FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60
MIN_COORDS = 0
MAX_COORDS = 100

BUTTON_PIN = 17

# Configure logging for Raspberry Pi
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class Scooter:
    def __init__(self):
        self.id = None
        self.coordinates = [random.randint(0, 100), random.randint(0, 100)]
        self.is_locked = True
        self.sensitivity = 10

        self.unlock_time = None
        self.stm_driver = Driver()

        self.ping_interval = 50

        self.MQTT_BROKER = 'mqtt20.iik.ntnu.no'
        self.MQTT_PORT = 1883
        self.MQTT_TOPIC_INPUT = 'ttm4115/team_4_project/command/test'

        # self.client.on_connect = self.on_connect
        # self.client.on_disconnect = self.on_disconnect
        # self.client.on_message = self.on_message
        #self.client.connect(MQTT_BROKER, 1883, 60)

        #self.zone = None
        """
        # Button setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=self.change_zone, bouncetime=300)
        """

        self._logger = logging.getLogger(__name__)

        self.mqtt_client = mqtt.Client()

        # callback methods
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        # Connect to the broker
        self.mqtt_client.connect(self.MQTT_BROKER, self.MQTT_PORT)

        # subscribe to proper topic(s) of your choice
        self.mqtt_client.subscribe(self.MQTT_TOPIC_INPUT)

        # start the internal loop to process MQTT messages
        self.mqtt_client.loop_start()

        self.make_stm()

        self.tag = str(uuid.uuid4())
        self.user_id = None
        self.transaction_id = None

        self.sense = SenseHat()
        self.sense.stick.direction_up = self.pushed_up
        self.sense.stick.direction_down = self.pushed_down
        self.sense.stick.direction_right = self.pushed_right
        self.sense.stick.direction_left = self.pushed_left

        self.sense.show_message("Locked")

        try:
            message = {
                "command": "init_scooter",
                "type": "request",
                "tag": self.tag,
            }

            logging.info(f"Sending init JSON: {message}")

            self.mqtt_client.publish(self.MQTT_TOPIC_INPUT, json.dumps(message))

        except Exception as e:
            logging.info(f'Init error {e}')


    def make_stm(self):

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
            'effect': "send_status()"
        }

        t6 = {
            "trigger": "unlock",
            "source": "unlocked",
            "target": "unlocked",
            'effect': "send_error()"
        }

        t7 = {
            "trigger": "lock",
            "source": "locked",
            "target": "locked",
            'effect': "send_error()"
        }

        self.stm = Machine(name=f"scooter_{self.id}", transitions=[t1, t2, t3, t4, t5, t6, t7], obj=self)
        self.stm_driver.add_machine(self.stm)
        self.stm_driver.start()

    def on_connect(self, client, userdata, flags, rc):
        # we just log that we are connected
        self._logger.debug('MQTT connected to {}'.format(client))

    def on_message(self, client, userdata, msg):
        payload = json.loads(msg.payload.decode())

        type = payload.get("type")

        if(type == "response" and payload.get("command") == "init_scooter"):
            tag = payload.get("tag")
            if(self.tag == tag):
                self.id = payload.get("scooter_id")
                logging.info(f"Initialised tag: {self.tag}")

        elif(type == "request" and payload.get("command") in ["lock", "unlock"] and payload.get("scooter_id") == self.id):
            self.transaction_id = payload.get("transaction_id")
            self.user_id = payload.get("user_id")
            self.stm.send(payload.get("command"))

    # def change_zone(self, event):

    #     if event.action == "pressed":
    #         if event.direction == "up":
    #             self.zone = (self.zone + 1) % 3
    #         elif event.direction == "down":
    #             self.zone = (self.zone - 1) % 3

    #     print(f"Selected Zone: {self.zone}")
    #     self.client.mqtt_client.publish(self.topic_coordinates, str(self.zone))

    def status_timer(self):
        self.stm.start_timer("status_timer", self.ping_interval)

    def lock_scooter(self):
        logging.info("Scooter is now locked.")
        self.is_locked = True
        # Timer stop. Send timer
        if self.unlock_time is not None:
            duration = int(time.time() - self.unlock_time)
            self.unlock_time = None
        else:
            duration = 0

        #self.sense_light()
        #self.sense.clear((255, 0, 0)) # Red for locked

        message = {
            "type": "response",
            "command": "lock",
            "scooter_id": self.id,
            "coordinates": self.coordinates,
            "timer": duration,
            "transaction_id": self.transaction_id,
        }


        self.transaction_id = None
        self.user_id = None
        
        self.mqtt_client.publish(self.MQTT_TOPIC_INPUT, json.dumps(message))
        self.sense.show_message("Locked")

    def unlock_scooter(self):
        logging.info("Scooter is now unlocked.")
        self.is_locked = False
        # Timer start
        self.unlock_time = time.time()
        #self.sense_light()
        #self.sense.clear((0, 255, 0))  # Green for unlocked
        
        message = {
            "command": "unlock",
            "type": "response",
            "scooter_id": self.id,
            "coordinates": self.coordinates,
            "transaction_id": self.transaction_id,
        }

        self.transaction_id = None
        self.mqtt_client.publish(self.MQTT_TOPIC_INPUT, json.dumps(message))

        self.sense.show_message("Unlocked")

    def send_error(self):
        logging.info("Invalid command recieved.")

        if(self.is_locked):
            message = {
                "command": "error",
                "message": f"Trying to lock a locked scooter"
            }
        else:
            message = {
                "command": "error",
                "message": f"Trying to unlock an unlocked scooter"
            }

        self.mqtt_client.publish(self.MQTT_TOPIC_INPUT, json.dumps(message))

#     def shutdown(self, signum, frame):
#         logging.info("Shutting down gracefully...")
#         self.client.disconnect()
#         self.driver.stop()
#         #self.sense.clear()  # Turn off LED display
#         GPIO.cleanup()  # Cleanup GPIO on shutdown
#         sys.exit(0)


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

    def send_status(self):

        """
        Zone handling. It sends arbitrary coordinates to the server, which decides the zone.
        We use a button on the rasberry pi to simulate different areas/coordinates
        """

        self.stm.start_timer("status_timer", self.ping_interval)

        timestamp = int(datetime.now().timestamp())

        message = {
            "command": "ping",
            "data": json.dumps({"coordinates": self.coordinates, "locked": self.is_locked, "user_id": self.user_id}),
            "timestamp": timestamp,
            "scooter_id": self.id,
            "ping_interval": self.ping_interval,
        }

        logging.info(f"Sending data JSON for: {self.id}")
        self.mqtt_client.publish(self.MQTT_TOPIC_INPUT, json.dumps(message))

    def pushed_up(self):
        if not self.is_locked:
            self.coordinates[1] = max(self.coordinates[1] - 1, MIN_COORDS)
            print("Moving - coordinates: ", self.coordinates)

    def pushed_down(self):
        if not self.is_locked:
            self.coordinates[1] = min(self.coordinates[1] + 1, MAX_COORDS)
            print("Moving - coordinates: ", self.coordinates)

    def pushed_right(self):
        if not self.is_locked:
            self.coordinates[0] = max(self.coordinates[0] + 1, MIN_COORDS)
            print("Moving - coordinates: ", self.coordinates)

    def pushed_left(self):
        if not self.is_locked:
            self.coordinates[1] = min(self.coordinates[1] - 1, MAX_COORDS)
            print("Moving - coordinates: ", self.coordinates)


if __name__ == "__main__":
    Scooter()