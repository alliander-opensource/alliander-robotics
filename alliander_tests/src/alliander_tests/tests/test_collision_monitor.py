# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import time

import rclpy
from alliander_utilities.config_objects import Lidar, Vehicle, link
from geometry_msgs.msg import TwistStamped
from rclpy.node import Node

from ..utils import wait_for_subscriber


class _TestCollisionMonitoring:
    """Test class for collision monitoring tests.

    Attributes:
         platforms (dict): A dictionary of the platforms to launch.
         world (str): The world to launch for the test.
    """

    platforms: dict
    world: str = "test_navigation.sdf"

    def test_collision_monitoring(self, test_node: Node, timeout: int) -> None:
        """Test that cmd_vel is reduced to 70% by the collision monitor.

        Args:
            test_node (Node): The ROS 2 node to use for the test.
            timeout (int): The timeout in seconds.
        """
        input_velocity = 0.0001
        expected_output = input_velocity * 0.7

        publisher = test_node.create_publisher(
            TwistStamped, f"/{self.platforms['vehicle'].namespace}/cmd_vel_raw", 10
        )
        result = {}

        def callback_function_cmd_vel(msg: TwistStamped) -> None:
            """Callback function to handle messages from the state topic.

            Args:
                msg (TwistStamped): The message received from the state topic.
            """
            result["output_velocity"] = msg.twist.linear.x

        test_node.create_subscription(
            msg_type=TwistStamped,
            topic=f"/{self.platforms['vehicle'].namespace}/cmd_vel_final",
            callback=callback_function_cmd_vel,
            qos_profile=10,
        )

        wait_for_subscriber(publisher, timeout)
        msg = TwistStamped()
        msg.twist.linear.x = input_velocity

        publish_duration = 30  # seconds
        publish_rate_sec = 0.1  # seconds
        deadline = time.monotonic() + publish_duration

        while (
            time.monotonic() < deadline
            and result.get("output_velocity") != expected_output
        ):
            publisher.publish(msg)
            rclpy.spin_once(test_node, timeout_sec=publish_rate_sec)

        assert result.get("output_velocity") == expected_output, (
            f"Expected output velocity to be ~{expected_output}, got {result.get('output_velocity')}"
        )


for vehicle in ["panther", "lynx"]:
    for lidar in ["velodyne", "ouster"]:
        vehicle_platform = Vehicle(vehicle, (0, 0, 0.2))
        lidar_platform = Lidar(lidar, (0.13, -0.13, 0.35))
        link(vehicle_platform, lidar_platform)
        vehicle_platform.nav2_config.navigation = True
        vehicle_platform.nav2_config.collision_monitor = True
        test_class = type(
            f"Test{vehicle.capitalize()}{lidar.capitalize()}CollisionMonitoring",
            (_TestCollisionMonitoring,),
            {"platforms": {"vehicle": vehicle_platform, "lidar": lidar_platform}},
        )
        globals()[test_class.__name__] = test_class
