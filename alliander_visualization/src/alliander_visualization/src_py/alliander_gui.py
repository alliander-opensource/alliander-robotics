#!/usr/bin/env python3

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import json
import threading
from dataclasses import dataclass

import rclpy
from alliander_interfaces.srv import PoseStampedSrv, StringSrv
from alliander_utilities.config_objects import Arm, Platform, PlatformList, Vehicle
from alliander_utilities.ros_utils import spin_node
from geographic_msgs.msg import GeoPath, GeoPoseStamped
from geometry_msgs.msg import PoseStamped
from nicegui import app, events, ui
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
from std_srvs.srv import Empty, SetBool, Trigger

TIMEOUT = 3

EXAMPLE_POSE = PoseStamped()
EXAMPLE_POSE.header.frame_id = "map"
EXAMPLE_POSE.pose.position.x = 0.4
EXAMPLE_POSE.pose.position.z = 0.1

COLS = 2  # Number of columns in the UI and maximum number of platforms to control
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

    def lat(self) -> float:
        """Get the latitude of the waypoint.

        Returns:
            float: The latitude.
        """
        return self.marker.latlng[0]

    def lng(self) -> float:
        """Get the longitude of the waypoint.

        Returns:
            float: The longitude.
        """
        return self.marker.latlng[1]

    def lat_str(self) -> str:
        """Get the latitude string of the waypoint.

        Returns:
            str: The latitude string.
        """
        return f"{round(self.lat(), 5)}"

    def lng_str(self) -> str:
        """Get the longitude string of the waypoint.

        Returns:
            str: The longitude string.
        """
        return f"{round(self.lng(), 5)}"


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

        self.ui = UserInterface(self)
        connected = 0
        controllers: list[ArmControl | VehicleControl | None] = [None, None, None]
        for platform in platform_list.platforms:
            if connected == COLS:
                self.get_logger().warn(
                    f"Maximum number of platforms to control is {COLS}. Extra platforms will be ignored."
                )
            match platform.platform_type:
                case "Arm":
                    controller = ArmControl(self, platform.namespace)
                case "Vehicle":
                    controller = VehicleControl(self, platform, self.ui)
                case _:
                    continue
            controllers[connected] = controller
            connected += 1

        self.ui.load_controllers(controllers)


class ArmControl:
    """Contains the arm control functions."""

    def __init__(self, node: UserInterfaceNode, namespace: str):
        """Initialize the arm control.

        Args:
            node (UserInterfaceNode): The main UI node.
            namespace (str): The namespace of the arm platform.
        """
        self.node: Node = node
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

    def __init__(
        self, node: UserInterfaceNode, platform: Platform, ui: "UserInterface"
    ):
        """Initialize the vehicle control.

        Args:
            node (UserInterfaceNode): The main UI node.
            platform (Platform): The vehicle platform.
            ui (UserInterface): The user interface instance.
        """
        self.node: Node = node
        self.namespace = platform.namespace
        self.ui = ui
        self.connect_vehicle()

        for child in platform.childs:
            if child.platform_type == "GPS":
                node.create_subscription(
                    NavSatFix, f"/{child.namespace}/gps/fix", self.update_position, 10
                )

    def connect_vehicle(self) -> None:
        """Connected with vehicle-related topics, services, and actions."""
        self.stop_navigation_client = self.node.create_client(
            Trigger, f"/{self.namespace}/nav2_manager/stop"
        )
        self.gps_waypoints_publisher = self.node.create_publisher(
            GeoPath, "/gps_waypoints", 10
        )

    def start_navigation(self, waypoints: list[Waypoint]) -> None:
        """Start vehicle navigation.

        Args:
            waypoints (list[Waypoint]): The list of waypoints to navigate to.
        """
        goal = GeoPath()
        for waypoint in waypoints:
            geo_pose_stamped = GeoPoseStamped()
            geo_pose_stamped.pose.position.latitude = waypoint.lat()
            geo_pose_stamped.pose.position.longitude = waypoint.lng()
            goal.poses.append(geo_pose_stamped)
        self.gps_waypoints_publisher.publish(goal)

    def stop_navigation(self) -> None:
        """Stop vehicle navigation."""
        self.stop_navigation_client.call(Trigger.Request(), TIMEOUT)

    def update_position(self, msg: NavSatFix) -> None:
        """Update the vehicle position on the map.

        Args:
            msg (NavSatFix): The ROS message containing the GPS location.
        """
        if not self.ui.leaflet or not self.ui.leaflet.is_initialized:
            return
        if self.ui.vehicle_marker is None:
            marker = ui.leaflet.marker(latlng=(msg.latitude, msg.longitude))
            self.ui.set_marker(marker, "red")
            self.ui.vehicle_marker = marker
        else:
            self.ui.vehicle_marker.move(msg.latitude, msg.longitude)


class UserInterface:
    """Defines the user interface."""

    def __init__(self, node: UserInterfaceNode):
        """Initialize the UI.

        Args:
            node (UserInterfaceNode): The main UI node.
        """
        self.node = node
        self.leaflet: ui.leaflet | None = None
        self.grid: ui.aggrid
        self.selection_marker: ui.leaflet.marker | None = None
        self.vehicle_marker: ui.leaflet.marker | None = None
        self.waypoints: dict[int, Waypoint] = {}

    def load_controllers(
        self, controllers: list[ArmControl | VehicleControl | None]
    ) -> None:
        """Load the controllers into the UI.

        Args:
            controllers (list[ArmControl | VehicleControl | None]): The list of controllers to load.
        """

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
                        ui.button(
                            "Start",
                            on_click=lambda: vehicle_control.start_navigation(
                                self.waypoints_ordered
                            ),
                        )
                        ui.button("Stop", on_click=vehicle_control.stop_navigation)

                with ui.card().classes("items-center w-full"):
                    ui.label("Waypoints").classes("text-lg")

                    self.grid = ui.aggrid(
                        {
                            "columnDefs": [
                                {"headerName": "#", "field": "order", "rowDrag": True},
                                {"headerName": "lat", "field": "lat"},
                                {"headerName": "lng", "field": "lng"},
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
                        ui.button("Save", on_click=self.save)
                        ui.button("Load", on_click=self.load)

    async def leaflet_ui(self) -> None:
        """Setup the leaflet map UI."""
        self.leaflet = ui.leaflet(center=CENTER_DEFAULT, zoom=19).classes(
            "w-full h-full"
        )
        self.leaflet.clear_layers()
        self.leaflet.tile_layer(
            url_template=r"https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
            options={"maxZoom": 30, "maxNativeZoom": 19},
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

        if not self.selection_marker:
            self.selection_marker = ui.leaflet.marker(latlng=(lat, lng))
        else:
            self.selection_marker.move(lat, lng)

    def clear_selection_marker(self) -> None:
        """Clear the current selection marker."""
        if self.selection_marker and self.leaflet:
            self.leaflet.remove_layer(self.selection_marker)
            self.selection_marker = None

    @staticmethod
    def set_marker(
        marker: ui.leaflet.marker, color: str, number: int | None = None
    ) -> None:
        """Set the marker icon based on color and number.

        Args:
            marker (ui.leaflet.marker): The marker to set the icon for.
            color (str): The color of the marker.
            number (int | None): The number on the marker.
        """
        if number is not None:
            url = f"https://raw.githubusercontent.com/sheiun/leaflet-color-number-markers/main/dist/img/{color}/marker-icon-2x-{color}-{number}.png"
        else:
            url = f"https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-{color}.png"
        icon = f"L.icon({{iconUrl: '{url}'}})"
        marker.run_method(":setIcon", icon)

    def add(self) -> None:
        """Add a waypoint at the current marker position."""
        if not self.selection_marker:
            return
        self.add_waypoint(self.selection_marker.latlng)
        self.clear_selection_marker()

    def add_waypoint(self, latlng: tuple[float, float]) -> None:
        """Add a waypoint at the specified latitude and longitude.

        Args:
            latlng (tuple[float, float]): The latitude and longitude of the waypoint.
        """
        marker = ui.leaflet.marker(latlng=latlng)
        waypoint = Waypoint(marker)
        waypoint.order = len(self.waypoints)

        self.waypoints[waypoint.id] = waypoint
        self.update()

    async def remove(self) -> None:
        """Remove all selected waypoints."""
        selected_rows = await self.grid.get_selected_rows()
        for row in selected_rows:
            if self.leaflet:
                self.leaflet.remove_layer(self.waypoints[row["id"]].marker)
                self.waypoints.pop(row["id"])
        self.update()

    def save(self) -> None:
        """Save the current waypoints to a JSON file."""

        def save() -> None:
            data = {"waypoints": []}
            for waypoint in self.waypoints_ordered:
                data["waypoints"].append((waypoint.lat(), waypoint.lng()))
            try:
                ui.download.content(json.dumps(data), filename.value)
                ui.notify("Waypoints Saved.", type="positive")
            except Exception as e:
                ui.notify(f"Failed to save waypoints: {e}", type="negative")
            dialog.close()

        with ui.dialog() as dialog, ui.card():
            ui.label("Save as...")
            filename = ui.input("filename", value="waypoints.json")
            ui.button("Save", on_click=save)
        dialog.open()

    def load(self) -> None:
        """Load waypoints from a JSON file."""

        async def load(upload_event: events.UploadEventArguments) -> None:
            try:
                data = await upload_event.file.json()
                for latlng in data["waypoints"]:
                    self.add_waypoint(latlng)
                ui.notify("Waypoints Loaded.", type="positive")
            except Exception as e:
                ui.notify(f"Failed to load waypoints: {e}", type="negative")
            dialog.close()

        with ui.dialog() as dialog, ui.card():
            ui.upload(on_upload=load)
        dialog.open()

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
        # Fill gaps for possibly removed waypoints:
        for index, waypoint in enumerate(self.waypoints_ordered):
            if waypoint.order != index:
                waypoint.order = index
            self.set_marker(waypoint.marker, "grey", waypoint.order)

        # Update grid ui:
        self.grid.options["rowData"] = [
            {"order": wp.order, "lat": wp.lat_str(), "lng": wp.lng(), "id": wp.id}
            for wp in self.waypoints_ordered
        ]

    @property
    def waypoints_ordered(self) -> list[Waypoint]:
        """Get the waypoints ordered.

        Returns:
            list[Waypoint]: The ordered list of waypoints.
        """
        return sorted(self.waypoints.values(), key=lambda wp: wp.order)


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
