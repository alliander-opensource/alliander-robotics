#!/usr/bin/env python3
# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import math

import rclpy
from geometry_msgs.msg import TwistStamped
from rclpy.node import Node

# Thresholds for abnormal behaviour:
MAX_LINEAR_X = 2.0       # m/s
MAX_LINEAR_Y = 0.1       # m/s — differential drive should not move sideways
MAX_ANGULAR_Z = 2.0      # rad/s


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
        self.get_logger().info("cmd_vel_logger started, listening to /panther/cmd_vel and /lynx/cmd_vel")

    def _callback_panther(self, msg: TwistStamped) -> None:
        sender = msg.header.frame_id or "<unknown>"
        self.get_logger().info(f"Received from frame_id: {sender}")
        self._check_nan(msg)
        self._check_limits(msg)

    def _callback_lynx(self, msg: TwistStamped) -> None:
        sender = msg.header.frame_id or "<unknown>"
        self.get_logger().info(f"Received from frame_id: {sender}")
        self._check_nan(msg)
        self._check_limits(msg)

    def _check_nan(self, msg: TwistStamped) -> None:
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
            if math.isnan(value) or math.isinf(value):
                self.get_logger().error(f"cmd_vel contains invalid value in {field}: {value}")

    def _check_limits(self, msg: TwistStamped) -> None:
        msg = msg.twist
        if abs(msg.linear.x) > MAX_LINEAR_X:
            self.get_logger().warning(
                f"Linear X velocity {msg.linear.x:.2f} m/s exceeds limit of {MAX_LINEAR_X} m/s"
            )
        if abs(msg.linear.y) > MAX_LINEAR_Y:
            self.get_logger().warning(
                f"Unexpected lateral velocity linear.y={msg.linear.y:.2f} m/s "
                f"(differential drive should not move sideways)"
            )
        if abs(msg.angular.z) > MAX_ANGULAR_Z:
            self.get_logger().warning(
                f"Angular Z velocity {msg.angular.z:.2f} rad/s exceeds limit of {MAX_ANGULAR_Z} rad/s"
            )


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
