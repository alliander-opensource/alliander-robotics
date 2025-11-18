#!/usr/bin/env python3

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import threading

import rclpy
from geometry_msgs.msg import PoseStamped
from nicegui import app, ui
from rcdt_interfaces.srv import MoveToConfiguration, PoseStampedSrv
from rcdt_utilities.ros_utils import spin_node
from rclpy.node import Node
from std_srvs.srv import Empty, SetBool, Trigger

TIMEOUT = 3

EXAMPLE_POSE = PoseStamped()
EXAMPLE_POSE.header.frame_id = "map"
EXAMPLE_POSE.pose.position.x = 0.4
EXAMPLE_POSE.pose.position.z = 0.1
EXAMPLE_POSE.pose.orientation.x = 1.0
EXAMPLE_POSE.pose.orientation.w = 0.0


class UI(Node):
    """Node of the UI."""

    def __init__(self):
        """Initialize the node."""
        super().__init__("simple_gui")
        self.declare_parameter("namespace", "")
        self.namespace = (
            self.get_parameter("namespace").get_parameter_value().string_value
        )
        if not self.namespace:
            self.get_logger().error("Namespace parameter is not set.")
            return
        self.create_clients()
        self.setup_gui()

    def create_clients(self) -> None:
        """Create the service clients."""
        self.move_to_configuration_client = self.create_client(
            MoveToConfiguration,
            f"/{self.namespace}/moveit_manager/move_to_configuration",
        )
        self.toggle_octomap_scan_client = self.create_client(
            SetBool, f"/{self.namespace}/moveit_manager/toggle_octomap_scan"
        )
        self.clear_octomap_client = self.create_client(
            Empty, f"/{self.namespace}/clear_octomap"
        )
        self.visualize_grasp_pose_client = self.create_client(
            PoseStampedSrv, f"/{self.namespace}/moveit_manager/visualize_grasp_pose"
        )
        self.create_plan_client = self.create_client(
            PoseStampedSrv, f"/{self.namespace}/moveit_manager/create_plan"
        )
        self.visualize_plan_client = self.create_client(
            Trigger, f"/{self.namespace}/moveit_manager/visualize_plan"
        )
        self.execute_plan_client = self.create_client(
            Trigger, f"/{self.namespace}/moveit_manager/execute_plan"
        )

    def setup_gui(self) -> None:
        """Setup the GUI pages."""

        @ui.page("/")
        def page() -> None:
            """Setup the page of the GUI."""
            with ui.card().classes("items-center"):
                ui.label("Arm").classes("text-xl ")
                with ui.card().classes("items-center full-width"):
                    ui.label("Basic Control").classes("text-lg")
                    with ui.row():
                        ui.button("Home", on_click=self.home)
                with ui.card().classes("items-center full-width"):
                    ui.label("Octomap Scan").classes("text-lg")
                    with ui.row():
                        ui.button(
                            "Start", on_click=lambda: self.toggle_octomap_scan(True)
                        )
                        ui.button(
                            "Stop", on_click=lambda: self.toggle_octomap_scan(False)
                        )
                        ui.button("Clear", on_click=self.clear_octomap)
                with ui.card().classes("items-center full-width"):
                    ui.label("Grasp Pose").classes("text-lg")
                    ui.button("Visualize", on_click=self.visualize_grasp_pose)
                with ui.card().classes("items-center full-width"):
                    ui.label("End-effector Plan").classes("text-lg")
                    with ui.row():
                        ui.button("Create", on_click=self.create_plan)
                        ui.button("Visualize", on_click=self.visualize_plan)
                        ui.button("Execute", on_click=self.execute_plan)

    def home(self) -> None:
        """Move the robot to the home configuration."""
        request = MoveToConfiguration.Request()
        request.configuration = "home"
        if self.move_to_configuration_client.call(request, TIMEOUT) is None:
            self.get_logger().error("Failed to call move to configuration service.")
        else:
            self.get_logger().info("Successfully called move to configuration service.")

    def toggle_octomap_scan(self, enable: bool) -> None:
        """Enable or disable octomap scanning.

        Args:
            enable (bool): True to enable scanning, False to disable.
        """
        request = SetBool.Request()
        request.data = enable

        if self.toggle_octomap_scan_client.call(request, TIMEOUT) is None:
            self.get_logger().error("Failed to call toggle octomap scan service.")
        else:
            self.get_logger().info("Successfully called toggle octomap scan service.")

    def clear_octomap(self) -> None:
        """Clear the octomap."""
        if self.clear_octomap_client.call(Empty.Request(), TIMEOUT) is None:
            self.get_logger().error("Failed to call clear octomap service.")
        else:
            self.get_logger().info("Successfully called clear octomap service.")

    def visualize_grasp_pose(self) -> None:
        """Visualize the grasp pose in Rviz."""
        request = PoseStampedSrv.Request()
        request.pose = EXAMPLE_POSE
        if self.visualize_grasp_pose_client.call(request, TIMEOUT) is None:
            self.get_logger().error("Failed to call visualize gripper pose service.")
        else:
            self.get_logger().info(
                "Successfully called visualize gripper pose service."
            )

    def visualize_plan(self) -> None:
        """Visualize the plan in Rviz."""
        if self.visualize_plan_client.call(Trigger.Request(), TIMEOUT) is None:
            self.get_logger().error("Failed to call visualize plan service.")
        else:
            self.get_logger().info("Successfully called visualize plan service.")

    def create_plan(self) -> None:
        """Create a plan to reach the grasp pose."""
        request = PoseStampedSrv.Request()
        request.pose = EXAMPLE_POSE
        if self.create_plan_client.call(request, TIMEOUT) is None:
            self.get_logger().error("Failed to call create plan service.")
        else:
            self.get_logger().info("Successfully called create plan service.")

    def execute_plan(self) -> None:
        """Execute the plan."""
        if self.execute_plan_client.call(Trigger.Request(), TIMEOUT) is None:
            self.get_logger().error("Failed to call execute plan service.")
        else:
            self.get_logger().info("Successfully called execute plan service.")


def ros_main(args: list | None = None) -> None:
    """Main function to initialize the ROS 2 node and start the executor.

    Args:
        args (list | None): Command line arguments, defaults to None.
    """
    rclpy.init(args=args)
    node = UI()
    spin_node(node)


app.on_startup(lambda: threading.Thread(target=ros_main).start())
ui.run()
