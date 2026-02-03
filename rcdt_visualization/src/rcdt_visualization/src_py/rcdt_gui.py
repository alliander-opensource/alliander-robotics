#!/usr/bin/env python3

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import threading
from dataclasses import dataclass

import rclpy
from geographic_msgs.msg import GeoPath, GeoPoseStamped
from geometry_msgs.msg import PoseStamped
from nicegui import app, events, ui
from rcdt_interfaces.srv import PoseStampedSrv, StringSrv
from rcdt_utilities.config_objects import Arm, PlatformList, Vehicle
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
CENTER_DEFAULT = (51.966960, 5.940906)  # Default map center (latitude, longitude)


@dataclass
class Waypoint:
    """Contains the marker and order of a waypoint.

    Attributes:
        marker (ui.leaflet.marker): The marker of the waypoint.
        id (int): The unique ID of the waypoint.
        order (int): The order of the waypoint.
    """

    marker: ui.leaflet.marker
    id: int = 0
    order: int = 0

    def __post_init__(self):
        """Initialize the waypoint ID."""
        Waypoint.id += 1
        self.id = Waypoint.id

    def lat(self) -> str:
        """Get the latitude string of the waypoint.

        Returns:
            str: The latitude string.
        """
        return f"{round(self.marker.latlng[0], 5)}"

    def long(self) -> str:
        """Get the longitude string of the waypoint.

        Returns:
            str: The longitude string.
        """
        return f"{round(self.marker.latlng[1], 5)}"


class UserInterfaceNode(Node):
    """Node of the UI."""

    def __init__(self):
        """Initialize the node."""
        super().__init__("graphical_user_interface")
        self.declare_parameter("platform_list", "")
        platform_list_json = (
            self.get_parameter("platform_list").get_parameter_value().string_value
        )
        if not platform_list_json:
            platform_list = PlatformList()
            platform_list.platforms.append(Vehicle("mock"))
            platform_list.platforms.append(Arm("mock"))
        else:
            platform_list = PlatformList.from_str(platform_list_json)

        connected = 0
        controllers = 3 * [None]
        for platform in platform_list.platforms:
            if connected == COLS:
                self.get_logger().warn(
                    f"Maximum number of platforms to control is {COLS}. Extra platforms will be ignored."
                )
            match platform.platform_type:
                case "Arm":
                    controller = ArmControl(self, platform.namespace)
                case "Vehicle":
                    controller = VehicleControl(self, platform.namespace)
                case _:
                    continue
            controllers[connected] = controller
            connected += 1

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
            StringSrv, f"/{namespace}/moveit_manager/move_to_configuration"
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
        request = StringSrv.Request()
        request.text = configuration
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
        self.waypoints = GeoPath()
        self.connect_vehicle(namespace)

    def add_waypoint(self, latlng: tuple[float, float]) -> None:
        """Add currently selected waypoint to the waypoint list.

        Args:
            latlng (tuple[float, float]): Latitude and longitude to navigate to.
        """
        geo_pose_stamped = GeoPoseStamped()
        geo_pose_stamped.pose.position.latitude = latlng[0]
        geo_pose_stamped.pose.position.longitude = latlng[1]
        self.waypoints.poses.append(geo_pose_stamped)

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

    def start_navigation(self) -> None:
        """Start vehicle navigation."""
        goal = GeoPath()
        geo_pose_stamped = GeoPoseStamped()
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
        self.leaflet: ui.leaflet
        self.grid: ui.aggrid
        self.marker: ui.leaflet.marker | None = None
        self.waypoints: dict[int, Waypoint] = {}

        @ui.page("/")
        async def page() -> None:
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
                        await self.leaflet_ui()

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
                        ui.button("Start", on_click=vehicle_control.start_navigation)
                        ui.button("Stop", on_click=vehicle_control.stop_navigation)

                with ui.card().classes("items-center w-full"):
                    ui.label("Waypoints").classes("text-lg")

                    self.grid = ui.aggrid(
                        {
                            "columnDefs": [
                                {"headerName": "#", "field": "order", "rowDrag": True},
                                {"headerName": "lat", "field": "lat"},
                                {"headerName": "long", "field": "long"},
                                {"headerName": "id", "field": "id", "hide": True},
                            ],
                            "rowData": [],
                            "rowDragManaged": True,
                            "animateRows": True,
                            "rowSelection": {"mode": "multiRow"},
                        },
                    )
                    self.waypoints = {}
                    self.grid.on("rowDragEnd", self.change_order)

                    with ui.row():
                        ui.button("Add", on_click=self.add)
                        ui.button("Remove", on_click=self.remove)

    async def leaflet_ui(self) -> None:
        """Setup the leaflet map UI."""
        self.leaflet = ui.leaflet(center=CENTER_DEFAULT, zoom=19).classes(
            "w-full h-full"
        )
        self.leaflet.on("map-click", self.place_selection_marker)
        self.leaflet.on("contextmenu.prevent", self.clear_selection_marker)
        await self.leaflet.initialized()

    def place_selection_marker(self, e: events.GenericEventArguments) -> None:
        """Handle map click events to place or move the selection marker.

        Args:
            e (events.GenericEventArguments): The event arguments.
        """
        lat = e.args["latlng"]["lat"]
        lng = e.args["latlng"]["lng"]

        if not self.marker:
            self.marker = ui.leaflet.marker(latlng=(lat, lng))
        else:
            self.marker.move(lat, lng)

    def clear_selection_marker(self) -> None:
        """Clear the current selection marker."""
        if self.marker:
            self.leaflet.remove_layer(self.marker)
            self.marker = None

    @staticmethod
    def set_marker(marker: ui.leaflet.marker, color: str, number: int) -> None:
        """Set the marker icon based on color and number.

        Args:
            marker (ui.leaflet.marker): The marker to set the icon for.
            color (str): The color of the marker.
            number (int): The number on the marker.
        """
        url = f"https://raw.githubusercontent.com/sheiun/leaflet-color-number-markers/main/dist/img/{color}/marker-icon-2x-{color}-{number}.png"
        icon = f"L.icon({{iconUrl: '{url}'}})"
        marker.run_method(":setIcon", icon)

    def add(self) -> None:
        """Add a waypoint at the current marker position."""
        if not self.marker:
            return
        marker = ui.leaflet.marker(latlng=self.marker.latlng)
        waypoint = Waypoint(marker)
        waypoint.order = len(self.waypoints)

        self.waypoints[waypoint.id] = waypoint
        self.clear_selection_marker()
        self.update()

    async def remove(self) -> None:
        """Remove all selected waypoints."""
        selected_rows = await self.grid.get_selected_rows()
        for row in selected_rows:
            self.leaflet.remove_layer(self.waypoints[row["id"]].marker)
            self.waypoints.pop(row["id"])
        self.update()

    async def change_order(self) -> None:
        """Change the order of the waypoints after a drag-and-drop action."""
        for n in range(len(self.grid.options["rowData"])):
            row_data = await self.grid.run_grid_method(
                f"g => g.getDisplayedRowAtIndex({n}).data"
            )
            row_id = row_data["id"]
            self.waypoints[row_id].order = n
        self.update()

    def update(self) -> None:
        """Update the waypoints after a change was made."""
        ordered_waypoints = sorted(self.waypoints.values(), key=lambda wp: wp.order)

        # Fill gaps for possibly removed waypoints:
        for index, waypoint in enumerate(ordered_waypoints):
            if waypoint.order != index:
                waypoint.order = index
            self.set_marker(waypoint.marker, "red", waypoint.order)

        # Update grid ui:
        self.grid.options["rowData"] = [
            {"order": wp.order, "lat": wp.lat(), "long": wp.long(), "id": wp.id}
            for wp in ordered_waypoints
        ]


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
