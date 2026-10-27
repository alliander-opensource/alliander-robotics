# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


import copy
import time

from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.node import Node
from tf2_ros import Buffer

from alliander_nav2.speed_control import Speed, SpeedControl

DOCKING_STAGING_SPEED = Speed(linear=0.2, angular=0.314)


class DockingControl:
    """Class for controlling the docking behavior of the robot."""

    def __init__(
        self,
        node: Node,
        tf_buffer: Buffer,
        basic_navigator: BasicNavigator,
        speed_control: SpeedControl,
    ):
        """Initialize.

        Args:
            node (Node): The ROS 2 node used for creating clients and logging.
            tf_buffer (Buffer): The TF2 buffer for transforming poses between frames.
            basic_navigator (BasicNavigator): The BasicNavigator instance for controlling the robot's navigation.
            speed_control (SpeedControl): The SpeedControl instance for managing the robot's speed.
        """
        self.node = node
        self.logger = node.get_logger()
        self.tf_buffer = tf_buffer
        self.basic_navigator = basic_navigator
        self.speed_control = speed_control

        self.node.declare_parameter("docking_staging_offset", -1.0)
        self.docking_staging_offset: float = self.node.get_parameter(
            "docking_staging_offset"
        ).value

        self.canceled = False

    def cancel(self) -> None:
        """Cancel the docking process."""
        self.canceled = True
        self.logger.info("Canceling docking process...")

    def undock_robot(self) -> bool:
        """Undock the robot.

        Returns:
            bool: True if undocking was successful, False otherwise.
        """
        self.canceled = False
        self.basic_navigator.undockRobot()
        while not self.basic_navigator.isTaskComplete():
            if self.canceled:
                self.basic_navigator.cancelTask()
                return False
            self.logger.info("Undocking...")
            time.sleep(1)
        return self.basic_navigator.getResult() == TaskResult.SUCCEEDED

    def dock_robot(self) -> bool:
        """Dock the robot by first navigating to a staging pose and then performing the final docking maneuver.

        Returns:
            bool: True if docking was successful, False otherwise.
        """
        self.canceled = False
        pose_dock, pose_stage = self.get_poses_in_dock_frame()

        return all(
            [
                self.speed_control.set_max_speed(DOCKING_STAGING_SPEED),
                self.navigate_to_staging_pose(pose_stage),
                self.perform_docking_maneuver(pose_dock),
            ]
        )

    def get_poses_in_dock_frame(self) -> tuple[PoseStamped, PoseStamped]:
        """Define the docking and staging poses.

        Returns:
            tuple[PoseStamped, PoseStamped]: The docking pose and the staging pose.
        """
        pose_dock = PoseStamped()
        pose_dock.header.frame_id = "dock"
        pose_stage = copy.deepcopy(pose_dock)
        pose_stage.pose.position.x = self.docking_staging_offset
        return pose_dock, pose_stage

    def navigate_to_staging_pose(self, pose_in_dock_frame: PoseStamped) -> bool:
        """Navigate to the staging pose.

        Args:
            pose_in_dock_frame (PoseStamped): The staging pose to navigate to, expressed in the dock frame.

        Returns:
            bool: True if the staging pose was reached successfully, False otherwise.
        """
        pose_in_map_frame = PoseStamped()
        pose_in_map_frame.header.frame_id = "map"
        while True:
            if not self.transform_pose(pose_in_dock_frame, pose_in_map_frame):
                return False

            self.basic_navigator.goToPose(pose_in_map_frame)
            if self.basic_navigator.isTaskComplete():
                break
            while not self.basic_navigator.isTaskComplete():
                if self.canceled:
                    self.basic_navigator.cancelTask()
                    return False
                self.logger.info("Navigating to staging pose...")
                time.sleep(1)
        task_result: TaskResult = self.basic_navigator.getResult()
        if task_result != TaskResult.SUCCEEDED:
            self.logger.error("Failed to reach staging pose.")
        return task_result == TaskResult.SUCCEEDED

    def perform_docking_maneuver(self, pose_in_dock_frame: PoseStamped) -> bool:
        """Perform the docking maneuver.

        Args:
            pose_in_dock_frame (PoseStamped): The docking pose, expressed in the dock frame.

        Returns:
            bool: True if the docking maneuver was successful, False otherwise.
        """
        pose_in_map_frame = PoseStamped()
        pose_in_map_frame.header.frame_id = "map"
        if not self.transform_pose(pose_in_dock_frame, pose_in_map_frame):
            return False
        self.basic_navigator.dockRobotByPose(
            pose_in_map_frame, "charging_dock", nav_to_dock=False
        )
        while not self.basic_navigator.isTaskComplete():
            if self.canceled:
                self.basic_navigator.cancelTask()
                return False
            self.logger.info("Docking...")
            time.sleep(1)
        task_result: TaskResult = self.basic_navigator.getResult()
        return task_result == TaskResult.SUCCEEDED

    def transform_pose(self, pose_in: PoseStamped, pose_out: PoseStamped) -> bool:
        """Transform a pose to another frame.

        Args:
            pose_in (PoseStamped): The input pose to be transformed.
            pose_out (PoseStamped): The output pose with the desired target frame specified in its header.

        Returns:
            bool: True if the transformation was successful, False otherwise.
        """
        try:
            pose_out_ = self.tf_buffer.transform(pose_in, pose_out.header.frame_id)
            pose_out.header = pose_out_.header
            pose_out.pose = pose_out_.pose
            return True
        except Exception as e:
            self.logger.error(
                f"Failed to transform pose to {pose_out.header.frame_id} frame: {e}"
            )
            return False
