# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import contextlib
import random
import sys
import time

import rclpy
from alliander_utilities.config_objects import Lidar, Vehicle, link
from geometry_msgs.msg import PoseStamped, TransformStamped
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import TransformException  # ty: ignore[unresolved-import]
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener

from ..utils import call_trigger_service, wait_for_subscriber

vehicle = Vehicle(random.choice(["panther", "lynx"]), position=(0, 0, 0.2))
lidar = Lidar(random.choice(["velodyne", "ouster"]), (0.13, -0.13, 0.35))
link(vehicle, lidar)
vehicle.nav2_config.navigation = True

PLATFORMS = [vehicle, lidar]
WORLD = "test_navigation.sdf"


def test_goal_pose_lidar(
    test_node: Node, navigation_distance_tolerance: float, timeout: int
) -> None:
    """Test that navigation to a goal pose is successful.

    Args:
        test_node (Node): The ROS 2 node to use for the test.
        navigation_distance_tolerance (float): The tolerance for navigation.
        timeout (int): The timeout in seconds.

    Raises:
        TimeoutError: When a timeout occurs.
    """
    # 1) Obtain current pose in map frame:
    tf_buffer = Buffer()
    TransformListener(tf_buffer, test_node)
    current_pose = TransformStamped()

    start_time = time.time()
    while current_pose == TransformStamped():
        rclpy.spin_once(test_node, timeout_sec=0)
        with contextlib.suppress(TransformException):
            current_pose = tf_buffer.lookup_transform(
                "map", f"{vehicle.namespace}/base_link", Time()
            )
        if time.time() - start_time > timeout:
            raise TimeoutError()

    # 2) Publish goal pose 3 meter in front of current position:
    goal_pose = PoseStamped()
    goal_pose.header.frame_id = "map"
    goal_pose.pose.position.x = current_pose.transform.translation.x + 3
    goal_pose.pose.position.y = current_pose.transform.translation.y
    goal_pose.pose.position.z = current_pose.transform.translation.z

    publisher = test_node.create_publisher(
        PoseStamped, f"/{vehicle.namespace}/goal_pose", 10
    )
    wait_for_subscriber(publisher, timeout)
    publisher.publish(goal_pose)
    test_node.get_logger().info("Published goal pose for navigation.")

    # 3) Wait until goal is reached within tolerance:
    start_time = time.time()
    distance: float = sys.float_info.max
    while distance > navigation_distance_tolerance:
        rclpy.spin_once(test_node, timeout_sec=0)
        with contextlib.suppress(TransformException):
            current_pose = tf_buffer.lookup_transform(
                "map", f"{vehicle.namespace}/base_link", Time()
            )
        distance = abs(current_pose.transform.translation.x - goal_pose.pose.position.x)
        if time.time() - start_time > timeout:
            raise TimeoutError(
                f"Distance is {distance} while tolerance is {navigation_distance_tolerance}."
            )

    # 4) Stop navigation, since the goal can be reached before the navigation is finished due to tolerance:
    assert call_trigger_service(
        test_node, f"/{vehicle.namespace}/nav2_manager/stop", timeout
    )
