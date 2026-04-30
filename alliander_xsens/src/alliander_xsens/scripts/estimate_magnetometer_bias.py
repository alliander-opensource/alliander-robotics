#!/usr/bin/env python3

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
"""Estimate magnetometer hard-iron bias from live ROS 2 data or a CSV file.

Usage (live):
    uv run estimate_magnetometer_bias.py

Usage (from CSV):
    uv run estimate_magnetometer_bias.py /path/to/data.csv

Bias is estimated as the midpoint of the measurement range on each axis,
which approximates the hard-iron offset under the assumption that the sensor
was rotated through all orientations during the calibration sweep.
"""

import sys
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import MagneticField

try:
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ModuleNotFoundError:
    print("matplotlib not found. Data will not be plotted.")
    HAS_MATPLOTLIB = False

MAG_TOPIC = "/xsens/imu/mag"
MAG_TIMEOUT = 2.0  # seconds of silence before bias is estimated


class MagneticBiasEstimator(Node):
    """ROS 2 node that estimates the hard-iron magnetometer bias.

    Subscribes to magnetometer messages and accumulates samples. Once the
    stream has been silent for `MAG_TIMEOUT` seconds the node computes the
    midpoint bias and optionally renders a 3-D scatter plot of the collected
    measurements.

    """

    def __init__(self, csv_file: str = "") -> None:
        """Initialize the MagneticBiasEstimator.

        Args:
            csv_file (str): Optional path to a CSV file with pre-recorded measurements.
                When provided the node estimates the bias immediately from the file
                rather than waiting for live messages.
        """
        super().__init__("magnetic_bias_estimator")
        self.sub_mag = self.create_subscription(
            MagneticField, MAG_TOPIC, self.mag_callback, 1
        )
        self.timer = self.create_timer(MAG_TIMEOUT, self.on_timer)
        self.stamp_mag_received = 0.0
        self.num_mag_received = 0

        self.mag_x: list[float] = []
        self.mag_y: list[float] = []
        self.mag_z: list[float] = []
        self.magnetic_bias: tuple[float, float, float] = (0.0, 0.0, 0.0)

        if csv_file:
            self.parse_csv(csv_file)

    def mag_callback(self, msg: MagneticField) -> None:
        """Append an incoming magnetometer sample to the internal buffers."""
        self.get_logger().info("Received magnetic field message.", once=True)
        self.num_mag_received += 1
        self.stamp_mag_received = time.time()
        self.mag_x.append(msg.magnetic_field.x)
        self.mag_y.append(msg.magnetic_field.y)
        self.mag_z.append(msg.magnetic_field.z)

    def on_timer(self) -> None:
        """Trigger bias estimation once the magnetometer stream goes silent."""
        if self.num_mag_received == 0:
            self.get_logger().info("Waiting for imu/mag messages")
            return
        if time.time() - self.stamp_mag_received > MAG_TIMEOUT:
            self.estimate_bias()
            self.plot()
            self.num_mag_received = 0

    def estimate_bias(self) -> None:
        """Estimate the hard-iron bias as the midpoint of each axis' range.

        Updates `self.magnetic_bias` with the ``(x, y, z)`` midpoints and
        logs the result together with the sample count.
        """
        mx = (max(self.mag_x) + min(self.mag_x)) / 2
        my = (max(self.mag_y) + min(self.mag_y)) / 2
        mz = (max(self.mag_z) + min(self.mag_z)) / 2
        self.get_logger().info(
            f"Bias estimation with {self.num_mag_received} samples: "
            f"mx={mx:.6f}, my={my:.6f}, mz={mz:.6f}"
        )
        self.magnetic_bias = (mx, my, mz)

    def plot(self) -> None:
        """Show a 3-D scatter plot of all collected samples and the estimated bias.

        Does nothing when matplotlib is not installed.
        """
        if not HAS_MATPLOTLIB:
            return

        ax = plt.figure().add_subplot(projection="3d")
        ax.scatter(self.mag_x, self.mag_y, self.mag_z, label="samples")
        ax.scatter(*self.magnetic_bias, color="#ff0000", marker="X", label="bias")
        ax.set_xlabel("mag_x")
        ax.set_ylabel("mag_y")
        ax.set_zlabel("mag_z")
        ax.set_title(f"Magnetic field measurements (n={self.num_mag_received})")
        ax.legend()
        ax.grid(True)

        plt.tight_layout()
        plt.show()

    def parse_csv(self, csv_file: str) -> None:
        """Load pre-recorded magnetometer data from a CSV file and estimate bias.

        The CSV must contain at least three columns (mag_x, mag_y, mag_z) with
        a single header row that is skipped during loading.

        Args:
            csv_file: Path to the comma-separated data file.
        """
        import numpy as np  # noqa: PLC0415

        data = np.loadtxt(csv_file, delimiter=",", skiprows=1)
        self.mag_x, self.mag_y, self.mag_z = (
            data[:, 0].tolist(),
            data[:, 1].tolist(),
            data[:, 2].tolist(),
        )
        self.num_mag_received = len(self.mag_x)

        self.estimate_bias()
        self.plot()


if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else ""

    rclpy.init(args=None)
    node = MagneticBiasEstimator(csv_file)
    rclpy.spin(node)

    rclpy.shutdown()
