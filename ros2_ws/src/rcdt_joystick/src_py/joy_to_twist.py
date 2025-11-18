#!/usr/bin/env python3

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import rclpy
from geometry_msgs.msg import Twist, TwistStamped
from rcdt_utilities.ros_utils import get_file_path, get_yaml, spin_node
from rclpy import logging
from rclpy.node import Node
from sensor_msgs.msg import Joy

ros_logger = logging.get_logger(__name__)


class JoyToTwist(Node):
    """A ROS2 node that converts joystick input to Twist messages.

    This node subscribes to joystick input and publishes Twist messages based on the joystick axes and buttons.
    """

    def __init__(self) -> None:
        """Initialize the JoyToTwist node."""
        super().__init__("joy_to_twist_node")
        self.declare_parameter("sub_topic", "/joy")
        self.declare_parameter("pub_topic", "")
        self.declare_parameter("stamped", True)
        self.declare_parameter("config_pkg", "")
        self.declare_parameter("pub_frame", "")
        self.declare_parameter("scale", 1.0)

        sub_topic = self.get_parameter("sub_topic").get_parameter_value().string_value
        pub_topic = self.get_parameter("pub_topic").get_parameter_value().string_value
        self.stamped = self.get_parameter("stamped").get_parameter_value().bool_value
        config_pkg = self.get_parameter("config_pkg").get_parameter_value().string_value
        pub_frame = self.get_parameter("pub_frame").get_parameter_value().string_value
        self.scale = self.get_parameter("scale").get_parameter_value().double_value

        if not sub_topic:
            self.get_logger().warn("No subscriber topic was specified. Exiting.")
            return

        if not pub_topic:
            self.get_logger().warn("No publisher topic was specified. Exiting.")
            return

        if not config_pkg:
            self.get_logger().warn("No package for config file was specified. Exiting.")
            return

        config = get_file_path(config_pkg, ["config"], "gamepad_mapping.yaml")
        self.mapping = get_yaml(config)

        if not self.mapping:
            self.get_logger().warn(f"No mapping was found in {config}. Exiting.")
            return

        self.create_subscription(Joy, sub_topic, self.handle_input, 10)
        self.pub = self.create_publisher(
            TwistStamped if self.stamped else Twist, pub_topic, 10
        )
        self.twist_msg = Twist()
        self.twist_stamped_msg = TwistStamped()
        self.twist_stamped_msg.twist = self.twist_msg
        self.twist_stamped_msg.header.frame_id = pub_frame
        self.profile = "A"

    def handle_input(self, sub_msg: Joy) -> None:
        """Handle incoming joystick messages and convert them to Twist messages.

        Args:
            sub_msg (Joy): The incoming joystick message containing axes and buttons.
        """
        for idx in range(len(sub_msg.axes)):
            joy_value = sub_msg.axes[idx]
            if idx not in self.mapping["axes"]:
                continue
            axis: dict = self.mapping["axes"][idx]

            if axis == "switch_profile":
                self.profile = "A" if joy_value > -1 else "B"
                continue

            for movement in ["angular", "linear"]:
                config: dict = axis.get(movement)
                if config is None:
                    continue
                profile = config.get("profile", self.profile)
                if profile != self.profile:
                    twist_value = 0.0
                else:
                    twist_value = -joy_value if config.get("flip", False) else joy_value
                    twist_value *= self.scale if 0 <= self.scale <= 1 else 1
                direction = config["direction"]
                vector = getattr(self.twist_msg, movement)
                setattr(vector, direction, twist_value)
        if self.stamped:
            self.twist_stamped_msg.header.stamp = self.get_clock().now().to_msg()
            self.pub.publish(self.twist_stamped_msg)
        else:
            self.pub.publish(self.twist_msg)


def main(args: list | None = None) -> None:
    """Main function to initialize the ROS2 node and spin it.

    Args:
        args (list | None): Command line arguments, defaults to None.
    """
    rclpy.init(args=args)
    node = JoyToTwist()
    spin_node(node)


if __name__ == "__main__":
    main()
