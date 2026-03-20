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
    """Setup the launch description for the diagnostic nodes.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: A list of actions to be executed in the launch description.

    Raises:
        RuntimeError: Don't run the diagnostics node when no platforms require diagnostics.
    """
    platforms = PlatformList.from_str(platform_list_arg.string_value(context)).platforms

    sensor_configs: dict[str, list[dict]] = {}

    for platform in platforms:
        if platform.diagnostic_topic:
            sensor_configs.setdefault(platform.platform_type.lower(), []).append(
                {
                    "namespace": platform.namespace,
                    "topic": platform.diagnostic_topic,
                    "timeouts": platform.diagnostic_timeouts,  # (warn, error, stale)
                }
            )

    parameters: dict[str, str | list[str]] = {
        "modules": [],
    }

    for sensor_type, configs in sensor_configs.items():
        if not configs:
            continue

        if len(configs) > 1:
            warnings.warn(
                f"Multiple {sensor_type.upper()} sensors detected, using first.",
                RuntimeWarning,
                stacklevel=1,
            )

        config = configs[0]

        namespace = config["namespace"]
        topic = config["topic"]
        timeouts = config["timeouts"]

        parameters["modules"].append(sensor_type)
        parameters[f"{sensor_type}.topic"] = f"/{namespace}/{topic}"
        parameters[f"{sensor_type}.timeouts"] = list(timeouts)

    if not parameters["modules"]:
        raise RuntimeError("No platform present, cancelling the diagnostics package.")

    diagnostics_node = Node(
        package="alliander_diagnostics",
        executable="alliander_diagnostics_node",
        name="diagnostics",
        parameters=[parameters],
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
