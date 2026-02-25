# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import math
import typing
from dataclasses import dataclass, field
from typing import Annotated, List, Literal, Union

from mashumaro.mixins.json import DataClassJSONMixin
from mashumaro.types import Discriminator


def link(
    parent_platform: Platform,
    child_platform: Platform,
    parent_link: str = "",
    child_link: str = "",
) -> None:
    """Create a parent-child relationship between two platforms.

    Args:
        parent_platform (Platform): platform that is the parent in the TF relation.
        child_platform (Platform): platform that is the child in the TF relaiton.
        parent_link (str): parent's link name where the connection is made.
        child_link (str): child's link name where the connection is made.
    """
    # Add parent to child:
    child_platform.parent.namespace = parent_platform.namespace
    child_platform.parent.link = (
        parent_link if parent_link else parent_platform.default_link_to_child()
    )
    child_platform.parent.connects_to = (
        child_link if child_link else child_platform.default_link_to_parent()
    )

    # Add child to parent:
    child = Child()
    child.platform_type = type(child_platform).__name__
    child.namespace = child_platform.namespace
    child.link = child_link if child_link else child_platform.default_link_to_parent()
    child.connects_to = (
        parent_link if parent_link else parent_platform.default_link_to_child()
    )
    parent_platform.childs.append(child)


# Base classes:
@dataclass
class Config(DataClassJSONMixin):
    """Base class for all configuration dataclasses."""

    def to_str(self) -> str:
        """Convert the configuration to a string representation.

        Returns:
            str: The string representation of the configuration.
        """
        return str(self.to_json())

    @classmethod
    def from_str(cls, data: str) -> typing.Self:
        """Create a configuration object from a string representation.

        Args:
            data (str): The string representation of the configuration.

        Returns:
            typing.Self: The configuration object.
        """
        return cls.from_json(data)


@dataclass
class Parent(Config):
    """Class representing a parent platform.

    Attributes:
        namespace (str): namespace of the parent platform.
        link (str): link name of the parent platform that connects to a child.
        connects_to (str): child platform to connect to.
    """

    namespace: str = ""
    link: str = ""
    connects_to: str = ""


@dataclass
class Child(Config):
    """Class representing a child platform.

    Attributes:
        platform_type (str): type of platform (e.g. Arm, Vehicle, etc.).
        namespace (str): namespace of the child platform.
        link (str): link name of the child platform that connects to the parent.
        connects_to (str): parent platform to connect to.

    """

    platform_type: str = ""
    namespace: str = ""
    link: str = ""
    connects_to: str = ""


# General platform definition:
@dataclass
class Platform(Config):
    """Base class for all platforms.

    Attributes:
        name (str): Name of the platform.
        position (tuple): 3D position coordinates (x, y, z).
        orientation (tuple): 3D orientation in degrees (roll, pitch, yaw).
        namespace (str): Namespace for the platform.
        platform_type (str): Type identifier for the platform.
        simulation (bool): Whether the platform is running in simulation.
        parent (Parent): Parent platform configuration.
        childs (list[Child]): List of child platform configurations.
        initialized (bool): Whether the platform has been initialized.
    """

    name: str
    position: tuple = (0, 0, 0)
    orientation: tuple = (0, 0, 0)
    namespace: str = ""
    platform_type: str = ""
    simulation: bool = True

    parent: Parent = field(default_factory=Parent)
    childs: list[Child] = field(default_factory=list[Child])

    initialized: bool = False

    def __post_init__(self) -> None:
        """Initialize the platform configuration."""
        if self.initialized:
            return
        self.orientation = tuple(map(math.radians, self.orientation))
        if not self.namespace:
            self.namespace = self.name
        if not self.parent.connects_to:
            self.parent.connects_to = self.default_link_to_parent()
        self.initialized = True

    def package(self) -> str:
        """Get the package name for the platform.

        Returns:
            str: The package name.
        """
        match self.name:
            case "panther" | "lynx":
                return "alliander_husarion"
            case _:
                return f"alliander_{self.name}"

    def default_link_to_parent(self) -> str:
        """Get the default link used to connect to a parent platform.

        Returns:
            str: The link name.
        """
        match self.name:
            case "panther" | "lynx":
                return "odom"
            case "franka":
                return "fr3_link0" if self.parent.namespace else "world"
            case _:
                return "base_link" if self.parent.namespace else "world"

    def default_link_to_child(self) -> str:
        """Get the default link used to connect to a child platform.

        Returns:
            str: The link name.

        Raises:
            ValueError: If the platform name is unknown.
        """
        match self.name:
            case "panther" | "lynx":
                return "base_link"
            case "franka":
                return "fr3_hand"
            case _:
                raise ValueError(
                    f"No link_to_child for unknown platform name: {self.name}"
                )


# Tools:
@dataclass
class Nav2Config(Config):
    """Configuration for Nav2 on a vehicle platform.

    Attributes:
        collision_monitor (bool): Whether to enable collision monitoring.
        slam (bool): Whether to enable SLAM.
        navigation (bool): Whether to enable navigation.
        gps (bool): Whether to enable GPS integration.
        controller (Literal["dwb", "graceful_motion", "mppi", "pure_pursuit", "rotation_shim", "vector_pursuit"]): Navigation controller type to use.
        map (Literal["simulation_map", "ipkw", "ipkw_buiten"]): Map to use for navigation.
        window_size (int): Window size parameter.
    """

    collision_monitor: bool = False
    slam: bool = False
    navigation: bool = False
    gps: bool = False
    controller: Literal[
        "dwb",
        "graceful_motion",
        "mppi",
        "pure_pursuit",
        "rotation_shim",
        "vector_pursuit",
    ] = "vector_pursuit"
    map: Literal["simulation_map", "ipkw", "ipkw_buiten"] = "simulation_map"
    window_size: int = 10


@dataclass
class MoveitConfig(Config):
    """Configuration for MoveIt on an arm platform.

    Attributes:
        load_rviz_motion_planning_plugin (bool): Whether to load the RViz motion planning plugin.
    """

    load_rviz_motion_planning_plugin: bool = False


# Platforms:
@dataclass
class Arm(Platform):
    """Configuration for an Arm platform.

    Attributes:
        platform_type (str): Type identifier for the platform.
        gripper (bool): Whether the arm has a gripper attached.
        moveit (bool) : Whether to enable MoveIt motion planning.
        ip_address (str): IP address of the arm controller.
        moveit_config (MoveitConfig): MoveIt configuration settings.
    """

    platform_type: str = "Arm"
    gripper: bool = False
    moveit: bool = False
    ip_address: str = "10.15.20.4"

    moveit_config: MoveitConfig = field(default_factory=MoveitConfig)


@dataclass
class Vehicle(Platform):
    """Configuration for a Vehicle platform.

    Attributes:
        platform_type (str): Type identifier for the platform.
        nav2_config (Nav2Config): Nav2 configuration settings.
    """

    platform_type: str = "Vehicle"
    nav2_config: Nav2Config = field(default_factory=Nav2Config)

    @property
    def nav2(self) -> bool:
        """Return whether any Nav2 features are enabled.

        Returns:
            bool: True if any Nav2 features are enabled, False otherwise.
        """
        return any(
            [
                # self.nav2_config.collision_monitor,
                self.nav2_config.slam,
                self.nav2_config.navigation,
            ]
        )


@dataclass
class Camera(Platform):
    """Configuration for a Camera platform.

    Attributes:
        platform_type (str): Type identifier for the platform.
    """

    platform_type: str = "Camera"


@dataclass
class Lidar(Platform):
    """Configuration for a Lidar platform.

    Attributes:
        platform_type (str): Type identifier for the platform.
        ip_address (str): IP address of the Lidar sensor.
        ip_udp_destination (str): Destination IP address for Lidar data.
    """

    platform_type: str = "Lidar"
    ip_address: str = "10.15.20.5"
    ip_udp_destination: str = "10.15.20.3"


@dataclass
class GPS(Platform):
    """Configuration for a GPS platform.

    Attributes:
        platform_type (str): Type identifier for the platform.
        ip_address (str): IP address of the GPS receiver.
    """

    platform_type: str = "GPS"
    ip_address: str = ""


# Configurations containing lists of platforms:
@dataclass
class PlatformList(Config):
    """Base class for configurations containing lists of platforms.

    Attributes:
        platforms (list[Platform]): List of platform configurations.
    """  # noqa: DOC605

    platforms: List[
        Annotated[
            Union[Platform, Arm, Vehicle, Lidar, Camera, GPS],
            Discriminator(field="platform_type", include_supertypes=True),
        ]
    ] = field(default_factory=list)


@dataclass
class SimulatorConfig(Config):
    """Configuration for the simulator.

    Attributes:
        load_ui (bool): Whether to load the simulator UI.
        world (str): World file to load in the simulator.
    """

    load_ui: bool = False
    world: str = "empty.sdf"


@dataclass
class VisualizationConfig(Config):
    """Configuration for visualization tools.

    Attributes:
        rviz (bool): Whether to enable RViz visualization.
        foxglove (bool): Whether to enable Foxglove visualization.
        vizanti (bool): Whether to enable Vizanti visualization.
        gui (bool): Whether to enable GUI.
    """

    rviz: bool = False
    foxglove: bool = True
    vizanti: bool = False
    gui: bool = False
