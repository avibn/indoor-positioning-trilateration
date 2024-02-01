# This will contain the MQTT client and the controller logic
import asyncio

from calc import get_position
from image import generate_image_payload
from libs.bluetooth import Bluetooth

if __name__ == "__main__":
    # Create a bluetooth connection
    bt = Bluetooth("00:00:00:00:00:00")

    # Get position (example)
    x, y = get_position((0, 0), (0, 10), (10, 0), -88, -86, -69)

    # Send image payload
    asyncio.run(bt.send(generate_image_payload(x, y)))

    # Disconnect from the bluetooth
    bt.disconnect()
