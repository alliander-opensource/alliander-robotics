from __future__ import annotations

import math
import typing
from dataclasses import dataclass, field

from mashumaro.mixins.json import DataClassJSONMixin


class EnvironmentConfiguration:
    """A class used to dynamically create all the required nodes for a platform.

    Attributes:
        bridge_topics (list[str]): A list of all topics that should be bridged between Gazebo and ROS.
        platform_indices (dict[str, int]): A collections of the different platforms and the number of occurrences.
        platforms (list[Platform]): A list of all the platforms.
        names (list[str]): A list of all platform names.
        simulation (bool): Whether the platforms are in simulation mode or not.
        use_vizanti (bool): Whether to use Vizanti for visualization.
        use_joystick (bool): Whether to enable joystick input.
        world (str): The world file to be used in Gazebo.
    """

    platforms: dict[str, "Platform"] = {}
    world: str = "empty.sdf"


def link(
    parent_platform: Platform,
    child_platform: Platform,
    parent_link: str = "",
    child_link: str = "",
) -> None:
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
    child.namespace = child_platform.namespace
    child.link = child_link if child_link else child_platform.default_link_to_parent()
    child.connects_to = (
        parent_link if parent_link else parent_platform.default_link_to_child()
    )
    parent_platform.childs.append(child)


@dataclass
class Config(DataClassJSONMixin):
    def to_str(self) -> str:
        return str(self.to_json())

    @classmethod
    def from_str(cls, data: str) -> typing.Self:
        return cls.from_json(data)


@dataclass
class Parent(Config):
    namespace: str = ""
    link: str = ""
    connects_to: str = ""


@dataclass
class Child(Config):
    namespace: str = ""
    link: str = ""
    connects_to: str = ""


@dataclass
class Platform(Config):
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
        if self.initialized:
            return
        self.orientation = tuple(map(math.radians, self.orientation))
        self.platform_type = type(self).__name__
        if not self.namespace:
            self.namespace = self.name
        if not self.parent.connects_to:
            self.parent.connects_to = self.default_link_to_parent()
        EnvironmentConfiguration.platforms[self.namespace] = self
        self.initialized = True

    def default_link_to_parent(self) -> str:
        match self.name:
            case "panther" | "lynx":
                return "odom"
            case "franka":
                return "fr3_link0" if self.parent.namespace else "world"
            case _:
                return "base_link" if self.parent.namespace else "world"

    def default_link_to_child(self) -> str:
        match self.name:
            case "panther" | "lynx":
                return "base_link"
            case "franka":
                return "fr3_hand"
            case _:
                raise ValueError(
                    f"No link_to_child for unknown platform name: {self.name}"
                )


@dataclass
class Arm(Platform):
    gripper: bool = False
    moveit: bool = False
    ip_address: str = ""


@dataclass
class Vehicle(Platform):
    collision_monitor: bool = False
    slam: bool = False
    navigation: bool = False
    use_gps: bool = False
    window_size: int = 10


@dataclass
class Camera(Platform):
    pass


@dataclass
class Lidar(Platform):
    ip_address: str = ""


@dataclass
class GPS(Platform):
    ip_address: str = ""


@dataclass
class SimulatorConfig(Config):
    load_ui: bool = True
    world: str = "empty.sdf"
    platforms: list[Platform] = field(default_factory=list)


@dataclass
class ToolsConfig(Config):
    rviz: bool = True
    vizanti: bool = False
    platforms: list[Platform] = field(default_factory=list)
