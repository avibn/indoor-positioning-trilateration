import asyncio
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
from controller import Controller
from environment import *
from filter import apply_kalman_filter, initialize_kalman_filter
from graph import animate, set_on_close
from utils import convert_string_to_datetime

RUN_PIXEL_DISPLAY = True  # Whether to run the pixel display
GRAPH_REFRESH_INTERVAL = 2  # Refresh interval for the graph (seconds)
DISPLAY_REFRESH_INTERVAL = 4  # Refresh interval for the pixe ldisplay (seconds)

# Load env variables from .env file
load_dotenv()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# State to stop the threads
stop_threads = False

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


# Initialize the trilateration controller
locationEstimator = TrilaterationController(
    bp_1=RECEIVER_1_POS,
    bp_2=RECEIVER_2_POS,
    bp_3=RECEIVER_3_POS,
    measured_power_1=RECEIVER_1_TX_POWER,
    measured_power_2=RECEIVER_2_TX_POWER,
    measured_power_3=RECEIVER_3_TX_POWER,
    path_loss_exponent=PATH_LOSS_EXPONENT,
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

# Bluetooth controller
if RUN_PIXEL_DISPLAY:
    bt = Controller("DC:03:BB:B0:67:4A")

    # Set the beacons on the display
    bt.set_beacons(
        [
            locationEstimator.scale_coordinates(*RECEIVER_1_POS),
            locationEstimator.scale_coordinates(*RECEIVER_2_POS),
            locationEstimator.scale_coordinates(*RECEIVER_3_POS),
        ]
    )

    # Create a global event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.set_event_loop(loop)

    async def update_plot(x, y):
        """
        Update the plot with the given x and y values.

        Parameters:
        x (list): The x values for the plot.
        y (list): The y values for the plot.

        Returns:
        None
        """
        logging.info("+++ Updating plot: " + str(x) + ", " + str(y))
        await bt.plot(x, y)


def process_values():
    while not stop_threads:
        if receiver_1 and receiver_2 and receiver_3:
            logging.info(
                f"Latest Values: {' | '.join(str(receiver[-1]['rssi']) for receiver in [receiver_1, receiver_2, receiver_3])}"
            )
            logging.info(
                f"Latest Filtered: {' | '.join(str(receiver[-1]['filtered_rssi']) for receiver in [receiver_1, receiver_2, receiver_3])}"
            )

        # Calculate the estimated position
        if not (receiver_1 and receiver_2 and receiver_3):
            logging.info("Not enough data to calculate position")
            time.sleep(5)
            continue

        rssi_1 = receiver_1[-1]["filtered_rssi"][0]
        rssi_2 = receiver_2[-1]["filtered_rssi"][0]
        rssi_3 = receiver_3[-1]["filtered_rssi"][0]

        # Update the position
        position = locationEstimator.get_position(rssi_1, rssi_2, rssi_3)
        logging.info(f"Estimated position: {position}")

        # Update the display
        if RUN_PIXEL_DISPLAY:
            loop.run_until_complete(update_plot(position[0], position[1]))

        time.sleep(DISPLAY_REFRESH_INTERVAL)


def run_graph():
    def get_updated_data():
        base_stations = [
            {
                "coords": RECEIVER_1_POS,
                "distance": locationEstimator.get_distance(
                    receiver_1[-1]["filtered_rssi"][0], 1
                ),
            },
            {
                "coords": RECEIVER_2_POS,
                "distance": locationEstimator.get_distance(
                    receiver_2[-1]["filtered_rssi"][0], 2
                ),
            },
            {
                "coords": RECEIVER_3_POS,
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
        interval=GRAPH_REFRESH_INTERVAL * 1000,
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

        # Set on graph close (raise KeyboardInterrupt)
        # todo:: fix this
        def on_close(event):
            logging.info("Closing graph")

        set_on_close(on_close)

        # Start the graph animation in the main thread
        logging.info("Starting graph animation")
        run_graph()

    except KeyboardInterrupt:
        logging.info("Gracefully shutting down...")

        # Stop the threads
        stop_threads = True
        client.disconnect()
        logging.info("MQTT disconnected.")

        processing_thread.join()
        logging.info("Processing (display) thread stopped.")

        mqtt_thread.join()
        logging.info("MQTT thread stopped.")

        # Stop bt
        if RUN_PIXEL_DISPLAY:
            loop.run_until_complete(bt.disconnect())
            logging.info("Bluetooth disconnected.")

        # Exit the program
        exit(0)


if __name__ == "__main__":
    run()
