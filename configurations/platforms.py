# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .environment_configuration import EnvironmentConfiguration


@dataclass
class Platform:
    name: str
    position: tuple = (0, 0, 0)
    orientation: tuple = (0, 0, 0)
    namespace: str = ""
    parent: "Platform" | None = None
    childs: list["Platform"] = field(default_factory=list)
    convert_orientation_to_radians: bool = True

    def __post_init__(self):
        if not self.namespace:
            self.namespace = self.name
        if self.convert_orientation_to_radians:
            self.orientation = tuple(map(math.radians, self.orientation))
        EnvironmentConfiguration.platforms.append(self)
        if self.parent:
            self.parent.childs.append(self)

    @property
    def link_to_parent(self) -> str:
        match self.name:
            case "panther":
                return "odom"
            case "franka":
                return "fr3_link0" if self.parent else "world"
            case "ouster":
                return "base_link" if self.parent else "world"
            case "velodyne":
                return "base_link" if self.parent else "world"
            case "realsense":
                return "base_link" if self.parent else "world"
            case "zed":
                return "base_link" if self.parent else "world"
            case _:
                raise ValueError(
                    f"No link_to_child for unknown platform name: {self.name}"
                )

    @property
    def link_to_child(self) -> str:
        match self.name:
            case "panther":
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
    navigation: bool = False


@dataclass
class Camera(Platform):
    pass


@dataclass
class Lidar(Platform):
    ip_address: str = ""


@dataclass
class GPS(Platform):
    pass
