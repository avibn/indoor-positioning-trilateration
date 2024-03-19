import json
import ssl
import time

import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_ntp
import socketpool
import wifi
from adafruit_ble import BLERadio
from adafruit_ble.advertising import Advertisement
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement

# Get wifi details and more from a secrets.py file
try:
    from secrets import addresses_to_filter, mqtt_env, secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Connect to WiFi
wifi.radio.connect(secrets["ssid"], secrets["password"])

# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)

# Get time server (Network Time Protocol)
ntp = adafruit_ntp.NTP(pool, tz_offset=0)

# Bluetooth
ble = BLERadio()
counter = 0

# Set up MQTT client
mqtt_client = MQTT.MQTT(
    broker=mqtt_env["broker"],
    port=mqtt_env["port"],
    username=mqtt_env["username"],
    password=mqtt_env["password"],
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
)


# MQTT Event Handlers
def __mqtt_connect_handler(mqtt_client, userdata, flags, rc):
    print("Successfully connected to MQTT broker.")
    print("     Flags: {0}\n     RC: {1}".format(flags, rc))


def __mqtt_disconnect_handler(mqtt_client, userdata, rc):
    print("Disconnected from MQTT broker.")


def __mqtt_publish_handler(mqtt_client, userdata, topic, pid):
    print("Published to {0} with PID {1}".format(topic, pid))


# Set the event handlers
mqtt_client.on_connect = __mqtt_connect_handler
mqtt_client.on_disconnect = __mqtt_disconnect_handler
mqtt_client.on_publish = __mqtt_publish_handler


# Connect to the MQTT broker
print(f"Trying to connect to MQTT broker - {mqtt_client.broker}")
mqtt_client.connect()


# Publish a message
def publish_message(message: str):
    mqtt_client.publish(mqtt_env["topic"], message)


def get_time():
    current_time = ntp.datetime  # Fetch current time once
    year, month, day, hour, mins, secs, weekday, yearday, tm_isdst = current_time
    return "{:02d}/{:02d}/{} {:02d}:{:02d}:{:02d}".format(
        day, month, year, hour, mins, secs
    )


# Start BLE scan for advertisements
def start_scan():
    for advertisement in ble.start_scan(ProvideServicesAdvertisement, Advertisement):
        addr_bytes = advertisement.address.address_bytes
        addr_str = "".join("{:02x}".format(b) for b in addr_bytes).lower()

        if addr_str in addresses_to_filter:
            current_time_str = get_time()
            print(addr_str, current_time_str, "RSSI:", advertisement.rssi)

            # Send the message to the MQTT broker
            message = json.dumps(
                {
                    "address": addr_str,
                    "time": current_time_str,
                    "rssi": advertisement.rssi,
                }
            )
            publish_message(message)

            ble.stop_scan()

    # ble.stop_scan()  # Ensure scanning is stopped before continuing
    print("Scan done.")


while True:
    try:
        start_scan()
    except OSError as e:
        ble.stop_scan()  # stop the scan before we try again
        print("Failed to scan: ", e)
        continue
    except Exception as e:
        print("Unexpected error:", e)
        ble.stop_scan()
        mqtt_client.disconnect()  # todo - only disconnect if we're stopping
        raise e
    time.sleep(2)  # sleep for 2 seconds before scanning again
