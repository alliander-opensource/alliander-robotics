# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.launch_utils import SKIP, state_publisher_node, static_tf_node
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path

simulation_arg = LaunchArgument("simulation", True)
namespace_arg = LaunchArgument("namespace", "")
position_arg = LaunchArgument("position", "")
orientation_arg = LaunchArgument("orientation", "")
link_to_parent_arg = LaunchArgument("link_to_parent", "")
parent_arg = LaunchArgument("parent", "")
parent_link_arg = LaunchArgument("parent_link", "")
childs_arg = LaunchArgument("childs", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    simulation = simulation_arg.bool_value(context)
    namespace = namespace_arg.string_value(context)
    position = position_arg.string_value(context).split()
    orientation = orientation_arg.string_value(context).split()
    link_to_parent = link_to_parent_arg.string_value(context)
    parent = parent_arg.string_value(context)
    parent_link = parent_link_arg.string_value(context)
    childs = childs_arg.string_value(context).split()

    state_publisher = state_publisher_node(
        namespace=namespace,
        platform="ouster",
        xacro="rcdt_os1_128.urdf.xacro",
        xacro_arguments={
            "parent": "" if parent else "world",
        },
    )

    static_tf = static_tf_node(
        parent_frame=f"{parent}/{parent_link}" if parent else "map",
        child_frame=f"{namespace}/{link_to_parent}",
        position=position,
        orientation=orientation,
    )

    hardware = RegisteredLaunchDescription(
        get_file_path("rcdt_ouster", ["launch"], "hardware.launch.py"),
        {"namespace": namespace},
    )

    target_frame = ""
    pointcloud_to_laserscan_node = Node(
        package="pointcloud_to_laserscan",
        executable="pointcloud_to_laserscan_node",
        remappings=[
            ("cloud_in", f"/{namespace}/scan/points"),
            ("scan", f"/{namespace}/scan"),
        ],
        parameters=[
            {
                "target_frame": target_frame,
                "min_height": 0.1,
                "max_height": 2.0,
                "range_min": 0.05,
                "range_max": 90.0,
            }
        ],
        namespace=namespace,
    )

    return [
        Register.on_start(state_publisher, context),
        Register.on_start(static_tf, context),
        Register.group(hardware, context) if not simulation else SKIP,
        Register.on_start(pointcloud_to_laserscan_node, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description.

    Returns:
        LaunchDescription: The launch description.
    """
    return LaunchDescription(
        [
            simulation_arg.declaration,
            namespace_arg.declaration,
            position_arg.declaration,
            orientation_arg.declaration,
            link_to_parent_arg.declaration,
            parent_arg.declaration,
            parent_link_arg.declaration,
            childs_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
