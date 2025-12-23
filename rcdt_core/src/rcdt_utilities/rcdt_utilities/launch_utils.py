# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
from launch import LaunchDescriptionEntity
from launch_ros.actions import Node

from rcdt_utilities.ros_utils import get_file_path, get_robot_description

SKIP = LaunchDescriptionEntity()


def state_publisher_node(
    namespace: str, platform: str, xacro: str, xacro_arguments: dict | None = None
) -> Node:
    """Create a state publisher node.

    Returns:
        Node | None: The state publisher node for the robot or None if not applicable.
    """
    if xacro_arguments is None:
        xacro_arguments = {}
    xacro_path = get_file_path("rcdt_description", [platform, "urdf"], xacro)
    robot_description = get_robot_description(xacro_path, xacro_arguments)
    return Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="state_publisher",
        namespace=namespace,
        parameters=[
            robot_description,
            {"frame_prefix": f"{namespace}/"},
            {"publish_frequency": 1000.0},
        ],
    )


def static_tf_node(
    parent_frame: str,
    child_frame: str,
    position: tuple = (0, 0, 0),
    orientation: tuple = (0, 0, 0),
) -> Node:
    """Create a static_transform_publisher node that links two frames.

    Args:
        parent_frame (str): The parent frame.
        child_frame (str): The child frame.
        position (tuple): The position of the child frame relative to the parent frame.
        orientation (tuple): The orientation of the child frame relative to the parent frame.

    Returns:
        Node: A static_transform_publisher node that links the platform with the world or None if not applicable.

    Raises:
        ValueError: If position or orientation do not have exactly 3 entries.
    """
    entries = 3
    if len(position) != entries:
        raise ValueError("Position should be defined as '(x, y, z)'.")
    if len(orientation) != entries:
        raise ValueError("Orientation should be defined as '(roll, pitch, yaw)'.")

    return Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_tf_world",
        arguments=[
            "--frame-id",
            parent_frame,
            "--child-frame-id",
            child_frame,
            "--x",
            f"{position[0]}",
            "--y",
            f"{position[1]}",
            "--z",
            f"{position[2]}",
            "--roll",
            f"{orientation[0]}",
            "--pitch",
            f"{orientation[1]}",
            "--yaw",
            f"{orientation[2]}",
        ],
    )
