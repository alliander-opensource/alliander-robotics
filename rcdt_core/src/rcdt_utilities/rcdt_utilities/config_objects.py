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


class EnvironmentConfiguration:
    """A class used to store the environment configuration."""

    platforms: dict[str, "Platform"] = {}
    world: str = "empty.sdf"
    gazebo_ui: bool = False
    rviz: bool = True
    vizanti: bool = False
    rcdt_gui: bool = False


def link(
    parent_platform: Platform,
    child_platform: Platform,
    parent_link: str = "",
    child_link: str = "",
) -> None:
    """Create a parent-child relationship between two platforms."""
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
            Config: The configuration object.
        """
        return cls.from_json(data)


@dataclass
class Parent(Config):
    """Class representing a parent platform."""

    namespace: str = ""
    link: str = ""
    connects_to: str = ""


@dataclass
class Child(Config):
    """Class representing a child platform."""

    platform_type: str = ""
    namespace: str = ""
    link: str = ""
    connects_to: str = ""


# General platform definition:
@dataclass
class Platform(Config):
    """Base class for all platforms."""

    name: str
    position: tuple = (0, 0, 0)
    orientation: tuple = (0, 0, 0)
    namespace: str = ""
    platform_type: str = ""
    simulation: bool = True

    parent: Parent = field(default_factory=Parent)
    childs: list[Child] = field(default_factory=list[Child])

    initialized: bool = False

    def __post_init__(self):
        """Initialize the platform configuration."""
        if self.initialized:
            return
        self.orientation = tuple(map(math.radians, self.orientation))
        if not self.namespace:
            self.namespace = self.name
        if not self.parent.connects_to:
            self.parent.connects_to = self.default_link_to_parent()
        EnvironmentConfiguration.platforms[self.namespace] = self
        self.initialized = True

    def package(self) -> str:
        """Get the package name for the platform.

        Returns:
            str: The package name.
        """
        match self.name:
            case "panther" | "lynx":
                return "rcdt_husarion"
            case _:
                return f"rcdt_{self.name}"

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
    """Configuration for Nav2 on a vehicle platform."""

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
    """Configuration for MoveIt on an arm platform."""

    load_rviz_motion_planning_plugin: bool = False


# Platforms:
@dataclass
class Arm(Platform):
    """Configuration for an Arm platform."""

    platform_type: str = "Arm"
    gripper: bool = False
    moveit: bool = False
    ip_address: str = ""

    moveit_config: MoveitConfig = field(default_factory=MoveitConfig)


@dataclass
class Vehicle(Platform):
    """Configuration for a Vehicle platform."""

    platform_type: str = "Vehicle"
    nav2_config: Nav2Config = field(default_factory=Nav2Config)

    @property
    def nav2(self) -> bool:
        """Return whether any Nav2 features are enabled."""
        return any(
            [
                self.nav2_config.collision_monitor,
                self.nav2_config.slam,
                self.nav2_config.navigation,
            ]
        )


@dataclass
class Camera(Platform):
    """Configuration for a Camera platform."""

    platform_type: str = "Camera"


@dataclass
class Lidar(Platform):
    """Configuration for a Lidar platform."""

    platform_type: str = "Lidar"
    ip_address: str = "10.15.20.5"
    ip_destination: str = "10.15.20.3"


@dataclass
class GPS(Platform):
    """Configuration for a GPS platform."""

    platform_type: str = "GPS"
    ip_address: str = ""


# Configurations containing lists of platforms:
@dataclass
class PlatformList(Config):
    """Base class for configurations containing lists of platforms."""

    platforms: List[
        Annotated[
            Union[Platform, Arm, Vehicle, Lidar, Camera, GPS],
            Discriminator(field="platform_type", include_supertypes=True),
        ]
    ] = field(default_factory=list)


@dataclass
class SimulatorConfig(PlatformList):
    """Configuration for the simulator."""

    load_ui: bool = True
    world: str = "empty.sdf"


@dataclass
class VisualizationConfig(PlatformList):
    """Configuration for visualization tools."""

    rviz: bool = True
    vizanti: bool = False
    gui: bool = False
