#!/usr/bin/env python3

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import time

import rclpy
import tf2_geometry_msgs  # ruff: ignore[unused-import] (required for tf transform)
from alliander_interfaces.action import TriggerAction
from alliander_nav2.docking_control import DockingControl
from alliander_nav2.speed_control import Speed, SpeedControl
from alliander_utilities.ros_utils import spin_executor
from geographic_msgs.msg import GeoPath, GeoPoseStamped
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
from nav_msgs.msg import Path
from rclpy.action import ActionServer, CancelResponse
from rclpy.action.server import ServerGoalHandle
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from std_srvs.srv import Trigger
from tf2_ros import Buffer, TransformListener

NAVIGATION_SPEED = Speed(linear=2.0, angular=3.14)


class Nav2Manager(Node):
    """ROS 2 node to manage navigation using Nav2 BasicNavigator."""

    def __init__(self) -> None:
        """Initialize the Nav2Manager node."""
        super().__init__("nav2_manager")

        self.basic_navigator: BasicNavigator = BasicNavigator()
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.speed_control = SpeedControl(self)
        self.docking_control = DockingControl(
            self, self.tf_buffer, self.basic_navigator, self.speed_control
        )

        callback_group = ReentrantCallbackGroup()
        self.create_subscription(
            PoseStamped,
            "/goal_pose",
            self.cb_goal_pose,
            10,
            callback_group=callback_group,
        )
        self.create_subscription(
            Path,
            "/waypoints",
            self.cb_waypoints,
            10,
            callback_group=callback_group,
        )
        self.create_subscription(
            GeoPath,
            "/gps_waypoints",
            self.cb_gps_waypoints,
            10,
            callback_group=callback_group,
        )

        self.create_service(Trigger, "~/stop", self.cb_stop)

        ActionServer(
            self,
            TriggerAction,
            "~/dock_robot",
            self.cb_dock_robot,
            cancel_callback=self.cb_docking_cancel,
        )
        ActionServer(
            self,
            TriggerAction,
            "~/undock_robot",
            self.cb_undock_robot,
            cancel_callback=self.cb_docking_cancel,
        )

        self.get_logger().info("Controller is ready.")

    def cb_dock_robot(self, goal_handle: ServerGoalHandle) -> TriggerAction.Result:
        """Callback on a dock robot action.

        Args:
            goal_handle (ServerGoalHandle): The goal handle for the received action goal.

        Returns:
            TriggerAction.Result: The result of the action.
        """
        result = TriggerAction.Result()
        result.success = self.docking_control.dock_robot()
        goal_handle.succeed() if result.success else goal_handle.abort()
        return result

    def cb_undock_robot(self, goal_handle: ServerGoalHandle) -> TriggerAction.Result:
        """Callback on an undock robot action.

        Args:
            goal_handle (ServerGoalHandle): The goal handle for the received action goal.

        Returns:
            TriggerAction.Result: The result of the action.
        """
        result = TriggerAction.Result()
        result.success = self.docking_control.undock_robot()
        goal_handle.succeed() if result.success else goal_handle.abort()
        return result

    def cb_docking_cancel(self, _: ServerGoalHandle) -> CancelResponse:
        """Callback when a dock robot action is canceled.

        Returns:
            CancelResponse: The response indicating whether the cancel request is accepted.
        """
        self.docking_control.cancel()
        return CancelResponse.ACCEPT

    def cb_goal_pose(self, msg: PoseStamped) -> None:
        """Callback on receiving a PoseStamped message with a goal pose.

        Args:
            msg (PoseStamped): The received PoseStamped message.
        """
        self.get_logger().info("Received new goal pose for navigation.")
        if self.speed_control.set_max_speed(NAVIGATION_SPEED):
            self.basic_navigator.goToPose(msg)

    def cb_waypoints(self, msg: Path) -> None:
        """Callback on receiving a Path message with waypoints.

        Args:
            msg (Path): The received Path message.
        """
        self.get_logger().info("Received new waypoints for navigation.")
        if self.speed_control.set_max_speed(NAVIGATION_SPEED):
            self.basic_navigator.followWaypoints(msg.poses)

    def cb_gps_waypoints(self, msg: GeoPath) -> None:
        """Callback on receiving a GeoPoseStamped message with GPS waypoints.

        Args:
            msg (GeoPath): The received GeoPath message.
        """
        self.get_logger().info("Received new GPS waypoints for navigation.")
        if self.speed_control.set_max_speed(NAVIGATION_SPEED):
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

    # Use an executor to avoid problems with BasicNavigator's internal spinning:
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    spin_executor(executor)


if __name__ == "__main__":
    main()
