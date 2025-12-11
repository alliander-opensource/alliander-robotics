# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from launch_ros.actions import Node


class Arm:
    """Extension on Platform with arm specific functionalities."""

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

    def create_map_link(self) -> Node | None:
        """Create a static_transform_publisher node that links the platform to the map.

        Returns:
            Node | None: A static_transform_publisher node that links the platform with the world or None if not applicable.
        """
        if not self.simulation:
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
