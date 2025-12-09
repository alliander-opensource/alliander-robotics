#!/usr/bin/env python3

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import time

import rclpy
from geographic_msgs.msg import GeoPath, GeoPoseStamped
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
from nav_msgs.msg import Path
from rcdt_utilities.ros_utils import spin_node
from rclpy.node import Node
from std_srvs.srv import Trigger


class Nav2Manager(Node):
    """ROS 2 node to manage navigation using Nav2 BasicNavigator."""

    def __init__(self) -> None:
        """Initialize the Nav2Manager node."""
        super().__init__("nav2_manager")
        self.basic_navigator = BasicNavigator()

        self.create_subscription(PoseStamped, "/goal_pose", self.cb_goal_pose, 10)
        self.create_subscription(Path, "/waypoints", self.cb_waypoints, 10)
        self.create_subscription(GeoPath, "/gps_waypoints", self.cb_gps_waypoints, 10)
        self.create_service(Trigger, "~/stop", self.cb_stop)

        self.get_logger().info("Controller is ready.")

    def cb_goal_pose(self, msg: PoseStamped) -> None:
        """Callback on receiving a PoseStamped message with a goal pose.

        Args:
            msg (PoseStamped): The received PoseStamped message.
        """
        self.get_logger().info("Received new goal pose for navigation.")
        self.basic_navigator.goToPose(msg)

    def cb_waypoints(self, msg: Path) -> None:
        """Callback on receiving a Path message with waypoints.

        Args:
            msg (Path): The received Path message.
        """
        self.get_logger().info("Received new waypoints for navigation.")
        self.basic_navigator.followWaypoints(msg.poses)

    def cb_gps_waypoints(self, msg: GeoPath) -> None:
        """Callback on receiving a GeoPoseStamped message with GPS waypoints.

        Args:
            msg (GeoPath): The received GeoPath message.
        """
        self.get_logger().info("Received new GPS waypoints for navigation.")
        geo_poses = []
        for geo_pose_stamped in msg.poses:
            geo_pose_stamped: GeoPoseStamped
            geo_poses.append(geo_pose_stamped.pose)
        self.basic_navigator.followGpsWaypoints(geo_poses)

    def cb_stop(
        self, _: Trigger.Request, response: Trigger.Response
    ) -> Trigger.Response:
        """Stop any active navigation goal.

        Args:
            response (Trigger.Response): The response object.

        Returns:
            Trigger.Response: The response object.
        """
        active_task = not self.basic_navigator.isTaskComplete()
        if not active_task:
            response.message = "No active navigation task to stop."
            response.success = True
            self.get_logger().info(response.message)
            return response

        start = time.time()
        timeout = 3.0  # seconds
        self.basic_navigator.cancelTask()
        while time.time() - start < timeout:
            if self.basic_navigator.isTaskComplete():
                response.message = "Successfully cancelled the active navigation task."
                response.success = True
                self.get_logger().info(response.message)
                return response
            time.sleep(0.1)

        response.message = "Failed to cancel the active navigation task within timeout."
        response.success = False
        self.get_logger().warn(response.message)
        return response


def main(args: list | None = None) -> None:
    """Main function to initialize the ROS 2 node and set the thresholds.

    Args:
        args (list | None): Command line arguments, defaults to None.
    """
    rclpy.init(args=args)
    node = Nav2Manager()
    spin_node(node)


if __name__ == "__main__":
    main()
