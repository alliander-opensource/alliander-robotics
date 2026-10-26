# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


from alliander_utilities.launch_argument import LaunchArgument
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:  # noqa: PLR0912, PLR0915
    return []


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
