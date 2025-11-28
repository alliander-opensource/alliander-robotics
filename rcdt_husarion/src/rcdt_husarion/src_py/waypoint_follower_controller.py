#!/usr/bin/env python3
# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import rclpy
from action_msgs.msg import GoalStatus
from action_msgs.srv import CancelGoal
from nav2_msgs.action import FollowWaypoints
from nav_msgs.msg import Path
from rcdt_utilities.ros_utils import spin_executor
from rclpy.action import ActionClient
from rclpy.action.client import ClientGoalHandle
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.task import Future
from std_srvs.srv import Trigger


class WaypointFollowerController(Node):
    """Node to control the starting and stopping of the waypoint follower node."""

    def __init__(self, executor: SingleThreadedExecutor) -> None:
        """Initialize the WaypointFollowerController node.

        Args:
            executor (SingleThreadedExecutor): The executor is required for the spin_until_future_complete calls, otherwise a second call never finishes.
        """
        super().__init__("waypoint_follower_controller")
        self.executor = executor
        self.namespace = self.get_namespace().lstrip("/")

        cb_waypoints = MutuallyExclusiveCallbackGroup()
        cb_stop = MutuallyExclusiveCallbackGroup()

        self.create_subscription(
            Path, "/waypoints", self.cb_waypoints, 10, callback_group=cb_waypoints
        )
        self.create_service(Trigger, "~/stop", self.cb_stop, callback_group=cb_stop)

        self.follow_waypoints_action_client = ActionClient(
            self, FollowWaypoints, f"/{self.namespace}/follow_waypoints"
        )
        self.follow_waypoints_goal_handle: ClientGoalHandle | None = None
        self.follow_waypoints_goal = FollowWaypoints.Goal()

        self.navigate_to_pose_cancel_service_client = self.create_client(
            CancelGoal, f"/{self.namespace}/navigate_to_pose/_action/cancel_goal"
        )

        self.get_logger().info("Controller is ready.")

    def cb_waypoints(self, msg: Path) -> None:
        """Callback on receiving a Path message with waypoints.

        First stops any active navigation goal, then starts a new navigation goal with the received waypoints.

        Args:
            msg (Path): The received Path message.
        """
        if self.follow_waypoints_goal_handle is not None and not self.stop_navigation():
            self.get_logger().error("Failed to stop active goal.")
            return
        if not msg.poses:
            self.get_logger().warning(
                "Path contains zero waypoints, not starting navigation."
            )
            return

        self.follow_waypoints_goal = FollowWaypoints.Goal()
        self.follow_waypoints_goal.poses = msg.poses
        self.start_navigation()

    def cb_stop(
        self, _: Trigger.Request, response: Trigger.Response
    ) -> Trigger.Response:
        """Stop any active navigation goal.

        Args:
            response (Trigger.Response): The response object.

        Returns:
            Trigger.Response: The response object.
        """
        response.success = self.stop_navigation()
        return response

    def cb_finished(self, future: Future) -> None:
        """Callback when the navigation to waypoints is finished. Logs the result and resets the goal handle.

        Args:
            future (Future): The future containing the result of the action.
        """
        self.follow_waypoints_goal_handle = None
        response: FollowWaypoints.Impl.GetResultService.Response = future.result()
        result = response.result
        if response.status == GoalStatus.STATUS_CANCELED:
            self.get_logger().warning("Navigation was canceled.")
            return

        if response.status != GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().error(
                f"Navigation failed with status code {response.status}."
            )
            return

        self.get_logger().info("Navigation successfully finished!")
        if result.missed_waypoints:
            self.get_logger().warning(
                f"Missed {len(result.missed_waypoints)} waypoints during navigation: {result.missed_waypoints}."
            )

    def start_navigation(self) -> None:
        """Start the navigation to waypoints."""
        pre_msg = "Failed to start navigation:"
        if not self.follow_waypoints_action_client.wait_for_server(1):
            self.get_logger().error(f"{pre_msg} Failed to connect to action server.")
            return
        future = self.follow_waypoints_action_client.send_goal_async(
            self.follow_waypoints_goal
        )
        rclpy.spin_until_future_complete(self, future, self.executor, 1)
        if not future.done():
            self.get_logger().error(f"{pre_msg} No response within timeout.")
            return
        goal_handle: ClientGoalHandle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error(f"{pre_msg} Action goal was not accepted.")
            return
        self.get_logger().info("Navigation to waypoints is started!")
        self.follow_waypoints_goal_handle = goal_handle
        self._get_result_future: Future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.cb_finished)

    def stop_navigation(self) -> bool:
        """Stop the active navigation goal. If no goal is active, cancel all goals on the navigate_to_pose action server.

        Returns:
            bool: True if the navigation was stopped successfully, False otherwise.
        """
        pre_msg = "Failed to stop navigation:"
        if self.follow_waypoints_goal_handle is None:
            self.get_logger().warning(
                "No navigation task was active. Cancelling all goals on navigate_to_pose..."
            )
            return self.cancel_navigate_to_pose()
        future: Future = self.follow_waypoints_goal_handle.cancel_goal_async()
        rclpy.spin_until_future_complete(self, future, self.executor, 1)
        if not future.done():
            self.get_logger().error(f"{pre_msg} No response within timeout.")
            return False
        response: CancelGoal.Response = future.result()
        if response.return_code != CancelGoal.Response.ERROR_NONE:
            self.get_logger().error(
                f"{pre_msg} Cancel goal returned error code {response.return_code}."
            )
            return False
        self.get_logger().info("Navigation to waypoints is stopped!")
        self.follow_waypoints_goal_handle = None
        return True

    def cancel_navigate_to_pose(self) -> bool:
        """Cancel all the goals on the navigate_to_pose action server.

        Returns:
            bool: True if navigate_to_pose was cancelled successfully, False otherwise.
        """
        pre_msg = "Failed to cancel navigate_to_pose:"
        self.get_logger().info(
            "Cancelling all goals on navigate_to_pose action server..."
        )
        future: Future = self.navigate_to_pose_cancel_service_client.call_async(
            CancelGoal.Request()
        )
        rclpy.spin_until_future_complete(self, future, self.executor, 1)
        if not future.done():
            self.get_logger().error(f"{pre_msg} No response within timeout.")
            return False
        response: CancelGoal.Response = future.result()
        if response.return_code != CancelGoal.Response.ERROR_NONE:
            self.get_logger().error(
                f"{pre_msg} Cancel goal returned error code {response.return_code}."
            )
            return False
        self.get_logger().info("All goals on navigate_to_pose were cancelled.")
        return True


def main(args: list | None = None) -> None:
    """Main function to initialize the ROS 2 node and set the thresholds.

    Args:
        args (list | None): Command line arguments, defaults to None.
    """
    rclpy.init(args=args)
    executor = SingleThreadedExecutor()
    node = WaypointFollowerController(executor)
    executor.add_node(node)
    spin_executor(executor)


if __name__ == "__main__":
    main()
