# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from launch_ros.actions import Node


class Vehicle:
    """Extension on Platform with vehicle specific functionalities."""

    def __init__(  # noqa: PLR0913
        self,
        namespace: str,
        position: list | None = None,
        orientation: list = None,
        simulation: bool = True,
    ):
        """Initialize the Arm platform.

        Args:
            namespace (str): The namespace of the arm.
            position (list): The position of the arm.
            orientation (list): The orientation of the arm.
            simulation (bool): Whether the arm is in simulation mode.
        """
        self.namespace = namespace
        self.position = position if position is not None else [0, 0, 0]
        self.orientation = orientation if orientation is not None else [0, 0, 0]
        self.simulation = simulation

    def create_map_link(self) -> Node:
        """Create a static_transform_publisher node that links the platform to the map.

        If the platform is a Vehicle that is using SLAM or navigation, None is returned.
        In this case, a localization node will make the link to the 'map' frame.
        If a vehicle is not using SLAM or navigation, the 'odom' frame is directly linked to the 'map' frame.

        Returns:
            Node: A static_transform_publisher node that links the platform with the world or None if not applicable.
        """
        return Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="static_tf_world",
            arguments=[
                "--frame-id",
                "map",
                "--child-frame-id",
                f"{self.namespace}/odom",
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
