# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Literal

from launch_ros.actions import Node
from rcdt_launch.environment_configuration import EnvironmentConfiguration
from rcdt_launch.platforms.camera import Camera
from rcdt_launch.platforms.gps import GPS
from rcdt_launch.platforms.lidar import Lidar
from rcdt_launch.platforms.platform import Platform
from rcdt_launch.rviz import Rviz
from rcdt_launch.vizanti import Vizanti
from rcdt_utilities.register import RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path


class Vehicle(Platform):
    """Extension on Platform with vehicle specific functionalities.

    Attributes:
        SUPPORTED_PLATFORMS: The supported platforms.
    """

    SUPPORTED_PLATFORMS = Literal["panther"]

    def __init__(  # noqa: PLR0913
        self,
        platform: SUPPORTED_PLATFORMS,
        position: list,
        orientation: list | None = None,
        namespace: str | None = None,
        parent: Platform | None = None,
        parent_link: str = "",
        navigation: bool = False,
        use_gps: bool = False,
        slam: bool = False,
        collision_monitor: bool = False,
        window_size: int = 10,
    ):
        """Initialize the Vehicle platform.

        Args:
            platform (SUPPORTED_PLATFORMS): The platform type.
            position (list): The position of the vehicle.
            orientation (list | None): The initial orientation of the vehicle.
            namespace (str | None): The namespace of the vehicle.
            parent (Platform | None): The parent platform.
            parent_link (str): The link of the parent to which the platform is attached. If empty, the base_link of the parent is used.
            navigation (bool): Whether to start navigation for the vehicle.
            use_gps (bool): Whether to use GPS to navigate the vehicle.
            slam (bool): Whether to start SLAM for the vehicle.
            collision_monitor (bool): Whether to start the collision monitor for the vehicle.
            window_size (int): The window size for navigation.
        """
        super().__init__(
            platform, position, orientation, namespace, parent, parent_link
        )
        self.platform_type = platform
        self.namespace = self.namespace
        self.navigation = navigation
        self.use_gps = use_gps
        self.slam = slam
        self.collision_monitor = collision_monitor
        self.window_size = window_size

        self.lidar: Lidar | None = None
        self.camera: Camera | None = None
        self.gps: GPS | None = None

        if platform == "panther":
            Vizanti.add_platform_model(self.namespace)
            Vizanti.add_button("Trigger", f"/{self.namespace}/hardware/e_stop_trigger")
            Vizanti.add_button("Reset", f"/{self.namespace}/hardware/e_stop_reset")
            Vizanti.add_button(
                "Estop Status",
                f"/{self.namespace}/hardware/e_stop",
                "std_msgs/msg/Bool",
            )

        if (self.navigation or self.slam) and not self.use_gps:
            Rviz.add_map(f"/{self.namespace}/map")

        if self.navigation:
            Rviz.add_map(f"/{self.namespace}/global_costmap/costmap")
            Rviz.add_path(f"/{self.namespace}/plan")
            Vizanti.add_button(
                "Stop", f"/{self.namespace}/waypoint_follower_controller/stop"
            )
            Vizanti.add_initial_pose()
            Vizanti.add_goal_pose()
            Vizanti.add_waypoints(self.namespace)
            Vizanti.add_map(
                "global_costmap", f"/{self.namespace}/global_costmap/costmap"
            )
            Vizanti.add_path(f"/{self.namespace}/plan")

        if self.use_gps:
            Rviz.set_grid_size(self.window_size)
            Rviz.set_grid_frame(f"/{self.namespace}/base_footprint")

        if self.collision_monitor:
            Rviz.add_polygon(f"/{self.namespace}/polygon_slower")
            Rviz.add_polygon(f"/{self.namespace}/velocity_polygon_stop")

    @property
    def base_link(self) -> str:  # noqa: PLR0911
        """Return the base link for the robot.

        Returns:
            str: The base link for the robot.
        """
        return "base_link"

    @property
    def controller_path(self) -> str | None:
        """Return the controller launch file path for the robot.

        Returns:
            str | None: The controller launch file path or None if not applicable.

        Raises:
            ValueError: If an unknown Vehicle platform is specified.
        """
        match self.platform_type:
            case "panther":
                package = "rcdt_panther"
            case _:
                raise ValueError(f"Unknown Vehicle platform: {self.platform_type}")

        return get_file_path(package, ["launch"], "controllers.launch.py")

    @property
    def default_connect_link(self) -> str:
        """Return the default link to which child platforms should connect.

        Returns:
            str: The default connection link for the vehicle.

        Raises:
            ValueError: If the Vehicle platform is unknown.
        """
        match self.platform_type:
            case "panther":
                return "base_link"
            case _:
                raise ValueError(
                    "Unable to provide default connection link: Unknown Vehicle platform."
                )

    @property
    def xacro_path(self) -> str:  # noqa: PLR0911
        """Return the xacro file path for the robot.

        Returns:
            str: The xacro file path for the robot.

        Raises:
            ValueError: If the platform is unknown.
        """
        match self.platform_type:
            case "panther":
                return get_file_path("rcdt_panther", ["urdf"], "panther.urdf.xacro")
            case _:
                raise ValueError("Cannot provide xacro path: unknown Vehicle platform.")

    def create_launch_description(self) -> list[RegisteredLaunchDescription]:
        """Create the launch description with specific elements for a vehicle.

        Returns:
            list[RegisteredLaunchDescription]: The launch description for the platform.
        """
        launch_descriptions = []
        if self.navigation or self.collision_monitor or self.slam:
            launch_descriptions.append(self.create_nav2_launch())
        return launch_descriptions

    def create_map_link(self) -> Node | None:
        """Create a static_transform_publisher node that links the platform to the map.

        If the platform is a Vehicle that is using SLAM or navigation, None is returned.
        In this case, a localization node will make the link to the 'map' frame.
        If a vehicle is not using SLAM or navigation, the 'odom' frame is directly linked to the 'map' frame.

        Returns:
            Node | None: A static_transform_publisher node that links the platform with the world or None if not applicable.
        """
        if self.navigation or self.slam or self.use_gps:
            return None
        child_frame = f"{self.namespace}/odom"

        return Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="static_tf_world",
            arguments=[
                "--frame-id",
                "map",
                "--child-frame-id",
                child_frame,
                "--x",
                f"{self.position[0]}",
                "--y",
                f"{self.position[1]}",
                "--z",
                f"{self.position[2]}",
                "--roll",
                f"{self.orientation[0]}",
                "--pitch",
                f"{self.orientation[1]}",
                "--yaw",
                f"{self.orientation[2]}",
            ],
        )

    def create_nav2_launch(self) -> RegisteredLaunchDescription:
        """Create the Nav2 launch description.

        Returns:
            RegisteredLaunchDescription: The launch description for the Nav2.

        Raises:
            ValueError: If no lidar is attached to the vehicle.
        """
        if not self.lidar:
            raise ValueError("A lidar is required for use of nav2.")

        return RegisteredLaunchDescription(
            get_file_path("rcdt_panther", ["launch"], "nav2.launch.py"),
            launch_arguments={
                "simulation": str(EnvironmentConfiguration.simulation),
                "slam": str(self.slam),
                "collision_monitor": str(self.collision_monitor),
                "navigation": str(self.navigation),
                "namespace_vehicle": self.namespace,
                "namespace_lidar": self.lidar.namespace,
                "namespace_gps": self.gps.namespace if self.gps else "",
                "use_gps": str(self.use_gps),
                "window_size": str(self.window_size),
            },
        )

    def create_state_publisher(self) -> Node | None:
        """Create a state publisher node for the robot.

        Returns:
            Node | None: The state publisher node for the robot or None if not applicable.
        """
        if not EnvironmentConfiguration.simulation:
            return None

        return Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            namespace=self.namespace,
            parameters=[
                self.robot_description,
                {"frame_prefix": self.frame_prefix},
                {"publish_frequency": 1000.0},
            ],
        )

    def joystick_nodes(self) -> list[Node]:
        """Return the required nodes to control the platform with a joystick.

        Returns:
            list[Node]: The joystick nodes for the platform.
        """
        nodes: list[Node] = []

        pub_topic = f"/{self.namespace}/cmd_vel"
        if self.collision_monitor:
            pub_topic += "_raw"
        if self.platform_type == "panther":
            nodes.append(
                Node(
                    package="rcdt_joystick",
                    executable="joy_to_twist.py",
                    parameters=[
                        {"sub_topic": f"/{self.namespace}/joy"},
                        {"pub_topic": pub_topic},
                        {"config_pkg": "rcdt_panther"},
                    ],
                    namespace=self.namespace,
                )
            )

        return nodes
