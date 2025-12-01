#!/usr/bin/env python3

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import ast
import contextlib
import threading

import rclpy
from geographic_msgs.msg import GeoPath, GeoPoseStamped
from geometry_msgs.msg import PoseStamped
from nicegui import app, events, ui
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

COLS = 3  # Number of columns in the UI and maximum number of platforms to control


class UserInterfaceNode(Node):
    """Node of the UI."""

    def __init__(self):
        """Initialize the node."""
        super().__init__("graphical_user_interface")
        self.declare_parameter("platforms", "")
        platforms = self.get_parameter("platforms").get_parameter_value().string_value
        platforms_dict: dict | None = None
        with contextlib.suppress(ValueError):
            platforms_dict = ast.literal_eval(platforms)

        connected = 0
        controllers = 3 * [None]
        if isinstance(platforms_dict, dict):
            for namespace, platform_type in platforms_dict.items():
                if connected == COLS:
                    self.get_logger().warn(
                        f"Maximum number of platforms to control is {COLS}. Extra platforms will be ignored."
                    )
                match platform_type:
                    case "Arm":
                        controller = ArmControl(self, namespace)
                    case "Vehicle":
                        controller = VehicleControl(self, namespace)
                    case _:
                        continue
                controllers[connected] = controller
                connected += 1
        else:
            self.get_logger().warn(
                "Failed to parse platforms parameter as dictionary, so no platforms will be connected."
            )

        self.ui = UserInterface(self, controllers)


class ArmControl:
    """Contains the arm control functions."""

    def __init__(self, node: UserInterfaceNode, namespace: str):
        """Initialize the arm control.

        Args:
            node (UserInterfaceNode): The main UI node.
            namespace (str): The namespace of the arm platform.
        """
        self.node = node
        self.namespace = namespace
        self.connect_arm(namespace)

    def connect_arm(self, namespace: str) -> None:
        """Connected with arm-related topics, services, and actions.

        Args:
            namespace (str): The namespace of the arm platform.
        """
        self.move_to_configuration_client = self.node.create_client(
            MoveToConfiguration, f"/{namespace}/moveit_manager/move_to_configuration"
        )
        self.toggle_octomap_scan_client = self.node.create_client(
            SetBool, f"/{namespace}/moveit_manager/toggle_octomap_scan"
        )
        self.clear_octomap_client = self.node.create_client(
            Empty, f"/{namespace}/clear_octomap"
        )
        self.visualize_grasp_pose_client = self.node.create_client(
            PoseStampedSrv, f"/{namespace}/moveit_manager/visualize_grasp_pose"
        )
        self.create_plan_client = self.node.create_client(
            PoseStampedSrv, f"/{namespace}/moveit_manager/create_plan"
        )
        self.visualize_plan_client = self.node.create_client(
            Trigger, f"/{namespace}/moveit_manager/visualize_plan"
        )
        self.execute_plan_client = self.node.create_client(
            Trigger, f"/{namespace}/moveit_manager/execute_plan"
        )

    def move(self, configuration: str) -> None:
        """Move the robot to the specified configuration.

        Args:
            configuration (str): The target configuration.
        """
        request = MoveToConfiguration.Request()
        request.configuration = configuration
        if self.move_to_configuration_client.call(request, TIMEOUT) is None:
            self.node.get_logger().error(
                "Failed to call move to configuration service."
            )
        else:
            self.node.get_logger().info(
                "Successfully called move to configuration service."
            )

    def toggle_octomap_scan(self, enable: bool) -> None:
        """Enable or disable octomap scanning.

        Args:
            enable (bool): True to enable scanning, False to disable.
        """
        request = SetBool.Request()
        request.data = enable

        if self.toggle_octomap_scan_client.call(request, TIMEOUT) is None:
            self.node.get_logger().error("Failed to call toggle octomap scan service.")
        else:
            self.node.get_logger().info(
                "Successfully called toggle octomap scan service."
            )

    def clear_octomap(self) -> None:
        """Clear the octomap."""
        if self.clear_octomap_client.call(Empty.Request(), TIMEOUT) is None:
            self.node.get_logger().error("Failed to call clear octomap service.")
        else:
            self.node.get_logger().info("Successfully called clear octomap service.")

    def visualize_grasp_pose(self) -> None:
        """Visualize the grasp pose in Rviz."""
        request = PoseStampedSrv.Request()
        request.pose = EXAMPLE_POSE
        if self.visualize_grasp_pose_client.call(request, TIMEOUT) is None:
            self.node.get_logger().error(
                "Failed to call visualize gripper pose service."
            )
        else:
            self.node.get_logger().info(
                "Successfully called visualize gripper pose service."
            )

    def visualize_plan(self) -> None:
        """Visualize the plan in Rviz."""
        if self.visualize_plan_client.call(Trigger.Request(), TIMEOUT) is None:
            self.node.get_logger().error("Failed to call visualize plan service.")
        else:
            self.node.get_logger().info("Successfully called visualize plan service.")

    def create_plan(self) -> None:
        """Create a plan to reach the grasp pose."""
        request = PoseStampedSrv.Request()
        request.pose = EXAMPLE_POSE
        if self.create_plan_client.call(request, TIMEOUT) is None:
            self.node.get_logger().error("Failed to call create plan service.")
        else:
            self.node.get_logger().info("Successfully called create plan service.")

    def execute_plan(self) -> None:
        """Execute the plan."""
        if self.execute_plan_client.call(Trigger.Request(), TIMEOUT) is None:
            self.node.get_logger().error("Failed to call execute plan service.")
        else:
            self.node.get_logger().info("Successfully called execute plan service.")


class VehicleControl:
    """Contains the vehicle control functions."""

    def __init__(self, node: UserInterfaceNode, namespace: str):
        """Initialize the vehicle control.

        Args:
            node (UserInterfaceNode): The main UI node.
            namespace (str): The namespace of the vehicle platform.
        """
        self.node = node
        self.namespace = namespace
        self.connect_vehicle(namespace)

    def connect_vehicle(self, namespace: str) -> None:
        """Connected with vehicle-related topics, services, and actions.

        Args:
            namespace (str): The namespace of the vehicle platform.
        """
        self.stop_navigation_client = self.node.create_client(
            Trigger, f"/{namespace}/nav2_manager/stop"
        )
        self.gps_waypoints_publisher = self.node.create_publisher(
            GeoPath, "/gps_waypoints", 10
        )
        self.stop_navigation_client = self.node.create_client(
            Trigger, "/panther1/nav2_manager/stop"
        )

    def start_navigation(self, latlng: tuple[float, float]) -> None:
        """Start vehicle navigation.

        Args:
            latlng (tuple[float, float]): Latitude and longitude to navigate to.
        """
        goal = GeoPath()
        geo_pose_stamped = GeoPoseStamped()
        geo_pose_stamped.pose.position.latitude = latlng[0]
        geo_pose_stamped.pose.position.longitude = latlng[1]
        goal.poses.append(geo_pose_stamped)
        self.gps_waypoints_publisher.publish(goal)

    def stop_navigation(self) -> None:
        """Stop vehicle navigation."""
        self.stop_navigation_client.call(Trigger.Request(), TIMEOUT)


class UserInterface:
    """Defines the user interface."""

    def __init__(self, node: UserInterfaceNode, controllers: list):
        """Initialize the UI.

        Args:
            node (UserInterfaceNode): The main UI node.
            controllers (list): List of platform controllers.
        """
        self.node = node

        @ui.page("/")
        def page() -> None:
            """Setup the page of the UI."""
            ui.query(".nicegui-content").classes("p-0")
            with ui.card().tight().classes("w-full"):  # noqa: PLR1702
                with ui.card().classes("w-full h-[50vh]"):  # noqa: SIM117
                    with ui.element("div").classes(f"columns-{COLS} w-full h-full"):
                        for controller in controllers:
                            with ui.column().classes("items-center h-full"):
                                if isinstance(controller, ArmControl):
                                    self.arm_ui(controller)
                                elif isinstance(controller, VehicleControl):
                                    self.vehicle_ui(controller)
                                else:
                                    self.not_connected_ui()
                with ui.card().tight().classes("w-full"):  # noqa: SIM117
                    with ui.card().classes("w-full h-[50vh]"):
                        self.map_ui()

    @staticmethod
    def not_connected_ui() -> None:
        """Setup the not connected UI."""
        with ui.card().classes("items-center bg-gray-100 h-full w-full"):  # noqa: SIM117
            with ui.row().classes("h-full place-content-center"):
                ui.label("Not Connected").classes("text-xl")

    @staticmethod
    def arm_ui(arm_control: ArmControl) -> None:
        """Setup the arm control UI.

        Args:
            arm_control (ArmControl): The arm control instance.
        """
        with ui.card().classes("items-center bg-gray-100 h-full w-full"):
            ui.label(f"/{arm_control.namespace}").classes("text-xl")
            with ui.scroll_area().classes("h-full"):
                with ui.card().classes("items-center w-full"):
                    ui.label("Basic Control").classes("text-lg")
                    with ui.row():
                        ui.button("Home", on_click=lambda: arm_control.move("home"))
                        ui.button("Drop", on_click=lambda: arm_control.move("drop"))
                with ui.card().classes("items-center w-full"):
                    ui.label("Octomap Scan").classes("text-lg")
                    with ui.row():
                        ui.button(
                            "Start",
                            on_click=lambda: arm_control.toggle_octomap_scan(True),
                        )
                        ui.button(
                            "Stop",
                            on_click=lambda: arm_control.toggle_octomap_scan(False),
                        )
                        ui.button("Clear", on_click=arm_control.clear_octomap)
                with ui.card().classes("items-center full-width"):
                    ui.label("Grasp Pose").classes("text-lg")
                    ui.button("Visualize", on_click=arm_control.visualize_grasp_pose)
                with ui.card().classes("items-center full-width"):
                    ui.label("End-effector Plan").classes("text-lg")
                    with ui.row():
                        ui.button("Create", on_click=arm_control.create_plan)
                        ui.button("Visualize", on_click=arm_control.visualize_plan)
                        ui.button("Execute", on_click=arm_control.execute_plan)

    def vehicle_ui(self, vehicle_control: VehicleControl) -> None:
        """Setup the vehicle control UI.

        Args:
            vehicle_control (VehicleControl): The vehicle control instance.
        """
        with ui.card().classes("items-center bg-gray-100 h-full w-full"):
            ui.label(f"/{vehicle_control.namespace}").classes("text-xl")
            with ui.scroll_area().classes("h-full"):  # noqa: SIM117
                with ui.card().classes("items-center w-full"):
                    ui.label("Navigation").classes("text-lg")
                    with ui.row():
                        ui.button(
                            "Start",
                            on_click=lambda: vehicle_control.start_navigation(
                                self.marker.latlng
                            ),
                        )
                        ui.button("Stop", on_click=vehicle_control.stop_navigation)

    def map_ui(self) -> None:
        """Setup the map control UI."""
        center_default = (51.966960, 5.940906)
        leaflet = ui.leaflet(center=center_default, zoom=19).classes("w-full h-full")
        self.marker = leaflet.marker(latlng=center_default)

        def handle_click(e: events.GenericEventArguments) -> None:
            """Handle map click events to place or move a marker.

            Args:
                e (events.GenericEventArguments): The event arguments.
            """
            lat = e.args["latlng"]["lat"]
            lng = e.args["latlng"]["lng"]
            self.marker.move(lat, lng)

        leaflet.on("map-click", handle_click)


def ros_main(args: list | None = None) -> None:
    """Main function to initialize the ROS 2 node and start the executor.

    Args:
        args (list | None): Command line arguments, defaults to None.
    """
    rclpy.init(args=args)
    node = UserInterfaceNode()
    spin_node(node)


app.on_startup(lambda: threading.Thread(target=ros_main).start())
ui.run()
