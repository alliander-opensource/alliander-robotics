#!/usr/bin/env python3
# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

"""Meta Quest Reader."""

import numpy as np
import rclpy
from alliander_meta.meta_quest_reader import MetaQuestReader
from geometry_msgs.msg import TransformStamped
from rclpy.node import Node
from scipy.spatial.transform import Rotation
from sensor_msgs.msg import Joy
from tf2_ros import TransformBroadcaster


class MetaQuestNode(Node):
    """Node to read data from the Meta Quest."""

    def __init__(self):
        """Initialize the node."""
        super().__init__("meta_quest_node")
        self.tf_broadcaster = TransformBroadcaster(self)

        self.reader = MetaQuestReader()
        self.pub_joy = self.create_publisher(Joy, "/quest/joystick", 10)

        self.create_timer(0.001, self.publish_tf)
        self.create_timer(0.01, self.publish_joystick)
        self.get_logger().info("Meta Quest Node initialized.")

    def publish_joystick(self) -> None:
        """Publish the joystick data."""
        joy = Joy()
        joy.axes = [0.0] * 6
        joy.buttons = [0] * 10
        joy.axes[0] = self.reader.get_trigger_value("right")
        joy.axes[1] = self.reader.get_grip_value("right")
        joy.buttons[0] = self.reader.get_button_state("A")
        joy.header.stamp = self.get_clock().now().to_msg()
        self.pub_joy.publish(joy)

    def publish_tf(self) -> None:
        """Publish the tf data."""
        transform = self.reader.get_hand_controller_transform_ros("right")
        if not isinstance(transform, np.ndarray):
            return

        transform_stamped = TransformStamped()
        transform_stamped.header.frame_id = "map"
        transform_stamped.child_frame_id = "quest/hand_right"

        transform_stamped.transform.translation.x = transform[0, 3]
        transform_stamped.transform.translation.y = transform[1, 3]
        transform_stamped.transform.translation.z = transform[2, 3]

        rotation = Rotation.from_matrix(transform[:3, :3])
        rotation *= Rotation.from_euler("xyz", [0, np.pi / 2, np.pi / 2])

        quat = rotation.as_quat()
        transform_stamped.transform.rotation.x = quat[0]
        transform_stamped.transform.rotation.y = quat[1]
        transform_stamped.transform.rotation.z = quat[2]
        transform_stamped.transform.rotation.w = quat[3]

        transform_stamped.header.stamp = self.get_clock().now().to_msg()
        self.tf_broadcaster.sendTransform(transform_stamped)


def main(args: list | None = None) -> None:
    """Main function to initialize the ROS 2 node.

    Args:
        args (list | None): Command line arguments, defaults to None.
    """
    rclpy.init(args=args)
    reader = MetaQuestNode()
    rclpy.spin(reader)
    reader.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
