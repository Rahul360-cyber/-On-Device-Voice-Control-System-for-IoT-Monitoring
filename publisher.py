"""
MQTT Publisher
"""
import psutil
import uuid
import time
import json
from datetime import datetime
from time import sleep
import paho.mqtt.client as mqtt

# Create a new MQTT client
client = mqtt.Client()
# Connect to MQTT broker
client.connect('mqtt.eclipseprojects.io', 1883)

mac_address = hex(uuid.getnode())

# Infinite loop to continuously collect and publish data every 10 seconds
while True:
    data_records = []

    # Collect data for 10 seconds
    for i in range(10):
        timestamp = int(time.time() * 1000)  # timestamp in ms
        battery_level = psutil.sensors_battery().percent
        power_plugged = int(psutil.sensors_battery().power_plugged)

        record = {
            'timestamp': timestamp,
            'battery_level': battery_level,
            'power_plugged': power_plugged
        }

        data_records.append(record)
        time.sleep(1)

    # Publish collected data every 10 seconds
    data = {
        'mac_address': mac_address,
        'events': data_records
    }

    # Converting to json format
    my_string = json.dumps(data, sort_keys=False, indent=4)
    client.publish('s316411', my_string)
