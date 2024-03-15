import os

import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import logging

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

# Create a client instance
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "SubscriberClient")

# Set authentication for the client
client.username_pw_set(username, password)


# Event handlers
def on_connect(client, userdata, flags, return_code):
    if return_code != 0:
        return logging.info("could not connect, return code:", return_code)

    logging.info("Connected to broker")
    logging.info("Subscribing to topic: " + topic)
    return client.subscribe(topic)


def on_message(client, userdata, message):
    decoded_message = str(message.payload.decode("utf-8"))
    logging.info("Received message: " + decoded_message)


# Assign event handlers
client.on_connect = on_connect
client.on_message = on_message


def run():
    logging.info("Connecting to broker")
    client.connect(host, port)

    logging.info("Starting MQTT subscriber")
    client.loop_forever()


if __name__ == "__main__":
    run()
