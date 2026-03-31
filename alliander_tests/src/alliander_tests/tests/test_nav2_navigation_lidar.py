# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import contextlib
import math
import sys
import time

import rclpy
from alliander_utilities.config_objects import Lidar, Vehicle, link
from geometry_msgs.msg import PoseStamped, TransformStamped, TwistStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import JointState
from tf2_ros import TransformException  # ty: ignore[unresolved-import]
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener

from ..utils import call_trigger_service, wait_for_node_active, wait_for_subscriber


class _TestNavigationLidar:
    """Base class for lidar navigation tests.

    Attributes:
        platforms (dict): A dictionary of the platforms to launch.
        world (str): The world to launch.
    """

    platforms: dict
    world: str = "test_navigation.sdf"

    def test_goal_pose_lidar(
        self, test_node: Node, navigation_distance_tolerance: float, timeout: int
    ) -> None:
        """Test that navigation to a goal pose is successful.

        Args:
            test_node (Node): The ROS 2 node to use for the test.
            navigation_distance_tolerance (float): The tolerance for navigation.
            timeout (int): The timeout in seconds.

        Raises:
            TimeoutError: When a timeout occurs.
        """

        # 0) Log callbacks
        def joint_state_callback(msg: JointState) -> None:
            joint_state: JointState = msg
            if math.isnan(joint_state.position[0]):
                test_node.get_logger().error("ERROR: joint state is NaN!")

        test_node.create_subscription(
            JointState,
            f"/{self.platforms['vehicle'].namespace}/joint_states",
            joint_state_callback,
            10,
        )

        def odom_callback(msg: Odometry) -> None:
            odom: Odometry = msg
            if math.isnan(odom.pose.pose.position.x):
                test_node.get_logger().error("ERROR: odom is NaN!")

        test_node.create_subscription(
            Odometry,
            f"/{self.platforms['vehicle'].namespace}/odom",
            odom_callback,
            10,
        )

        def twist_callback(msg: TwistStamped) -> None:
            twist: TwistStamped = msg
            if math.isnan(twist.twist.linear.x):
                test_node.get_logger().error("ERROR: cmd_vel is NaN!")

        test_node.create_subscription(
            TwistStamped,
            f"/{self.platforms['vehicle'].namespace}/cmd_vel",
            twist_callback,
            10,
        )
        # 1) Obtain current pose in map frame:
        tf_buffer = Buffer()
        TransformListener(tf_buffer, test_node)
        current_pose = TransformStamped()

        start_time = time.time()
        while current_pose == TransformStamped():
            rclpy.spin_once(test_node, timeout_sec=0)  # TODO: change to 0.1 maybe?
            with contextlib.suppress(TransformException):
                current_pose = tf_buffer.lookup_transform(
                    "map", f"{self.platforms['vehicle'].namespace}/base_link", Time()
                )
            if time.time() - start_time > timeout:
                raise TimeoutError()

        # 2) Publish goal pose 3 meter in front of current position:
        goal_pose = PoseStamped()
        goal_pose.header.frame_id = "map"
        goal_pose.pose.position.x = current_pose.transform.translation.x + 3
        goal_pose.pose.position.y = current_pose.transform.translation.y
        goal_pose.pose.position.z = current_pose.transform.translation.z

        publisher = test_node.create_publisher(PoseStamped, "/goal_pose", 10)
        wait_for_node_active(
            test_node, f"/{self.platforms['vehicle'].namespace}/bt_navigator", 10.0
        )
        wait_for_node_active(
            test_node, f"/{self.platforms['vehicle'].namespace}/planner_server", 10.0
        )
        wait_for_node_active(
            test_node, f"/{self.platforms['vehicle'].namespace}/controller_server", 10.0
        )
        wait_for_subscriber(publisher, timeout)
        publisher.publish(goal_pose)
        test_node.get_logger().info("Published goal pose for navigation.")

        # 3) Wait until goal is reached within tolerance:
        start_time = time.time()
        distance: float = sys.float_info.max
        timed_out = False
        last_log_time = 0.0

        while distance > navigation_distance_tolerance:
            rclpy.spin_once(test_node, timeout_sec=0)
            with contextlib.suppress(TransformException):
                current_pose = tf_buffer.lookup_transform(
                    "map", f"{self.platforms['vehicle'].namespace}/base_link", Time()
                )
                distance = abs(
                    current_pose.transform.translation.x - goal_pose.pose.position.x
                )
            now = time.time()
            if now - last_log_time >= 1.0:
                test_node.get_logger().info(f"Distance to goal: {distance:.2f}m")
                last_log_time = now
            if time.time() - start_time > timeout:
                timed_out = True
                break

        test_node.get_logger().info(f"Final TEST distance to goal: {distance}.")

        assert not timed_out, (
            f"Timeout: distance {distance} > tolerance {navigation_distance_tolerance}"
        )

        # 4) Stop navigation, since the goal can be reached before the navigation is finished due to tolerance:
        assert call_trigger_service(
            test_node,
            f"/{self.platforms['vehicle'].namespace}/nav2_manager/stop",
            timeout,
        )


for i, vehicle in enumerate(
    [
        "panther",
        "lynx",
        "panther",
        "lynx",
        "panther",
        "lynx",
        "panther",
        "lynx",
        "panther",
        "lynx",
    ]
):
    for lidar in ["velodyne", "ouster", "velodyne", "ouster", "velodyne"]:
        vehicle_platform = Vehicle(vehicle, (0, 0, 0.2))
        lidar_platform = Lidar(lidar, (0.13, -0.13, 0.35))
        link(vehicle_platform, lidar_platform)
        # vehicle_platform.nav2_config.navigation = True
        test_class = type(
            f"Test{vehicle.capitalize()}{lidar.capitalize()}Navigation{i}",
            (_TestNavigationLidar,),
            {"platforms": {"vehicle": vehicle_platform, "lidar": lidar_platform}},
        )
        globals()[test_class.__name__] = test_class
