#!/usr/bin/env python3
# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import rclpy
from alliander_utilities.ros_utils import spin_node
from geometry_msgs.msg import PoseStamped, TransformStamped
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import Joy
from tf2_msgs.msg import TFMessage
from tf2_ros import TransformBroadcaster, TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener

NS_ARM = "franka"


class Teleoperation(Node):
    def __init__(self):
        """Initialize the node."""
        super().__init__("teleoperation")
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.create_subscription(Joy, "/quest/joystick", self.handle_joystick, 10)
        self.create_subscription(TFMessage, "/meta/tf", self.handle_tf, 10)
        self.tf_publisher = self.create_publisher(TFMessage, "/tf", 10)
        self.servo_publisher = self.create_publisher(
            PoseStamped, "/franka/servo_node/pose_target_cmds", 10
        )
        self.timer = self.create_timer(0.01, self.publish_servo_target)

        self.outdated = True
        self.transform = TransformStamped()
        self.transform.header.frame_id = "hand_right"
        self.transform.child_frame_id = "end_effector_target"

        self.pose = PoseStamped()
        self.pose.header.frame_id = "map"

    def handle_tf(self, msg: TFMessage) -> None:
        """Handle incoming TF messages.

        Args:
            msg (TFMessage): The incoming TF message.
        """
        for transform in msg.transforms:
            transform.header.stamp = self.get_clock().now().to_msg()
        self.tf_publisher.publish(msg)

    def handle_joystick(self, msg: Joy) -> None:
        """Handle incoming joystick messages.

        Args:
            msg (Joy): The incoming joystick message.
        """
        if msg.axes[5] == 1:
            if self.outdated:
                self.set_end_effector_target_to_current_pose()
                self.outdated = False
            self.publish_tf()
        else:
            self.outdated = True

    def publish_servo_target(self) -> None:
        """Publish the servo target."""
        try:
            transform = self.tf_buffer.lookup_transform(
                self.pose.header.frame_id,
                "end_effector_target",
                Time(),
            )
            self.pose.header.stamp = self.get_clock().now().to_msg()
            self.pose.pose.position.x = transform.transform.translation.x
            self.pose.pose.position.y = transform.transform.translation.y
            self.pose.pose.position.z = transform.transform.translation.z
            self.pose.pose.orientation = transform.transform.rotation
            self.servo_publisher.publish(self.pose)
        except TransformException:
            pass

    def publish_tf(self) -> None:
        self.transform.header.stamp = self.get_clock().now().to_msg()
        self.tf_broadcaster.sendTransform(self.transform)

    def set_end_effector_target_to_current_pose(self) -> None:
        """Set the end effector target to the current pose."""
        try:
            transform = self.tf_buffer.lookup_transform(
                "hand_right",
                f"{NS_ARM}/fr3_link7",
                Time(),
            )
            self.transform.transform = transform.transform
        except TransformException as e:
            self.get_logger().error(f"Could not get transform: {e}")


def main(args: list | None = None) -> None:
    """Main function to initialize the ROS 2 node and set the thresholds.

    Args:
        args (list | None): Command line arguments, defaults to None.
    """
    rclpy.init(args=args)
    node = Teleoperation()
    spin_node(node)


if __name__ == "__main__":
    main()
