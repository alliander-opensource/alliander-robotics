# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import xacro
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.register import Register
from rcdt_utilities.ros_utils import get_file_path

namespace_arg = LaunchArgument("namespace", "franka")


def get_robot_description(
    xacro_path: str, xacro_arguments: dict | None = None, semantic: bool = False
) -> dict:
    """Process a Xacro file to generate the robot description.

    Args:
        xacro_path (str): The path to the Xacro file.
        xacro_arguments (dict | None): A dictionary of arguments to pass to the Xacro processor.
        semantic (bool): Whether to return the semantic robot description.

    Returns:
        dict: A dictionary containing the robot description in XML format.
    """
    if xacro_arguments is None:
        xacro_arguments = {}
    robot_description_config = xacro.process_file(xacro_path, mappings=xacro_arguments)
    name = "robot_description_semantic" if semantic else "robot_description"
    return {name: robot_description_config.toxml()}


def create_state_publisher(context: LaunchContext) -> Node | None:
    """Create a state publisher node for the robot.

    Returns:
        Node | None: The state publisher node for the robot or None if not applicable.
    """
    xacro_path = get_file_path("rcdt_franka", ["urdf"], "franka.urdf.xacro")
    robot_description = get_robot_description(
        xacro_path, {"simulation": str(True), "namespace": "franka"}
    )
    namespace = namespace_arg.string_value(context)
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


def launch_setup(context: LaunchContext) -> list:
    nodes = []
    state_publisher_node = create_state_publisher(context)
    if isinstance(state_publisher_node, Node):
        print("Created state publisher node!")
        nodes.append(Register.on_start(state_publisher_node, context))
    else:
        print("create_state_publisher() returned None")
    return nodes


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            namespace_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
