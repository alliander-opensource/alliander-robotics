#!/usr/bin/env python3

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import sys
import time
from enum import Enum
from typing import List, Optional

import rclpy
import requests
from rclpy.node import Node
from rclpy.publisher import Publisher
from rclpy.timer import Timer
from sensor_msgs.msg import CompressedImage

from alliander_seekthermal.mac_finder import MacAddressFinder


class ColorPalette(Enum):
    """Class representing different G300 color palettes.

    Attributes:
        WHITEHOT: cold is black, hot is white.
        BLACKHOT: cold is white, hot is black.
        SPECTRA: from blue, through green and yellow, to red.
        TYRIAN: from dark purple, through red, to white.
        IRON: from purple, through red, to white.
        AMBER: from black to lighter shades of yellow.
        HI: like white hot, but hottest areas are yellow, red, and black.
    """

    WHITEHOT = 0
    BLACKHOT = 1
    SPECTRA = 2
    TYRIAN = 4
    IRON = 5
    AMBER = 6
    HI = 7


class SeekThermalBridge(Node):
    """ROS2 node that bridges the Seek Thermal camera to a ROS topic.

    Members:
        ip_addr (str): IP address of the Seek Thermal camera.
        frame_id (str): ROS2 frame ID to publish on.
        publisher_ (Publisher): ROS2 publisher for compressed images.
        timer_ (Timer): ROS2 timer that triggers periodic image polling.
        session_ (requests.Session): HTTP session used for camera API calls.
        token_ (Optional[str]): Bearer token obtained after successful login.
    """

    def __init__(self):
        """Initialize the Seek Thermal camera bridge node."""
        super().__init__("camera_bridge")

        self.declare_parameter("username", "admin")
        username = self.get_parameter("username").get_parameter_value().string_value
        self.declare_parameter("password", "admin")
        password = self.get_parameter("password").get_parameter_value().string_value
        self.declare_parameter("poll_period", 0.25)
        poll_period = (
            self.get_parameter("poll_period").get_parameter_value().double_value
        )
        self.declare_parameter("frame_id", "link_optical")
        self.frame_id: str = (
            self.get_parameter("frame_id").get_parameter_value().string_value
        )
        self.declare_parameter("camera_mac", "ec:9a:0c:60")
        mac_addr = self.get_parameter("camera_mac").get_parameter_value().string_value

        self.declare_parameter("color_palette", "tyrian")
        palette = self.get_parameter("color_palette").get_parameter_value().string_value
        try:
            self.color_palette_ = ColorPalette[palette.upper()]
        except KeyError:
            self.get_logger().warn(
                f"Invalid color palette {palette}. Options are {[p.value for p in ColorPalette]}. Defaulting to {ColorPalette(4).name}."
            )
            self.color_palette = ColorPalette(4)

        self.publisher_: Publisher = self.create_publisher(
            CompressedImage, "/topic_out_image/compressed", 1
        )
        self.timer_: Timer = self.create_timer(poll_period, self.timer_callback)
        self.session_: requests.Session = requests.Session()
        self.token_: Optional[str] = None

        # look for OUI (Organizationally Unique Identifier) only
        mac_addr_finder = MacAddressFinder(self.get_logger(), mac_addr)
        self.ip_addr: Optional[str] = mac_addr_finder.find_ip()
        if self.ip_addr is None:
            self.get_logger().info(
                f"Unable to find IP address of Seek Thermal camera (OUI MAC {mac_addr}). Make sure device is connected and pingable. You may need to reset the camera by long-pressing the RESET pin. Exiting."
            )
            sys.exit(1)
        else:
            self.get_logger().info(f"Found camera with IP {self.ip_addr}.")

        self.get_logger().info("Started Seek Thermal camera bridge node.")

        self._await_login(username, password)

    def _await_login(self, username: str, password: str) -> None:
        """Block until a successful login is obtained.

        Args:
            username (str): Camera login username.
            password (str): Camera login password.
        """
        while self.token_ is None:
            self.login(username, password)
            time.sleep(0.5)

    def login(self, username: str, password: str) -> None:
        """Authenticate with the camera API and store the bearer token.

        Args:
            username (str): Camera login username.
            password (str): Camera login password.
        """
        resp = self.session_.post(
            f"http://{self.ip_addr}/session/login",
            json={"username": username, "password": password},
        ).json()
        if "token" in resp:
            self.get_logger().info("Logged in.")
            self.token_ = resp["token"]
        else:
            self.get_logger().info(f"Login did not succeed. Error: {resp['error']}")

    def get_image(self) -> bytes:
        """Fetch the current JPEG image from the camera.

        Returns:
            bytes: Raw JPEG image bytes from the camera.
        """
        resp = self.session_.get(
            f"http://{self.ip_addr}/image/palette/{self.color_palette_.value}",
            headers={"Authorization": f"Bearer {self.token_}", "Accept": "image/jpeg"},
        )
        resp.raise_for_status()
        return resp.content

    def convert_image(self, jpeg_bytes: bytes) -> CompressedImage:
        """Wrap raw JPEG bytes in a ROS2 CompressedImage message.

        Args:
            jpeg_bytes (bytes): Raw JPEG image bytes to wrap.

        Returns:
            CompressedImage: ROS2 message with a current timestamp and JPEG format.
        """
        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        msg.format = "jpeg"
        msg.data = jpeg_bytes

        if len(jpeg_bytes) > 0:
            self.get_logger().info(
                "Publishing current image. This log will appear only once.", once=True
            )

        return msg

    def timer_callback(self) -> None:
        """Poll the camera for a new image and publish it to the ROS topic."""
        image = self.get_image()
        image_ros = self.convert_image(image)
        self.publisher_.publish(image_ros)


def main(args: Optional[List[str]] = None) -> None:
    """Initialize and spin the SeekThermalBridge node.

    Args:
        args (Optional[List[str]]): Command-line arguments passed to rclpy.
    """
    rclpy.init(args=args)

    camera_bridge = SeekThermalBridge()
    rclpy.spin(camera_bridge)

    camera_bridge.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main(args=None)
