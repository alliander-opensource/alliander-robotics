# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Literal

from launch_ros.actions import Node
from rcdt_launch.environment_configuration import EnvironmentConfiguration
from rcdt_launch.moveit import Moveit
from rcdt_launch.platforms.camera import Camera
from rcdt_launch.platforms.platform import Platform
from rcdt_launch.rviz import Rviz
from rcdt_utilities.register import RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path, get_robot_description


class Arm(Platform):
    """Extension on Platform with arm specific functionalities.

    Attributes:
        SUPPORTED_PLATFORMS: The supported platforms.
    """

    SUPPORTED_PLATFORMS = Literal["franka"]

    def __init__(  # noqa: PLR0913
        self,
        platform: SUPPORTED_PLATFORMS,
        position: list,
        orientation: list | None = None,
        namespace: str | None = None,
        parent: Platform | None = None,
        parent_link: str = "",
        moveit: bool = False,
        gripper: bool = False,
        ip_address: str = "",
    ):
        """Initialize the Arm platform.

        Args:
            platform (SUPPORTED_PLATFORMS): The platform type.
            position (list): The position of the arm.
            orientation (list | None): The initial orientation of the arm.
            namespace (str | None): The namespace of the arm.
            parent (Platform | None): The parent platform.
            parent_link (str): The link of the parent to which the platform is attached. If empty, the base_link of the parent is used.
            moveit (bool): Whether to use MoveIt for the arm.
            gripper (bool): Whether to add a start the gripper services.
            ip_address (str): The IP address of the arm.
        """
        super().__init__(
            platform, position, orientation, namespace, parent, parent_link
        )
        self.platform_type = platform
        self.moveit = moveit
        self.gripper = gripper
        self.ip_address = ip_address

        self.camera: Camera | None = None

        if moveit:
            Moveit.add(self.namespace, self.robot_description, self.platform_type)
            Rviz.moveit_namespaces.append(self.namespace)
            Rviz.add_motion_planning_plugin(self.namespace)
            Rviz.add_planning_scene(self.namespace)
            Rviz.add_robot_state(self.namespace)
            Rviz.add_trajectory(self.namespace)

    @property
    def base_link(self) -> str:  # noqa: PLR0911
        """Return the base link for the robot.

        Returns:
            str: The base link for the robot.
        """
        return "fr3_link0"

    @property
    def controller_path(self) -> str | None:
        """Return the controller launch file path for the robot.

        Returns:
            str | None: The controller launch file path or None if not applicable.

        Raises:
            ValueError: If an unknown Arm platform is specified.
        """
        match self.platform_type:
            case "franka":
                package = "rcdt_franka"
            case _:
                raise ValueError(f"Unknown Arm platform: {self.platform_type}")

        return get_file_path(package, ["launch"], "controllers.launch.py")

    @property
    def default_connect_link(self) -> str:
        """Return the default link to which child platforms should connect.

        Returns:
            str: The default connection link for the arm.

        Raises:
            ValueError: If the Arm platform is unknown.
        """
        match self.platform_type:
            case "franka":
                return "fr3_hand"
            case _:
                raise ValueError(
                    "Unable to provide default connection link: Unknown Arm platform."
                )

    @property
    def robot_description(self) -> dict:
        """Return the robot description for the robot.

        Returns:
            dict: The robot description for the robot.
        """
        xacro_arguments = {
            "simulation": str(EnvironmentConfiguration.simulation),
            "namespace": self.namespace,
        }
        xacro_arguments["childs"] = str(self.childs)
        xacro_arguments["parent"] = "" if self.is_child else "world"
        if self.platform_type == "franka":
            xacro_arguments["ip_address"] = self.ip_address

        return get_robot_description(self.xacro_path, xacro_arguments)

    @property
    def xacro_path(self) -> str:  # noqa: PLR0911
        """Return the xacro file path for the robot.

        Returns:
            str: The xacro file path for the robot.

        Raises:
            ValueError: If the platform is unknown.
        """
        match self.platform_type:
            case "franka":
                return get_file_path("rcdt_franka", ["urdf"], "franka.urdf.xacro")
            case _:
                raise ValueError("Cannot provide xacro path: unknown Arm platform.")

    def create_controller(self) -> RegisteredLaunchDescription:
        """Create a controller launch description for the robot.

        Returns:
            RegisteredLaunchDescription: The controller launch description for the robot.
        """
        launch_arguments = {
            "simulation": str(EnvironmentConfiguration.simulation),
            "namespace": self.namespace,
            "ip_address": self.ip_address,
        }
        return RegisteredLaunchDescription(
            self.controller_path, launch_arguments=launch_arguments
        )

    def create_gripper_launch(self) -> RegisteredLaunchDescription | None:
        """Create the gripper services launch description.

        Returns:
            RegisteredLaunchDescription | None: The launch description for the gripper services.
        """
        if self.platform_type == "franka":
            return RegisteredLaunchDescription(
                get_file_path("rcdt_franka", ["launch"], "gripper_services.launch.py"),
                launch_arguments={"namespace": self.namespace},
            )

        return None

    def create_launch_description(self) -> list[RegisteredLaunchDescription]:
        """Create the launch description with specific elements for an arm.

        Returns:
            list[RegisteredLaunchDescription]: The launch description for the platform.
        """
        launch_descriptions = []
        if self.gripper:
            launch_descriptions.append(self.create_gripper_launch())
        if self.moveit:
            launch_descriptions.append(self.create_moveit_launch())
        return launch_descriptions

    def create_map_link(self) -> Node | None:
        """Create a static_transform_publisher node that links the platform to the map.

        Returns:
            Node | None: A static_transform_publisher node that links the platform with the world or None if not applicable.
        """
        if not EnvironmentConfiguration.simulation:
            child_frame = f"{self.namespace}/base"
        else:
            child_frame = f"{self.namespace}/world"

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

    def create_moveit_launch(self) -> RegisteredLaunchDescription:
        """Create the MoveIt launch description.

        Returns:
            RegisteredLaunchDescription: The launch description for the MoveIt.
        """
        return RegisteredLaunchDescription(
            get_file_path("rcdt_moveit", ["launch"], "moveit.launch.py"),
            launch_arguments={
                "namespace_arm": self.namespace,
                "namespace_camera": self.camera.namespace if self.camera else "",
            },
        )

    def joystick_nodes(self) -> list[Node]:
        """Return the required nodes to control the platform with a joystick.

        Returns:
            list[Node]: The joystick nodes for the platform.
        """
        nodes: list[Node] = []

        if self.platform_type == "franka":
            nodes.append(
                Node(
                    package="rcdt_joystick",
                    executable="joy_to_twist.py",
                    parameters=[
                        {"sub_topic": f"/{self.namespace}/joy"},
                        {"pub_topic": f"/{self.namespace}/servo_node/delta_twist_cmds"},
                        {"config_pkg": "rcdt_franka"},
                        {"pub_frame": f"{self.namespace}/fr3_hand"},
                    ],
                    namespace=self.namespace,
                )
            )
            nodes.append(
                Node(
                    package="rcdt_joystick",
                    executable="joy_to_gripper.py",
                    parameters=[
                        {"config_pkg": "rcdt_franka"},
                    ],
                    namespace=self.namespace,
                )
            )

        return nodes
