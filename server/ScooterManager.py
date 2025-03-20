import json
import stmpy
import paho.mqtt.client as mqtt
import logging
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from Scooter import Scooter

MQTT_BROKER = 'mqtt20.iik.ntnu.no'
MQTT_PORT = 1883

MQTT_TOPIC_INPUT = 'ttm4115/team_4_project/command'
MQTT_TOPIC_OUTPUT = 'ttm4115/team_4_project/answer'

class ScooterManagerComponent:
    """
    The component to manage communication between the Scooter and the Server.

    This component connects to an MQTT broker and listens to commands to and from the Scooter and the Server.
    To interact with the component, do the following:

    * Connect to the same broker as the component. You find the broker address
    in the value of the variable `MQTT_BROKER`.
    * Subscribe to the topic in variable `MQTT_TOPIC_OUTPUT`. On this topic, the
    component sends its answers.
    * Send the messages listed below to the topic in variable `MQTT_TOPIC_INPUT`.

    The component takes requests from the front-end (on_http_request), and sends the information to the stm for that specific scooter.
    The component also listens to MQTT messages from the scooter, and sends the information to the front-end.
    
    The component listens to the following commands:
        {
            "command": "start",
            "type": "request",
            "coords": (int, int),
        }
        
        {
            "command": "coordinates",
            "coords": (int, int),
            "timestamp": int,
            "scooter_id": int,
        }
    """

    def on_connect(self, client, userdata, flags, rc):
        # we just log that we are connected
        self._logger.debug('MQTT connected to {}'
        
    def get_locations(self):
        return self.locations
    
    def get_response(self, scooter_id):
        pass
    
    def on_message(self, client, userdata, msg):
        """
        Processes incoming MQTT messages.

        We assume the payload of all received MQTT messages is an UTF-8 encoded
        string, which is formatted as a JSON object. The JSON object contains
        a field called `command` which identifies what the message should achieve.

        As a reaction to a received message, we can for example do the following:

        * create a new state machine instance to handle the incoming messages,
        * route the message to an existing state machine session,
        * handle the message right here,
        * throw the message away.

        """
        self._logger.debug('Incoming message to topic {}'.format(msg.topic))

        # TODO unwrap JSON-encoded payload
    
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception as err:
            self._logger.error('Message sent to topic {} had no valid JSON. Message ignored. {}'.format(msg.topic, err))
            return
        
        command = payload.get('command')
        type = payload.get('type')
        
        if command == "location_ping":
            id = payload.get('scooter_id')
            coordinates = payload.get('coordinates')
            timestamp = payload.get('timestamp')
            
            if id and coordinates and timestamp:
                self.locations[id] = (id, coordinates, timestamp)
        
        if type == "response":
            if command == "lock" or command == "unlock":
                id = payload.get('scooter_id')
                coordinates = payload.get('coordinates')
                
                
        # if command == 'new_timer':
        #     name = payload.get('name')
        #     duration = payload.get('duration')
        #     if name and duration:
        #         timer_logic = Scooter(name, duration, self)
        #         self.stm_driver.add_machine(timer_logic.stm)
        #     else:
        #         self._logger.error('Invalid payload for new_timer command.')
                
        # elif command == 'status_all_timers':
        #     for key in self.stm_driver._stms_by_id:
        #         stm = self.stm_driver._stms_by_id[key]._obj
        #         self.stm_driver.send('status_single_timer', stm.name)
                
        # elif command == 'status_single_timer':
        #     # handle status_single_timer command
        #     name = payload.get('name')
        #     if name:
        #         self.stm_driver.send('status_single_timer', name)
        #     else:
        #         self._logger.error('Invalid payload for status_single_timer command.')
        
        # elif command == 'cancel_timer':
        #     name = payload.get('name')
        #     if name:
        #         self.stm_driver.send('timer_stop', name)
                
        else:
            self._logger.error('Unknown command received.')
        
        # TODO extract command

        # TODO determine what to do

    def __init__(self):
        """
        Start the component.

        ## Start of MQTT
        We subscribe to the topic(s) the component listens to.
        The client is available as variable `self.client` so that subscriptions
        may also be changed over time if necessary.

        The MQTT client reconnects in case of failures.

        ## State Machine driver
        We create a single state machine driver for STMPY. This should fit
        for most components. The driver is available from the variable
        `self.driver`. You can use it to send signals into specific state
        machines, for instance.

        """
        # get the logger object for the component
        self._logger = logging.getLogger(__name__)
        print('logging under name {}.'.format(__name__))
        self._logger.info('Starting Component')

        # create a new MQTT client
        self._logger.debug('Connecting to MQTT broker {} at port {}'.format(MQTT_BROKER, MQTT_PORT))
        self.mqtt_client = mqtt.Client()
        
        # callback methods
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        # Connect to the broker
        self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        
        # subscribe to proper topic(s) of your choice
        self.mqtt_client.subscribe(MQTT_TOPIC_INPUT)
        
        # start the internal loop to process MQTT messages
        self.mqtt_client.loop_start()

        # we start the stmpy driver, without any state machines for now
        self.stm_driver = stmpy.Driver()
        self.stm_driver.start(keep_active=True)
        self._logger.debug('Component initialization finished')

        # create some scooters as stms
        self.locations = {}
        for i in range(3):
            scooter = Scooter(i, self)
            self.stm_driver.add_machine(scooter.stm)

    def stop(self):
        """
        Stop the component.
        """
        # stop the MQTT client
        self.mqtt_client.loop_stop()

        # stop the state machine Driver
        self.stm_driver.stop()

# asdf