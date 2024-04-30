import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

# Trilateration Graph
TRILATERATION_ZOOMED_IN = False
TRILATERATION_LEGEND = False

# RSSI Graph
RSSI_GRAPH_SHOW = True
RSSI_FIXED_Y_AXIS = False

if RSSI_GRAPH_SHOW:
    fig = plt.figure(figsize=(10, 6))

    gs = gridspec.GridSpec(3, 2)

    trilateration_graph = plt.subplot(gs[:, 0])
    rssi_graph1 = plt.subplot(gs[0, 1])
    rssi_graph2 = plt.subplot(gs[1, 1])
    rssi_graph3 = plt.subplot(gs[2, 1])
else:
    fig, trilateration_graph = plt.subplots(figsize=(6, 6))


# Square aspect ratio
trilateration_graph.set_aspect("equal", adjustable="box")


# Close event
def set_on_close(func):
    fig.canvas.mpl_connect("close_event", func)


def __plot_trilateration(
    base_stations: list,
    target: tuple,
    rssi_data_1: list = None,
    rssi_data_2: list = None,
    rssi_data_3: list = None,
):
    """
    Plot the trilateration graph for indoor positioning.

    Parameters:
    - base_stations (list): A list of dictionaries representing the base stations. Each dictionary should have the following keys:
        - 'coords' (tuple): The coordinates of the base station in the form (x, y).
        - 'distance' (float): The distance from the base station to the target.
    - target (tuple): The estimated position of the target in the form (x, y).
    - rssi_data_1 (list, optional): A list of dictionaries representing the RSSI data for the first beacon. Each dictionary should have the following
    - rssi_data_2 (list, optional): A list of dictionaries representing the RSSI data for the second beacon. Each dictionary should have the following
    - rssi_data_3 (list, optional): A list of dictionaries representing the RSSI data for the third beacon. Each dictionary should have the following
        - 'time' (str): The timestamp of the reading.
        - 'address' (str): The address of the beacon.
        - 'rssi' (int): The raw RSSI value.
        - 'filtered_rssi' (list): A list of filtered RSSI values.

    Returns:
    None
    """
    # -------------------- Trilateration Graph -------------------- #
    # Coordinates of the base stations
    base_points = np.array([list(base["coords"]) for base in base_stations])

    # Plot the base points
    trilateration_graph.scatter(
        base_points[:, 0], base_points[:, 1], label="Base Stations"
    )
    trilateration_graph.scatter(
        target[0], target[1], label="Position Estimate", color="red"
    )

    # Annotate the estimated position
    trilateration_graph.annotate(
        f"({target[0]:.1f}, {target[1]:.1f})",
        (target[0], target[1]),
        textcoords="offset points",
        xytext=(0, 10),
        ha="center",
        fontsize=8,
    )

    # Colours for the circles for the rssi distance circls
    colours = [
        "red",
        "green",
        "purple",
        "orange",
        "brown",
        "pink",
        "gray",
        "olive",
        "cyan",
    ]

    # Plot the circles (rssi distances)
    for i, base in enumerate(base_stations):
        circle = plt.Circle(
            base["coords"], base["distance"], fill=True, alpha=0.06, color=colours[i]
        )
        circle.set_edgecolor("black")
        circle.set_linewidth(1)
        circle.set_linestyle("--")
        circle.set_label(f"RSSI Distance {base['distance']:.1f}m")
        trilateration_graph.add_artist(circle)
        # trilateration_graph.add_patch(circle)

        # Annotate the base station coordinates
        trilateration_graph.annotate(
            f"({base['coords'][0]}, {base['coords'][1]})",
            (base["coords"][0], base["coords"][1]),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=8,
        )

        # Annotate the distance (radius of the circle)
        trilateration_graph.annotate(
            f"{base['distance']:.1f}m",
            (base["coords"][0], base["coords"][1]),
            textcoords="offset points",
            xytext=(0, -15),
            ha="center",
            fontsize=8,
        )

    # Calculate the min and max x and y for the circles
    min_x = min(base["coords"][0] - base["distance"] for base in base_stations) - 1
    max_x = max(base["coords"][0] + base["distance"] for base in base_stations) + 1
    min_y = min(base["coords"][1] - base["distance"] for base in base_stations) - 1
    max_y = max(base["coords"][1] + base["distance"] for base in base_stations) + 1

    # Draw x and y axis
    trilateration_graph.axhline(0, color="black", linewidth=1.5)
    trilateration_graph.axvline(0, color="black", linewidth=1.5)

    if not TRILATERATION_ZOOMED_IN:
        trilateration_graph.axis(xmin=min_x, xmax=max_x, ymin=min_y, ymax=max_y)
    if TRILATERATION_LEGEND:
        trilateration_graph.legend(loc="upper left")

    trilateration_graph.grid(True)
    trilateration_graph.set_title("Trilateration for Indoor Positioning")

    # ------------------------- RSSI Graph ------------------------ #
    if not RSSI_GRAPH_SHOW:
        return

    if not rssi_data_1 or not rssi_data_2 or not rssi_data_3:
        return

    # Group the rssi data by address
    beacons = {
        "beacon_1": rssi_data_1,
        "beacon_2": rssi_data_2,
        "beacon_3": rssi_data_3,
    }

    for i, (address, data) in enumerate(beacons.items()):
        graph = {0: rssi_graph1, 1: rssi_graph2, 2: rssi_graph3}[i]

        # Get arrays for rssi and filtered rssi
        y1 = np.array([reading["rssi"] for reading in data])
        y2 = np.array([reading["filtered_rssi"] for reading in data])

        # Plot the data
        graph.plot(y1, label=f"RSSI", color=colours[0], linestyle="-")
        graph.plot(y2, label=f"Filtered RSSI", color=colours[1], linestyle="--")

    if RSSI_FIXED_Y_AXIS:
        rssi_graph1.set_ylim(-80, -20)

    # Set the labels and title
    rssi_graph1.set_title("RSSI from Beacons")
    rssi_graph3.set_xlabel("Time")
    rssi_graph2.set_ylabel("RSSI (dBm)")
    rssi_graph1.grid(True)
    rssi_graph2.grid(True)
    rssi_graph3.grid(True)
    rssi_graph1.legend(loc="upper left")


def animate(
    base_stations: list,
    target: tuple,
    get_updated_data: callable = None,
    interval: int = 1000,
):
    """
    Animates the trilateration graph for indoor positioning.

    Parameters:
    - base_stations (list): A list of dictionaries representing the base stations. Each dictionary should have the following keys: 'coords' (tuple), 'distance' (float).
    - target (tuple): The target coordinates.
    - get_updated_data (callable, optional): A function that returns updated base stations and target coordinates.
    - interval (int, optional): The interval in milliseconds between each update.

    Returns:
    - FuncAnimation: The animation object. (call plt.show() to display the animation)
    """
    # Initial plot
    __plot_trilateration(base_stations, target)

    # Update function for the animation called every `interval`` milliseconds
    def update(i):
        # Clear current plt
        trilateration_graph.clear()
        if RSSI_GRAPH_SHOW:
            rssi_graph1.clear()
            rssi_graph2.clear()
            rssi_graph3.clear()

        # Update the data if any
        if get_updated_data is not None:
            # Get the data from the function supplied
            (
                new_base_stations,
                new_target,
                new_rssi_data_1,
                new_rssi_data_2,
                new_rssi_data_3,
            ) = get_updated_data()

            # Plot the updated data
            __plot_trilateration(
                new_base_stations,
                new_target,
                new_rssi_data_1,
                new_rssi_data_2,
                new_rssi_data_3,
            )

    # Animate the plot with the update function
    animation = FuncAnimation(fig, update, interval=interval, cache_frame_data=False)
    plt.show()


if __name__ == "__main__":
    base_stations = [
        {"coords": (0, 2.2), "distance": 0.14677992676220694},
        {"coords": (3.2, 0), "distance": 1.0},
        {"coords": (3.2, 3.1), "distance": 2.4484367468222272},
    ]

    initial_target = (1.5, 1.5)

    from collections import deque

    rssi_data_1 = deque(maxlen=10)
    rssi_data_2 = deque(maxlen=10)
    rssi_data_3 = deque(maxlen=10)

    # Test data
    rssi_data_1.append(
        {
            "time": "2021-08-01 12:00:00",
            "address": "address_1",
            "rssi": -50,
            "filtered_rssi": [-50],
        }
    )
    rssi_data_2.append(
        {
            "time": "2021-08-01 12:00:00",
            "address": "address_2",
            "rssi": -60,
            "filtered_rssi": [-60],
        }
    )
    rssi_data_3.append(
        {
            "time": "2021-08-01 12:00:00",
            "address": "address_3",
            "rssi": -70,
            "filtered_rssi": [-70],
        }
    )

    def get_updated_data():
        rssi_data_1.append(
            {
                "time": "2021-08-01 12:00:00",
                "address": "address_1",
                "rssi": np.random.randint(-70, -30),
                "filtered_rssi": [np.random.randint(-70, -30)],
            }
        )
        return (
            base_stations,
            (np.random.randint(0, 3.2), np.random.randint(0, 3.2)),
            list(rssi_data_1),
            list(rssi_data_2),
            list(rssi_data_3),
        )

    # Animation
    animate(base_stations, initial_target, get_updated_data)

    # No animation:
    # __plot_trilateration(base_stations, initial_target)
    # plt.show()
