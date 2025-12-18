# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.launch_utils import state_publisher_node, static_tf_node
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
        platform="franka",
        xacro="franka.urdf.xacro",
        xacro_arguments={
            "simulation": str(simulation),
            "namespace": namespace,
            "parent": "" if parent else "world",
            "childs": str([child.split(",") for child in childs if child]),
        },
    )

    static_tf = static_tf_node(
        parent_frame=f"{parent}/{parent_link}" if parent else "map",
        child_frame=f"{namespace}/{link_to_parent}",
        position=position,
        orientation=orientation,
    )

    controllers = RegisteredLaunchDescription(
        get_file_path("rcdt_franka", ["launch"], "controllers.launch.py")
    )

    gripper = RegisteredLaunchDescription(
        get_file_path("rcdt_franka", ["launch"], "gripper_services.launch.py"),
        launch_arguments={"namespace": "franka"},
    )

    return [
        Register.on_start(state_publisher, context),
        Register.on_start(static_tf, context),
        Register.group(controllers, context),
        Register.group(gripper, context),
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
