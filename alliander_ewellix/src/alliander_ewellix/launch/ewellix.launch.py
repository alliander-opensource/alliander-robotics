# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
from alliander_utilities.config_objects import Lift
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.launch_utils import SKIP
from alliander_utilities.register import Register
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node, SetParameter

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    lift_config = Lift.from_str(platform_arg.string_value(context))

    driver = Node(
        package="ewellix_driver",
        executable="ewellix_node",
        namespace=lift_config.namespace,
    )

    return [
        SetParameter(name="use_sim_time", value=lift_config.simulation),
        Register.on_start(driver, context) if not lift_config.simulation else SKIP,
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description.

    Returns:
        LaunchDescription: The launch description.
    """
    return LaunchDescription(
        [
            platform_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
