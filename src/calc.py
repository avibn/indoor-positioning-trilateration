def __rssi_to_distance(rssi, measured_power=-69, path_loss_exponent=1.8):
    """
    Converts RSSI (Received Signal Strength Indicator) to distance using the path loss model.

    Parameters:
        rssi (float): The RSSI value in dBm.
        measured_power (float, optional): The rssi value measured at 1 meter from the beacon. Default is -69.
        path_loss_exponent (float, optional): The path loss exponent. Default is 2. Should be in the range 2-4.

    Returns:
        float: The estimated distance in meters.
    """
    return 10 ** ((measured_power - rssi) / (10 * path_loss_exponent))


def __trilaterate(x1, y1, d1, x2, y2, d2, x3, y3, d3):
    """
    Trilaterates the position (X, Y) given the coordinates and distances of three points.

    Args:
        x1 (float): x-coordinate of the first point.
        y1 (float): y-coordinate of the first point.
        d1 (float): distance from the first point to the unknown position.
        x2 (float): x-coordinate of the second point.
        y2 (float): y-coordinate of the second point.
        d2 (float): distance from the second point to the unknown position.
        x3 (float): x-coordinate of the third point.
        y3 (float): y-coordinate of the third point.
        d3 (float): distance from the third point to the unknown position.

    Returns:
        tuple: The (X, Y) coordinates of the unknown position.
    """
    # Formula:
    # (x - x1)^2 + (y - y1)^2 = d1^2
    # (x - x2)^2 + (y - y2)^2 = d2^2
    # (x - x3)^2 + (y - y3)^2 = d3^2
    A = 2 * (x2 - x1)
    B = 2 * (y2 - y1)
    C = d1**2 - d2**2 - x1**2 + x2**2 - y1**2 + y2**2
    D = 2 * (x3 - x2)
    E = 2 * (y3 - y2)
    F = d2**2 - d3**2 - x2**2 + x3**2 - y2**2 + y3**2

    X = (C * E - F * B) / (E * A - B * D)
    Y = (C * D - A * F) / (B * D - A * E)

    return X, Y


def __scale_coordinates(x, y, initial_x=10, initial_y=10, max_value=32):
    """
    Scale the given coordinates to fit within the specified max_value.

    Parameters:
    x (float): The x-coordinate to be scaled.
    y (float): The y-coordinate to be scaled.
    initial_x (float): The initial upper bound for the x-coordinate. Default is 10.
    initial_y (float): The initial upper bound for the y-coordinate. Default is 10.
    max_value (int): The maximum value for the scaled coordinates. Default is 32.

    Returns:
    tuple: A tuple containing the scaled x and y coordinates.
    """
    scaled_x = int((x / initial_x) * max_value)  # todo:: CHANGE 10 to whatever
    scaled_y = int((y / initial_y) * max_value)

    scaled_x = max(0, min(scaled_x, max_value - 1))
    scaled_y = max(0, min(scaled_y, max_value - 1))

    return scaled_x, scaled_y


def get_position(
    bp_1: tuple, bp_2: tuple, bp_3: tuple, rssi_1: float, rssi_2: float, rssi_3: float
) -> tuple:
    """
    Calculates the estimated position based on the received signal strength indicator (RSSI) values
    and the known positions of three base stations.

    Args:
        bp_1 (tuple): The coordinates (x, y) of base station 1.
        bp_2 (tuple): The coordinates (x, y) of base station 2.
        bp_3 (tuple): The coordinates (x, y) of base station 3.
        rssi_1 (float): The RSSI value received from base station 1.
        rssi_2 (float): The RSSI value received from base station 2.
        rssi_3 (float): The RSSI value received from base station 3.

    Returns:
        tuple: The estimated position (x, y) scaled to fit within a 32x32 grid.
    """
    # Calculate distances
    d1 = __rssi_to_distance(rssi_1)
    d2 = __rssi_to_distance(rssi_2)
    d3 = __rssi_to_distance(rssi_3)

    print(f"Distances: {d1}, {d2}, {d3}")

    # Trilateration
    estimated_x, estimated_y = __trilaterate(
        bp_1[0],
        bp_1[1],
        d1,
        bp_2[0],
        bp_2[1],
        d2,
        bp_3[0],
        bp_3[1],
        d3,
    )
    print(f"Actual Position:    ({estimated_x}, {estimated_y})")

    # Get the maximum x and y coordinates to scale the estimated position
    max_x = max(bp_1[0], bp_2[0], bp_3[0])
    max_y = max(bp_1[1], bp_2[1], bp_3[1])

    # Scale the coordinates to fit within a 32x32 grid
    scaled_x, scaled_y = __scale_coordinates(estimated_x, estimated_y, max_x, max_y)

    # Logging
    print(f"Estimated Position: ({scaled_x}, {scaled_y}) in a 32x32 grid")
    return scaled_x, scaled_y


if __name__ == "__main__":
    # # RSSI values
    rssi_1 = -54
    rssi_2 = -69
    rssi_3 = -76

    # # Get estimated position
    # x, y = get_position((0, 10), (10, 0), (10, 10), rssi_1, rssi_2, rssi_3)
    x, y = get_position((0, 2.2), (3.2, 0), (3.2, 3.1), rssi_1, rssi_2, rssi_3)

    # rssi = -62
    # d = __rssi_to_distance(rssi)
    # print(d)

    # for i in range(-32, -82, -1):
    #     print(f"{i}: {__rssi_to_distance(i)}")
