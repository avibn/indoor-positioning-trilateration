import numpy as np
from filterpy.kalman import KalmanFilter

UNCERTAINTY = 17


def initialize_kalman_filter():
    # Initialize the Kalman Filter
    kf = KalmanFilter(dim_x=1, dim_z=1)
    kf.x = np.array([0.0])  # initial state
    kf.F = np.array([[1.0]])  # state transition matrix
    kf.H = np.array([[1.0]])  # Measurement function
    kf.P *= 1000.0  # covariance matrix
    kf.R = UNCERTAINTY  # state uncertainty
    return kf


def apply_kalman_filter(kf, new_value):
    # Use the Kalman Filter for the new value
    kf.predict()
    kf.update(np.array([new_value]))
    return kf.x  # This is the filtered value
