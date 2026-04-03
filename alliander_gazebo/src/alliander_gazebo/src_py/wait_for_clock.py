#!/usr/bin/env python3
# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import rclpy
from rclpy.node import Node
from rosgraph_msgs.msg import Clock


class WaitForClock(Node):
    """Test."""
    def __init__(self):
        """Test."""
        super().__init__("wait_for_clock")
        self.received = False
        self.create_subscription(Clock, "/clock", self.cb, 10)

    def cb(self, msg: Clock) -> None:  # noqa: ARG002
        """Test.

        Args:
            msg (Clock): test.
        """
        self.get_logger().info(f"Received /clock: {msg.clock}, continuing...")
        self.received = True


def main(args: list | None = None) -> None:
    """Test.

    Args:
        args (list | None): Command line arguments, defaults to None.
    """
    rclpy.init(args=args)
    node = WaitForClock()

    while rclpy.ok() and not node.received:
        rclpy.spin_once(node, timeout_sec=0.1)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
