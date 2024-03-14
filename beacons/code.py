import time
from adafruit_ble import BLERadio
from adafruit_ble.advertising import Advertisement
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement

# List of addresses to filter
addresses_to_filter = {"92c850cceee8"}

ble = BLERadio()

counter = 0

for advertisement in ble.start_scan(ProvideServicesAdvertisement, Advertisement):
    addr_bytes = advertisement.address.address_bytes
    addr_str = "".join("{:02x}".format(b) for b in addr_bytes).lower()

    if addr_str in addresses_to_filter:
        if counter % 4 == 0:
            print("RSSI:", advertisement.rssi)
            print("\tAddress:", addr_str)
        counter += 1

ble.stop_scan()  # Ensure scanning is stopped before continuing
print("Scan done.")
