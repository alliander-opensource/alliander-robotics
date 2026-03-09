# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import warnings

from alliander_utilities.config_objects import PlatformList
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.register import Register
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node, SetParameter

platform_list_arg = LaunchArgument("platform_list", "")
use_sim_time_arg = LaunchArgument("use_sim_time", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.

    Raises:
        RuntimeError: No platform is found.
    """
    platforms = PlatformList.from_str(platform_list_arg.string_value(context)).platforms

    # Create default namespaces which can be ignored when left unchanged
    gps_namespace = ""

    # Find platforms in the platform list
    for platform in platforms:
        match platform.platform_type:
            case "GPS":
                if not gps_namespace:
                    gps_namespace = f"/{platform.namespace}"
                else:
                    warnings.warn(
                        "No support for multiple GPS sensors yet, only accepting the first GPS.",
                        RuntimeWarning,
                        stacklevel=1,
                    )

            case _:
                pass

    if not gps_namespace:
        raise RuntimeError("No platform present, cancelling the diagnostics package.")

    diagnostics_node = Node(
        package="alliander_diagnostics",
        executable="diagnostics",
        name="diagnostics",
        parameters=[
            {"enable_gps": bool(gps_namespace)},
            {"gps_topic": f"{gps_namespace}/gps/fix"},
        ],
    )

    use_sim_time = use_sim_time_arg.bool_value(context)

    return [
        SetParameter(name="use_sim_time", value=use_sim_time),
        Register.on_start(diagnostics_node, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description.

    Returns:
        LaunchDescription: The launch description.
    """
    return LaunchDescription(
        [
            platform_list_arg.declaration,
            use_sim_time_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
