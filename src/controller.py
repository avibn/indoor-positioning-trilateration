# This will contain the MQTT client and the controller logic
import asyncio
from typing import List, Tuple

from bleak import BleakScanner

from calc import get_position
from image import generate_image_payload
from libs.bluetooth import Bluetooth


class Controller:
    def __init__(self, address: str = "DC:03:BB:B0:67:4A"):
        """
        Initializes the Controller object.

        Args:
            address (str): The Bluetooth address to connect to. Defaults to "DC:03:BB:B0:67:4A".

        Raises:
            Exception: If there is an error connecting to the Bluetooth device.
        """

        self.__background = [[(0, 0, 0) for _ in range(32)] for _ in range(32)]
        self.__beacons = [(0, 0), (0, 31), (31, 0)]
        self.__started = False
        try:
            self.__bt = Bluetooth(address)
        except Exception as e:
            print(f"Could not connect to bluetooth: {e}")
            raise e

    async def discover(self):
        """
        Discovers nearby devices using BleakScanner and prints them. (TODO: Remove this method in the future.)
        """

        devices = await BleakScanner.discover()
        for d in devices:
            print(d)

    async def __image_mode_on(self):
        """
        Sends a byte array to enable image mode.

        Raises:
            Any exceptions that occur during the sending process.
        """

        await self.__bt.send(
            bytearray(
                [
                    5,
                    0,
                    4,
                    1,
                    int(1) % 256,
                ]
            )
        )

    async def plot(self, x: int, y: int):
        """
        Plot the position (x, y) on the image.

        Parameters:
        - x (int): The x-coordinate of the position.
        - y (int): The y-coordinate of the position.

        Returns:
        None
        """

        # Ensure image mode is on
        if not self.__started:
            await self.__image_mode_on()
            self.__started = True

        # Send image payload
        await self.__bt.send(
            generate_image_payload((x, y), self.__beacons, background=self.__background)
        )

        print(f"Finished plotting position {x}, {y}")

    async def disconnect(self):
        """
        Disconnects from the Bluetooth device.
        """
        await self.__bt.disconnect()

    def set_background(self, background: List[List[Tuple[int, int, int]]]):
        """
        Set the background of the controller.

        Args:
            background (List[List[Tuple[int, int, int]]]): A 2D list of tuples representing the RGB values of each pixel.

        Returns:
            None
        """
        self.__background = background

    def set_beacons(self, beacons: List[Tuple[int, int]]):
        """
        Set the list of beacons.

        Args:
            beacons (List[Tuple[int, int]]): A list of tuples representing the coordinates of the beacons.

        Returns:
            None
        """
        self.__beacons = beacons


if __name__ == "__main__":
    bt = Controller("DC:03:BB:B0:67:4A")
    # bt.set_beacons([(0, 0), (0, 10), (10, 0)])

    # Set the background to look like a room with a bed and table
    background = [
        [(200, 200, 200) if i in [0, 31] or j in [0, 31] else (150, 75, 0) if 10 <= i <= 14 and 10 <= j <= 14 else (139, 69, 19) if 20 <= i <= 22 and 20 <= j <= 22 else (255, 255, 255) for j in range(32)] for i in range(32)  # fmt: skip
    ]
    bt.set_background(background)

    # Get position (example)
    x, y = get_position((0, 0), (0, 10), (10, 0), -88, -86, -69)

    async def plot_position(x, y):
        for i in range(20):
            # testing
            y = i + 3

            # Plot the position
            print(f"Plotting position {x}, {y}")
            await bt.plot(x, y)

            # await asyncio.sleep(2)

        await bt.disconnect()

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(plot_position(x, y))
