from scipy.optimize import least_squares


class TrilaterationController:
    def __init__(
        self,
        bp_1: tuple,
        bp_2: tuple,
        bp_3: tuple,
        scale=32,
        measured_power_1=-69,
        measured_power_2=-69,
        measured_power_3=-69,
        path_loss_exponent=1.8,
    ):
        """
        Initialize the trilateration controller.

        Args:
            bp_1 (tuple): Position of base station 1.
            bp_2 (tuple): Position of base station 2.
            bp_3 (tuple): Position of base station 3.
            scale (int, optional): Grid scale. Defaults to 32.
            measured_power_1 (int, optional): Measured power at base station 1. Defaults to -69.
            measured_power_2 (int, optional): Measured power at base station 2. Defaults to -69.
            measured_power_3 (int, optional): Measured power at base station 3. Defaults to -69.
            path_loss_exponent (float, optional): Path loss exponent. Defaults to 1.8.
        """
        # Base station positions
        self.bp_1 = bp_1
        self.bp_2 = bp_2
        self.bp_3 = bp_3

        # Grid scale
        self.scale = scale

        # Measured power and path loss exponent
        self.measured_power_1 = measured_power_1
        self.measured_power_2 = measured_power_2
        self.measured_power_3 = measured_power_3
        self.path_loss_exponent = path_loss_exponent

    def get_position(self, rssi_1: float, rssi_2: float, rssi_3: float) -> tuple:
        """
        Calculates the estimated position based on the received signal strength indicator (RSSI) values
        and the known positions of three base stations.

        Args:
            rssi_1 (float): The RSSI value received from base station 1.
            rssi_2 (float): The RSSI value received from base station 2.
            rssi_3 (float): The RSSI value received from base station 3.

        Returns:
            tuple: The estimated position (x, y) scaled to fit within a 32x32 grid.
        """
        # Calculate distances
        d1 = self.get_distance(rssi_1, 1)
        d2 = self.get_distance(rssi_2, 2)
        d3 = self.get_distance(rssi_3, 3)

        # Trilateration
        estimated_x, estimated_y = self.trilaterate(d1, d2, d3)

        # Scale the coordinates to fit within a 32x32 grid
        scaled_x, scaled_y = self.__scale_coordinates(estimated_x, estimated_y)

        return scaled_x, scaled_y

    def trilaterate(self, d1: float, d2: float, d3: float) -> tuple:
        """
        Trilaterates the position (X, Y) given the distances of three points.

        Args:
            d1 (float): distance from the first point to the unknown position.
            d2 (float): distance from the second point to the unknown position.
            d3 (float): distance from the third point to the unknown position.

        Returns:
            tuple: The (X, Y) coordinates of the unknown position.
        """
        x1, y1 = self.bp_1
        x2, y2 = self.bp_2
        x3, y3 = self.bp_3

        # Formula:
        # (x - x1)^2 + (y - y1)^2 = d1^2
        # (x - x2)^2 + (y - y2)^2 = d2^2
        # (x - x3)^2 + (y - y3)^2 = d3^2
        def equations(guess):
            x, y, r = guess

            return (
                (x - x1) ** 2 + (y - y1) ** 2 - (d1 - r) ** 2,
                (x - x2) ** 2 + (y - y2) ** 2 - (d2 - r) ** 2,
                (x - x3) ** 2 + (y - y3) ** 2 - (d3 - r) ** 2,
            )

        # Initial guess
        initial_guess = (0, 0, 0)

        # Use least squares to solve the equations
        results = least_squares(equations, initial_guess)

        # Return the estimated coordinates
        coordinates = results.x
        return coordinates[0], coordinates[1]

    def get_distance(self, rssi: float, node: int) -> float:
        """
        Converts RSSI (Received Signal Strength Indicator) to distance using the path loss model.

        Parameters:
        - rssi (float): The received signal strength indicator in dBm.
        - node (int): The node number (1, 2, or 3) corresponding to the base station.

        Returns:
        - distance (float): The calculated distance between the devices in meters.
        """
        if node == 1:
            measured_power = self.measured_power_1
        elif node == 2:
            measured_power = self.measured_power_2
        elif node == 3:
            measured_power = self.measured_power_3
        else:
            raise ValueError("Invalid node number")

        return 10 ** ((measured_power - rssi) / (10 * self.path_loss_exponent))

    def __scale_coordinates(self, x: float, y: float) -> tuple:
        """
        Scale the given coordinates to fit within the specified max_value.

        Parameters:
        x (float): The x-coordinate to be scaled.
        y (float): The y-coordinate to be scaled.

        Returns:
        tuple: A tuple containing the scaled x and y coordinates.
        """
        # Maximum x and y values from the base stations
        initial_x = max(self.bp_1[0], self.bp_2[0], self.bp_3[0])
        initial_y = max(self.bp_1[1], self.bp_2[1], self.bp_3[1])

        # Scale the coordinates
        scaled_x = int((x / initial_x) * self.scale)
        scaled_y = int((y / initial_y) * self.scale)

        # Ensure the scaled coordinates are within the grid
        scaled_x = max(0, min(scaled_x, self.scale - 1))
        scaled_y = max(0, min(scaled_y, self.scale - 1))

        return scaled_x, scaled_y

    def __str__(self):
        return f"TrilaterationController(bp_1={self.bp_1}, bp_2={self.bp_2}, bp_3={self.bp_3})"

    def __repr__(self):
        return self.__str__()


if __name__ == "__main__":
    val = "-47 | -42 | -42"
    # val = "-42 | -42 | -42"
    # val = "-28 | -62 | -45"
    val_str = list(map(float, val.split(" | ")))

    # Test data
    receiver_1_pos = (0, 2.2)
    rssi_1 = val_str[0]

    receiver_2_pos = (3.2, 0)
    rssi_2 = val_str[1]

    receiver_3_pos = (3.2, 3.1)
    rssi_3 = val_str[2]

    # Test TrilaterationController
    position_estimator = TrilaterationController(
        receiver_1_pos,
        receiver_2_pos,
        receiver_3_pos,
        measured_power_1=-40,
        measured_power_2=-40,
        measured_power_3=-40,
        path_loss_exponent=1.8,
    )
    position = position_estimator.get_position(rssi_1, rssi_2, rssi_3)

    d1 = position_estimator.get_distance(rssi_1, 1)
    d2 = position_estimator.get_distance(rssi_2, 2)
    d3 = position_estimator.get_distance(rssi_3, 3)
    position2 = position_estimator.trilaterate(d1, d2, d3)

    # Distances
    print(f"Distance from receiver 1: {position_estimator.get_distance(rssi_1, 1)}")
    print(f"Distance from receiver 2: {position_estimator.get_distance(rssi_2, 2)}")
    print(f"Distance from receiver 3: {position_estimator.get_distance(rssi_3, 3)}")
    print()

    print(f"Estimated position: {position}")
    print(f"Scaled position:    {position2}")
