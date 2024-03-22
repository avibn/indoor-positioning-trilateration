import json
import logging
import os
import threading
import time
from collections import deque

import numpy as np
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

from calc import get_position
from filter import apply_kalman_filter, initialize_kalman_filter
from graph import animate
from utils import convert_string_to_datetime

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Load env variables from .env file
load_dotenv()

# Environment variables
host = os.getenv("MQTT_HOST")
port = int(os.getenv("MQTT_PORT"))
username = os.getenv("MQTT_USERNAME")
password = os.getenv("MQTT_PASSWORD")
topic = os.getenv("MQTT_TOPIC")

if not all([host, port, username, password, topic]):
    logging.error("Environment variables not set")
    exit(1)

# Create a client instance
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "SubscriberClient")

# Set authentication for the client
client.username_pw_set(username, password)

# Stores for messages (max length 10 - removes old values when full)
receiver_1 = deque(maxlen=10)
receiver_2 = deque(maxlen=10)
receiver_3 = deque(maxlen=10)

# Todo:: remove
# Test data
# fmt: off
receiver_2.append({"time": "2021-08-01 12:00:00", "address": "address_2", "rssi": -42, "filtered_rssi": -42})
receiver_3.append({"time": "2021-08-01 12:00:00", "address": "address_3", "rssi": -42, "filtered_rssi": -42})
# fmt: on

# Initialize the Kalman filter for the 3 receivers
kf1 = initialize_kalman_filter()
kf2 = initialize_kalman_filter()
kf3 = initialize_kalman_filter()


# Event handlers
def on_connect(client, userdata, flags, return_code):
    if return_code != 0:
        return logging.info("could not connect, return code:", return_code)

    logging.info("Connected to broker")
    logging.info("Subscribing to topic: " + topic)
    return client.subscribe(topic)


def on_message(client, userdata, message):
    logging.info("Received message: " + str(message.payload))
    try:
        # message (payload, topic, timestamp)
        decoded_message = str(message.payload.decode("utf-8"))
        response = json.loads(decoded_message)  # (time, address, rssi)
        response["time"] = convert_string_to_datetime(response["time"])

        if message.topic == "receivers/1":
            response["filtered_rssi"] = apply_kalman_filter(kf1, response["rssi"])
            receiver_1.append(response)
        elif message.topic == "receivers/2":
            response["filtered_rssi"] = apply_kalman_filter(kf2, response["rssi"])
            receiver_2.append(response)
        elif message.topic == "receivers/3":
            response["filtered_rssi"] = apply_kalman_filter(kf3, response["rssi"])
            receiver_3.append(response)
        else:
            return logging.error("Unknown topic received: " + message.topic)

        # logging.info("Current list 1: " + str(list(map(lambda x: x["rssi"], receiver_1))))
        # logging.info("Current list 1: " + str(list(map(lambda x: x["filtered_rssi"], receiver_1))))
    except Exception as e:
        logging.error("Error processing message: " + str(e))


# Assign event handlers
client.on_connect = on_connect
client.on_message = on_message


# todo: take these as inputs
receiver_1_pos = (0, 2.2)
receiver_2_pos = (3.2, 0)
receiver_3_pos = (3.2, 3.1)
position = (0, 0)


# code to process the rssi values in parallel
def process_values():
    while True:
        if receiver_1:
            logging.info(
                "**Latest value from receiver 1: " + str(receiver_1[-1]["rssi"])
            )
        # if receiver_2:
        #     logging.info("Latest value from receiver 2: " + str(receiver_2[-1]))
        # if receiver_3:
        #     logging.info("Latest value from receiver 3: " + str(receiver_3[-1]))

        # Calculate the estimated position
        if not (receiver_1 and receiver_2 and receiver_3):
            logging.info("Not enough data to calculate position")
            time.sleep(5)
            continue

        rssi_1 = receiver_1[-1]["filtered_rssi"]
        rssi_2 = receiver_2[-1]["filtered_rssi"]
        rssi_3 = receiver_3[-1]["filtered_rssi"]

        position = get_position(
            receiver_1_pos,
            receiver_2_pos,
            receiver_3_pos,
            rssi_1,
            rssi_2,
            rssi_3,
        )
        print(f"Estimated position: {position}")

        time.sleep(5)


def run_graph():
    # use receiver dequeue to get the latest distance values
    # todo:: use __rssi_to_distance from calc.py to get the distances
    base_stations = [
        {"coords": receiver_1_pos, "distance": 1.5},
        {"coords": receiver_2_pos, "distance": 1.5},
        {"coords": receiver_3_pos, "distance": 1.5},
    ]

    get_updated_data = lambda: (
        base_stations,
        (
            np.random.randint(0, 5),
            np.random.randint(0, 5),
        ),  # todo:: use `position` instead
    )

    animate(base_stations, (0, 0), get_updated_data)


def run():
    logging.info("Connecting to broker")
    client.connect(host, port)

    # Start the processing thread
    threading.Thread(target=process_values, daemon=True).start()

    logging.info("Starting MQTT subscriber")
    # Start the MQTT subscriber loop in a new thread
    threading.Thread(target=client.loop_start, daemon=True).start()

    run_graph()
    client.loop_forever()


if __name__ == "__main__":
    run()
