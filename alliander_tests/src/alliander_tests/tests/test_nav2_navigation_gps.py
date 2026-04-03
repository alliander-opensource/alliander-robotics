# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import copy
import sys
import time

import rclpy
from alliander_utilities.config_objects import GPS, Lidar, Vehicle, link
from geographic_msgs.msg import GeoPath, GeoPoseStamped
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix

from ..utils import call_trigger_service, wait_for_subscriber


class _TestNavigationGPS:
    """Base class for navigation GPS tests.

    Attributes:
         platforms (dict): A dictionary of the platforms to launch.
         world (str): The world to launch.
    """

    platforms: dict
    world: str = "map_5.940906_51.966960"

    def test_goal_pose_gps(
        self, test_node: Node, navigation_degree_tolerance: float, timeout: int
    ) -> None:
        """Test that navigation to a goal pose is successful.

        Args:
            test_node (Node): The ROS 2 node to use for the test.
            navigation_degree_tolerance (float): The tolerance for navigation.
            timeout (int): The timeout in seconds.

        Raises:
            TimeoutError: When a timeout occurs.
        """
        timeout = 2  # TEST
        # 1) Obtain current GPS location:
        current_nav_sat = NavSatFix()

        def callback(msg: NavSatFix) -> None:
            current_nav_sat.latitude = msg.latitude
            current_nav_sat.longitude = msg.longitude

        test_node.create_subscription(
            NavSatFix, f"/{self.platforms['gps'].namespace}/gps/fix", callback, 10
        )

        start_time = time.time()
        while current_nav_sat == NavSatFix():
            rclpy.spin_once(test_node, timeout_sec=0)
            if time.time() - start_time > timeout:
                raise TimeoutError("Timeout while waiting for current GPS location.")

        # 2) Publish goal GPS location 1e-5 degrees north of current location:
        goal_nav_sat = copy.deepcopy(current_nav_sat)
        goal_nav_sat.latitude += 1e-5

        publisher = test_node.create_publisher(GeoPath, "/gps_waypoints", 10)
        wait_for_subscriber(publisher, timeout)
        goal_msg = GeoPath()
        goal_pose = GeoPoseStamped()
        goal_pose.pose.position.latitude = goal_nav_sat.latitude
        goal_pose.pose.position.longitude = goal_nav_sat.longitude
        goal_msg.poses.append(goal_pose)
        publisher.publish(goal_msg)

        # 3) Wait until goal is reached within tolerance:
        start_time = time.time()
        distance: float = sys.float_info.max
        timed_out = False
        last_log_time = 0.0

        while distance > navigation_degree_tolerance:
            rclpy.spin_once(test_node, timeout_sec=0)
            distance = abs(current_nav_sat.latitude - goal_nav_sat.latitude)
            now = time.time()
            if now - last_log_time >= 1.0:
                test_node.get_logger().info(f"Distance to goal: {distance}")
                last_log_time = now
            if time.time() - start_time > timeout:
                timed_out = True
                break

        test_node.get_logger().info(f"Final distance to goal: {distance}.")

        assert not timed_out, (
            f"Timeout: distance {distance} > tolerance {navigation_degree_tolerance}"
        )

        # 4) Stop navigation, since the goal can be reached before the navigation is finished due to tolerance:
        assert call_trigger_service(
            test_node,
            f"/{self.platforms['vehicle'].namespace}/nav2_manager/stop",
            timeout,
        )


for vehicle in ["panther", "lynx"]:
    for lidar in ["velodyne", "ouster"]:
        for gps in ["gps"]:
            vehicle_platform = Vehicle(vehicle, (0, 0, 0.2))
            lidar_platform = Lidar(lidar, (0.13, -0.13, 0.35))
            gps_platform = GPS(gps, (0, 0, 0.2))
            link(vehicle_platform, lidar_platform)
            link(vehicle_platform, gps_platform)
            # vehicle_platform.nav2_config.navigation = True
            # vehicle_platform.nav2_config.gps = True
            test_class = type(
                f"Test{vehicle.capitalize()}{lidar.capitalize()}{gps.capitalize()}Navigation",
                (_TestNavigationGPS,),
                {
                    "platforms": {
                        "vehicle": vehicle_platform,
                        "lidar": lidar_platform,
                        "gps": gps_platform,
                    }
                },
            )
            globals()[test_class.__name__] = test_class
