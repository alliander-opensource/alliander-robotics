# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rcdt_launch.platforms.platform import Platform


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

    bridge_topics: list[str] = []
    platform_indices: dict[str, int] = {}
    platforms: list["Platform"] = []
    names: list[str] = []
    simulation: bool = True
    use_vizanti: bool = False
    use_joystick: bool = True
    world: str = "walls.sdf"
