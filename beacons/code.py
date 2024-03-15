import adafruit_ntp
import socketpool
import time
import wifi
from adafruit_ble import BLERadio
from adafruit_ble.advertising import Advertisement
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

wifi.radio.connect(secrets["ssid"], secrets["password"])

pool = socketpool.SocketPool(wifi.radio)
ntp = adafruit_ntp.NTP(pool, tz_offset=0)

ble = BLERadio()
counter = 0

# List of addresses to filter
addresses_to_filter = {"92c850cceee8"}


def start_scan():
    for advertisement in ble.start_scan(ProvideServicesAdvertisement, Advertisement):
        addr_bytes = advertisement.address.address_bytes
        addr_str = "".join("{:02x}".format(b) for b in addr_bytes).lower()

        if addr_str in addresses_to_filter:
            current_time = ntp.datetime  # Fetch current time once
            year, month, day, hour, mins, secs, weekday, yearday, tm_isdst = (
                current_time
            )
            current_time_str = "{:02d}/{:02d}/{} {:02d}:{:02d}:{:02d}".format(
                day, month, year, hour, mins, secs
            )
            print(addr_str, current_time_str, "RSSI:", advertisement.rssi)
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
    time.sleep(2)
