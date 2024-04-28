import json
import logging
import os
import threading
import time
from collections import deque

import numpy as np
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

from calc import TrilaterationController
from filter import apply_kalman_filter, initialize_kalman_filter
from graph import animate
from utils import convert_string_to_datetime

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# State to stop the threads
stop_threads = False

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

# Test data
# fmt: off
receiver_1.append({"time": "2021-08-01 12:00:00", "address": "address_1", "rssi": -42, "filtered_rssi": [-42]})
receiver_2.append({"time": "2021-08-01 12:00:00", "address": "address_2", "rssi": -42, "filtered_rssi": [-42]})
receiver_3.append({"time": "2021-08-01 12:00:00", "address": "address_3", "rssi": -42, "filtered_rssi": [-42]})
# fmt: on

# Initialize the Kalman filter for the 3 receivers
kf1 = initialize_kalman_filter()
kf2 = initialize_kalman_filter()
kf3 = initialize_kalman_filter()


# todo: take these as inputs
receiver_1_pos = (0, 2.2)
receiver_2_pos = (3.2, 0)
receiver_3_pos = (3.2, 3.1)
position = (0, 0)

# Initialize the trilateration controller
locationEstimator = TrilaterationController(
    bp_1=receiver_1_pos,
    measured_power_1=-50,
    bp_2=receiver_2_pos,
    measured_power_2=-40,
    bp_3=receiver_3_pos,
    measured_power_3=-53,
    path_loss_exponent=1.8,
)


# MQTT event handlers
def on_connect(client, userdata, flags, return_code):
    if return_code != 0:
        return logging.info("could not connect, return code:", return_code)

    logging.info("Connected to broker")
    logging.info("Subscribing to topic: " + topic)
    return client.subscribe(topic)


def on_message(client, userdata, message):
    logging.info(message.topic + " - Received message: " + str(message.payload))
    try:
        # message (payload, topic, timestamp)
        decoded_message = str(message.payload.decode("utf-8"))
        response = json.loads(decoded_message)  # (time, address, rssi)
        response["time"] = convert_string_to_datetime(response["time"])

        # Apply Kalman filter to the RSSI values and store them
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

    except Exception as e:
        logging.error("Error processing message: " + str(e))


# Assign event handlers
client.on_connect = on_connect
client.on_message = on_message


# Process the rssi values in parallel
def process_values():
    global position

    while not stop_threads:
        if receiver_1 and receiver_2 and receiver_3:
            logging.info(
                "Latest Values: "
                + " | ".join(
                    map(
                        str,
                        [
                            receiver_1[-1]["rssi"],
                            receiver_2[-1]["rssi"],
                            receiver_3[-1]["rssi"],
                        ],
                    )
                )
            )
            logging.info(
                "Latest Filtered: "
                + " | ".join(
                    map(
                        str,
                        [
                            receiver_1[-1]["filtered_rssi"],
                            receiver_2[-1]["filtered_rssi"],
                            receiver_3[-1]["filtered_rssi"],
                        ],
                    )
                )
            )

        # Calculate the estimated position
        if not (receiver_1 and receiver_2 and receiver_3):
            logging.info("Not enough data to calculate position")
            time.sleep(5)
            continue

        # print("Type of rssi_1: ", type(receiver_1[-1]["filtered_rssi"]))
        rssi_1 = receiver_1[-1]["filtered_rssi"][0]
        rssi_2 = receiver_2[-1]["filtered_rssi"][0]
        rssi_3 = receiver_3[-1]["filtered_rssi"][0]

        # Update the position
        position = locationEstimator.get_position(rssi_1, rssi_2, rssi_3)
        logging.info(f"Estimated position: {position}")

        time.sleep(5)


def run_graph():
    def get_updated_data():
        base_stations = [
            {
                "coords": receiver_1_pos,
                "distance": locationEstimator.get_distance(
                    receiver_1[-1]["filtered_rssi"][0], 1
                ),
            },
            {
                "coords": receiver_2_pos,
                "distance": locationEstimator.get_distance(
                    receiver_2[-1]["filtered_rssi"][0], 2
                ),
            },
            {
                "coords": receiver_3_pos,
                "distance": locationEstimator.get_distance(
                    receiver_3[-1]["filtered_rssi"][0], 3
                ),
            },
        ]
        return (
            base_stations,
            locationEstimator.trilaterate(
                base_stations[0]["distance"],
                base_stations[1]["distance"],
                base_stations[2]["distance"],
            ),
        )

    animate(
        get_updated_data()[0],
        (0, 0),
        get_updated_data,
    )


def run():
    global stop_threads

    try:
        logging.info("Connecting to broker")
        client.connect(host, port)

        # Start the processing thread
        logging.info("Starting processing thread")
        processing_thread = threading.Thread(target=process_values, daemon=True)
        processing_thread.start()

        # Start the MQTT subscriber loop in a new thread
        logging.info("Starting MQTT subscriber")
        mqtt_thread = threading.Thread(target=client.loop_forever, daemon=True)
        mqtt_thread.start()

        # Start the graph animation in the main thread
        logging.info("Starting graph animation")
        run_graph()

    except KeyboardInterrupt:
        logging.info("Gracefully stopping the program")

        # Stop the threads
        stop_threads = True
        client.disconnect()
        processing_thread.join()
        mqtt_thread.join()
        logging.info("Stopped.")

        # Exit the program
        exit(0)


if __name__ == "__main__":
    run()
