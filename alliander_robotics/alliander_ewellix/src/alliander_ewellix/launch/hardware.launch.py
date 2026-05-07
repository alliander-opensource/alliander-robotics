# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from alliander_utilities.config_objects import Lift
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.register import Register
from alliander_utilities.ros_utils import get_file_path
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node

platform_arg = LaunchArgument("platform_config", "")
enable_lock_unlock = False


def launch_setup(context: LaunchContext) -> list:
    """Setup the launch description for the hardware.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: A list of actions to be executed in the launch description.
    """
    lift_config = Lift.from_str(platform_arg.string_value(context))
    ns: str = f"/{lift_config.namespace}" if lift_config.namespace else ""

    controllers_config = get_file_path(
        "alliander_description", ["ewellix", "config"], "controllers.yaml"
    )

    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[controllers_config],
        namespace=lift_config.namespace,
        remappings=[
            (f"{ns}/controller_manager/robot_description", f"{ns}/robot_description"),
        ],
    )

    return [
        Register.on_start(ros2_control_node, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the hardware.

    Returns:
        LaunchDescription: The launch description containing the hardware.
    """
    return LaunchDescription(
        [
            platform_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
