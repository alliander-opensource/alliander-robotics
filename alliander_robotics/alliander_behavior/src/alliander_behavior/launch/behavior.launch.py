# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


from alliander_utilities.config_objects import Vehicle
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.register import Register
from alliander_utilities.ros_utils import get_file_path
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:  # noqa: PLR0912, PLR0915
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    # TODO: make this generic, not only for Vehicles
    vehicle_config = Vehicle.from_str(platform_arg.string_value(context))
    namespace = vehicle_config.namespace
    bt_config = vehicle_config.bt_config
    tree = bt_config.tree

    task_planner_node = Node(
        package="alliander_behavior",
        executable="task_planner_node",
        namespace=namespace,
        parameters=[
            {
                "tree_file": get_file_path(
                    "alliander_behavior", ["config"], f"{tree}.xml"
                )
            }
        ],
    )
    return [Register.on_start(task_planner_node, context)]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the behavior tree stack.

    Returns:
        LaunchDescription: The launch description containing the actions to be executed.
    """
    return LaunchDescription(
        [
            platform_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
