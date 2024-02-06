import copy
import io
import struct
from typing import List, Tuple

from PIL import Image

pixel_size = 32


# https://github.com/derkalle4/python3-idotmatrix-client
def __create_bt_payloads(png_data):
    """Creates payloads from a PNG file.

    Args:
        png_data (bytearray): data of the png file

    Returns:
        bytearray: returns bytearray payload
    """
    # Split the PNG data into 4096-byte chunks
    chunk_size = 4096
    png_chunks = [
        png_data[i : i + chunk_size] for i in range(0, len(png_data), chunk_size)
    ]

    # Calculate the arbitrary metadata number
    idk = len(png_data) + len(png_chunks)
    idk_bytes = struct.pack("h", idk)  # convert to 16bit signed int
    png_len_bytes = struct.pack("i", len(png_data))

    # build data
    payloads = bytearray()
    for i, chunk in enumerate(png_chunks):
        payload = (
            idk_bytes
            + bytearray(
                [
                    0,
                    0,
                    2 if i > 0 else 0,
                ]
            )
            + png_len_bytes
            + chunk
        )
        payloads.extend(payload)
    return payloads


def __create_img_buffer(
    image_data: List[List[Tuple[int, int, int]]], rotate: int = 1, size: int = 32
) -> io.BytesIO:
    """
    Create an image buffer from the given image data.

    Args:
        image_data (List[List[Tuple[int, int, int]]]): The pixel data of the image.
        rotate (int, optional): The number of 90-degree rotations to apply to the image. Defaults to 1.
        size (int, optional): The size of the image. Defaults to 32.

    Returns:
        io.BytesIO: The image buffer as a BytesIO object.
    """

    # Create image
    img = Image.new("RGB", (size, size))
    img.putdata(image_data)

    # Rotate image
    img = img.rotate(90 * rotate)

    # Save the image as bytes
    png_buffer = io.BytesIO()
    img.save(png_buffer, format="PNG")
    png_buffer.seek(0)

    return png_buffer


def generate_image_payload(
    object_coords: Tuple[int, int],
    beacon_coords: List[Tuple[int, int]] = [],
    object_color: tuple = (255, 0, 0),
    beacon_color: tuple = (0, 255, 0),
    background: List[List[Tuple[int, int, int]]] = None,
) -> Image:
    """
    Generate an image payload with specified object coordinates, beacon coordinates, point color, and background.

    Parameters:
        object_coords (Tuple[int, int]): The coordinates of the object point in the image.
        beacon_coords (List[Tuple[int, int]], optional): The coordinates of the beacon points in the image. Defaults to an empty list.
        object_color (tuple, optional): The color of the object point. Defaults to (255, 0, 0) (red).
        beacon_color (tuple, optional): The color of the beacon points. Defaults to (0, 255, 0) (green).
        background (List[List[Tuple[int, int, int]]], optional): The background image data represented as a 2D array of RGB values. Defaults to black screen.

    Returns:
        Image: The generated image payload.

    """

    # Generate default 32x32 2D array of RGB values
    if not background:
        image_data = [[(0, 0, 0) for _ in range(32)] for _ in range(32)]
    else:
        image_data = copy.deepcopy(background)

    # Make points beacon points white
    for point in beacon_coords:
        beacon_x, beacon_y = point
        image_data[beacon_x][beacon_y] = beacon_color

    # Set the object point to the specified color
    point_x, point_y = object_coords
    image_data[point_x][point_y] = object_color

    # Flatten the 2D array to 1D
    image_data = [pixel for row in image_data for pixel in row]

    # Create image buffer
    png_buffer = __create_img_buffer(image_data)
    return __create_bt_payloads(png_buffer.getvalue())


if __name__ == "__main__":
    print(generate_image_payload((27, 20), [(0, 0), (0, 10), (10, 0)]))
