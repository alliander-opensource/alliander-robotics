# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import math
from typing import Literal

from launch_ros.actions import Node
from rcdt_launch.environment_configuration import EnvironmentConfiguration
from rcdt_launch.rviz import Rviz
from rcdt_utilities.register import RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path, get_robot_description


class Platform:  # noqa: PLR0904
    """A class used to dynamically create all the required nodes for a platform."""

    def __init__(  # noqa: PLR0913
        self,
        platform: Literal["axis"],
        position: list,
        orientation: list | None = None,
        namespace: str | None = None,
        parent: "Platform" | None = None,
        parent_link: str = "",
    ):
        """Initialize a platform instance.

        Args:
            platform (Literal["axis"]): The platform type of the platform.
            position (list): The initial position of the platform.
            orientation (list | None): The initial orientation of the platform.
            namespace (str | None): The namespace of the platform. If None, a unique namespace will be generated.
            parent (Platform | None): The parent platform, if any.
            parent_link (str): The link of the parent to which the platform is attached. If empty, the base_link of the parent is used.
        """
        self.platform_type = platform
        self.parent = parent
        self.childs = []
        self.add_to_env()
        self.namespace = namespace if namespace else self.generate_namespace()
        self.ip_address = None

        Rviz.add_platform_model(self.namespace)

        self.position = position
        self.orientation = (
            list(map(math.radians, orientation)) if orientation else [0, 0, 0]
        )

        if parent is None:
            self.is_child = False
            self.parent_link = "none"
        else:
            self.is_child = True
            self.parent_link = (
                parent_link if parent_link else parent.default_connect_link
            )
            parent.add_child(self)

    @property
    def base_link(self) -> str:  # noqa: PLR0911
        """Return the base link for the platform.

        Returns:
            str: The base link for the platform.

        Raises:
            ValueError: If the platform is unknown.
        """
        match self.platform_type:
            case "axis":
                return "base_link"
            case _:
                raise ValueError("Unable to provide base_link: Unknown platform.")

    @property
    def controller_path(self) -> str | None:
        """Return the controller launch file path for the platform."""
        pass

    @property
    def default_connect_link(self) -> str:
        """Return the default link to which child platforms should connect.

        Raises:
            ValueError: If the platform is unknown.
        """
        raise ValueError("Unable to provide default connection link: Unknown platform.")

    @property
    def frame_prefix(self) -> str:
        """Return the frame prefix for the platform based on its namespace.

        Returns:
            str: The frame prefix for the platform.
        """
        return self.namespace + "/" if self.namespace else ""

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

        return get_robot_description(self.xacro_path, xacro_arguments)

    @property
    def xacro_path(self) -> str:  # noqa: PLR0911
        """Return the xacro file path for the platform.

        Returns:
            str: The xacro file path for the platform.

        Raises:
            ValueError: If the platform is unknown.
        """
        match self.platform_type:
            case "axis":
                return get_file_path("rcdt_sensors", ["urdf"], "rcdt_axis.urdf.xacro")
            case _:
                raise ValueError("Cannot provide xacro path: unknown platform.")

    def add_child(self, child: "Platform") -> None:
        """Add a child platform to this platform.

        Args:
            child (Platform): The child platform to add.
        """
        self.childs.append([child.parent_link, child.namespace, child.base_link])

    def add_to_env(self) -> None:
        """Add a platform instance to the general environment configuration list."""
        EnvironmentConfiguration.platforms.append(self)
        current_value = EnvironmentConfiguration.platform_indices.get(
            self.platform_type, 0
        )
        EnvironmentConfiguration.platform_indices[self.platform_type] = (
            current_value + 1
        )

    def generate_namespace(self) -> str:
        """Generate an unique namespace for the given platform.

        Returns:
            str: The unique namespace for the platform.
        """
        index = EnvironmentConfiguration.platform_indices.get(self.platform_type, 0)
        return f"{self.platform_type}{index}"

    def create_state_publisher(self) -> Node | None:
        """Create a state publisher node for the platform.

        Returns:
            Node | None: The state publisher node for the platform or None if not applicable.
        """
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

    def create_parent_link(self) -> Node:
        """Create a static_transform_publisher node that links the platform to its parent.

        Returns:
            Node: The static_transform_publisher node.
        """
        return Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name=f"static_tf_{self.parent.namespace}_to_{self.namespace}",
            arguments=[
                "--frame-id",
                f"/{self.parent.namespace}/{self.parent_link}",
                "--child-frame-id",
                f"/{self.namespace}/{self.base_link}",
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

    def joystick_nodes(self) -> list[Node]:  # noqa: PLR6301
        """Return the required nodes to control the platform with a joystick.

        Returns:
            list[Node]: The joystick nodes for the platform.
        """
        return []

    def create_map_link(self) -> Node | None:
        """Create a static_transform_publisher node that links the platform to the map.

        Returns:
            Node | None: A static_transform_publisher node that links the platform with the world or None if not applicable.
        """
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

    def create_controller(self) -> RegisteredLaunchDescription:
        """Create a controller launch description for the platform.

        Returns:
            RegisteredLaunchDescription: The controller launch description for the platform.
        """
        launch_arguments = {
            "simulation": str(EnvironmentConfiguration.simulation),
            "namespace": self.namespace,
        }
        return RegisteredLaunchDescription(
            self.controller_path, launch_arguments=launch_arguments
        )

    def create_launch_description(self) -> list[RegisteredLaunchDescription]:  # noqa: PLR6301
        """Create the launch description for the specific platform.

        Returns:
            list[RegisteredLaunchDescription]: The launch description for the platform.
        """
        return []
