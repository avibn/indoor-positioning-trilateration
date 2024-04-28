import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

# Figure and axis for the plot
fig, ax = plt.subplots(figsize=(6, 6))


def __plot_trilateration(base_stations: list, target: tuple):
    """
    Plot the trilateration graph for indoor positioning.

    Parameters:
    - base_stations (list): A list of dictionaries representing the base stations. Each dictionary should have the following keys:
        - 'coords' (tuple): The coordinates of the base station in the form (x, y).
        - 'distance' (float): The distance from the base station to the target.
    - target (tuple): The estimated position of the target in the form (x, y).

    Returns:
    None
    """
    # Coordinates of the base stations
    base_points = np.array([list(base["coords"]) for base in base_stations])

    # Plot the base points
    plt.scatter(base_points[:, 0], base_points[:, 1], label="Base Stations")
    plt.scatter(target[0], target[1], label="Position Estimate", color="red")

    # Annotate the estimated position
    plt.annotate(
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
        # circle.set_facecolor("blue")
        circle.set_linewidth(1)
        circle.set_linestyle("--")
        circle.set_label(f"RSSI Distance {base['distance']:.1f}m")
        plt.gca().add_artist(circle)

        # Annotate the base station coordinates
        plt.annotate(
            f"({base['coords'][0]}, {base['coords'][1]})",
            (base["coords"][0], base["coords"][1]),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=8,
        )

        # Annotate the distance (radius of the circle)
        plt.annotate(
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
    plt.axhline(0, color="black", linewidth=1.5)
    plt.axvline(0, color="black", linewidth=1.5)

    # todo
    # Option 1 - shows the full circles too
    plt.xlim(min_x, max_x)
    plt.ylim(min_y, max_y)
    # Option 2 - zooms in to just the plots (base stations and target)
    # plt.tight_layout()

    plt.grid(True)
    # plt.legend()
    plt.title("Trilateration for Indoor Positioning")


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
        plt.clf()

        # Update the data if any
        if get_updated_data is not None:
            new_base_stations, new_target = get_updated_data()
            __plot_trilateration(new_base_stations, new_target)

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

    get_updated_data = lambda: (
        base_stations,
        (np.random.randint(0, 20), np.random.randint(0, 20)),
    )

    # Animation
    animate(base_stations, initial_target, get_updated_data)

    # No animation:
    # __plot_trilateration(base_stations, initial_target)
    # plt.show()
