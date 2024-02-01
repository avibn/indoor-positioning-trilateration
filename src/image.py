import io
from PIL import Image
import struct

pixel_size = 32


# https://github.com/derkalle4/python3-idotmatrix-client
def __create_payloads(png_data):
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


def generate_image_payload(
    point_x: int, point_y: int, point_color: tuple = (255, 0, 0)
) -> Image:
    # todo:: take in an optional background image
    # Generate a 32x32 2D array of random RGB values
    image_data = [[(0, 0, 0) for _ in range(32)] for _ in range(32)]

    # make points beacon points white
    image_data[0][0] = (255, 255, 255)
    image_data[0][31] = (255, 255, 255)
    image_data[31][0] = (255, 255, 255)
    # make point 28, 20 red
    image_data[point_x][point_y] = point_color

    # Flatten the 2D array to 1D
    image_data = [pixel for row in image_data for pixel in row]

    # Create image
    img = Image.new("RGB", (32, 32))
    img.putdata(image_data)

    # Rotate image
    img = img.rotate(90)

    # Save the image as bytes
    png_buffer = io.BytesIO()
    img.save(png_buffer, format="PNG")
    png_buffer.seek(0)

    return __create_payloads(png_buffer.getvalue())


if __name__ == "__main__":
    print(generate_image_payload(27, 20))
