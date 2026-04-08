#!/usr/bin/env python3
# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import math

import rclpy
from geometry_msgs.msg import TwistStamped
from rclpy.node import Node

# Thresholds for abnormal behaviour:
MAX_LINEAR_X = 2.0  # m/s
MAX_LINEAR_Y = 0.1  # m/s — differential drive should not move sideways
MAX_ANGULAR_Z = 2.0  # rad/s


class CmdVelLogger(Node):
    """Test."""

    def __init__(self) -> None:
        """Test."""
        super().__init__("cmd_vel_logger")
        self.sub_panther = self.create_subscription(
            TwistStamped, "/panther/cmd_vel", self._callback_panther, 10
        )
        self.sub_lynx = self.create_subscription(
            TwistStamped, "/lynx/cmd_vel", self._callback_lynx, 10
        )
        self.sub_drive_controller = self.create_subscription(
            TwistStamped, "/drive_controller/cmd_vel", self._callback_cmd_vel, 10
        )
        self.sub_cmd_vel = self.create_subscription(
            TwistStamped, "/cmd_vel", self._callback_cmd_vel, 10
        )
        self.get_logger().info(
            "cmd_vel_logger started, listening to /panther/cmd_vel and /lynx/cmd_vel"
        )
        self.last_time = 0

    def _callback_panther(self, msg: TwistStamped) -> None:
        self.get_logger().warn(
            f"Found data on /panther/cmd_vel, with timestamp: {msg.header.stamp}"
        )
        self._check_nan(msg, "panther")
        self._check_timing(msg, "/panther/cmd_vel")

    def _callback_lynx(self, msg: TwistStamped) -> None:
        self.get_logger().warn(
            f"Found data on /lynx/cmd_vel, with timestamp: {msg.header.stamp}"
        )
        self._check_nan(msg, "lynx")
        self._check_timing(msg, "/lynx/cmd_vel")

    def _callback_cmd_vel(self, msg: TwistStamped) -> None:
        self.get_logger().warn(
            f"Found data on /cmd_vel, with timestamp: {msg.header.stamp}"
        )

    def _callback_drive_cmd_vel(self, msg: TwistStamped) -> None:
        self.get_logger().warn(
            f"Found data on /drive_controller/cmd_vel, with timestamp: {msg.header.stamp}"
        )
        publishers = self.get_publishers_info_by_topic("/drive_controller/cmd_vel")
        for pub in publishers:
            self.get_logger().info(
                f"Publisher on /drive_controller/cmd_vel: "
                f"node={pub.node_name}, "
                f"namespace={pub.node_namespace}, "
                f"type={pub.topic_type}"
            )

    def _check_nan(self, msg: TwistStamped, namespace: str) -> None:
        msg = msg.twist
        values = {
            "linear.x": msg.linear.x,
            "linear.y": msg.linear.y,
            "linear.z": msg.linear.z,
            "angular.x": msg.angular.x,
            "angular.y": msg.angular.y,
            "angular.z": msg.angular.z,
        }
        for field, value in values.items():
            if math.isnan(value) or math.isinf(value) or not math.isfinite(value):
                self.get_logger().error(
                    f"cmd_vel contains invalid value in {field}: {value}"
                )
                publishers = self.get_publishers_info_by_topic(f"/{namespace}/cmd_vel")
                for pub in publishers:
                    self.get_logger().info(
                        f"Publisher on /{namespace}/cmd_vel: "
                        f"node={pub.node_name}, "
                        f"namespace={pub.node_namespace}, "
                        f"type={pub.topic_type}"
                    )

    def _check_timing(self, msg: TwistStamped, topic: str) -> None:
        now = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

        if self.last_time is not None:
            dt = now - self.last_time

            if dt > 0.5:  # noqa: PLR2004
                self.get_logger().warn(
                    f"[{topic}] Large time gap detected: dt={dt:.3f}s (clock pause?)"
                )

            if dt < 0:
                self.get_logger().error(
                    f"[{topic}] Time went backwards! dt={dt:.6f}"
                )

        self.last_time = now


def main() -> None:
    """Test."""
    rclpy.init()
    node = CmdVelLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
