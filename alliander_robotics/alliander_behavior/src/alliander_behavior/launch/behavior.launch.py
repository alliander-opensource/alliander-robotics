# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


import re

from alliander_utilities.config_objects import Vehicle
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.register import Register
from alliander_utilities.ros_utils import get_file_path
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node, SetParameter

platform_arg = LaunchArgument("platform_config", "")


def camel_to_snake(text: str) -> str:
    """Converts a CamelCase string to snake_case.

    Args:
        text (str): CamelCase string to convert.

    Returns:
        str: snake_case converted string.
    """
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", text).lower()


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    # Temporary, until other behaviors are implemented
    if "Vehicle" not in platform_arg.string_value(context):
        print(
            f"ERROR: for now, only Vehicles are supported in alliander_behavior. Faulty config: {platform_arg.string_value(context)}.\n\n Exiting..."
        )
        return []
    vehicle_config = Vehicle.from_str(platform_arg.string_value(context))
    bt_config = vehicle_config.bt_config

    params_filename = f"{camel_to_snake(bt_config.tree)}.yaml"
    params_file = get_file_path("alliander_behavior", ["config"], params_filename)

    behavior_executor = Node(
        package="alliander_behavior",
        executable="behavior_executor",
        namespace=vehicle_config.namespace,
        parameters=[
            params_file,
            {
                "tree_name": bt_config.tree,
                "behavior_trees": [
                    "alliander_behavior/behavior_trees",
                    "alliander_behavior/behavior_trees/subtrees",
                ],
                "plugins": [
                    "alliander_behavior/bt_plugins/common",
                    "alliander_behavior/bt_plugins/navigation",
                    "alliander_behavior/bt_plugins/power",
                ],
                "blackboard.battery_percentage_scale": (
                    0.01 if vehicle_config.simulation else 1.0
                ),
            },
        ],
        remappings=[
            ("waypoints", "gps_waypoints"),
            ("battery_status", "battery/battery_status"),
            ("stop_navigation", "navigation/stop"),
        ],
    )
    return [
        SetParameter(name="use_sim_time", value=vehicle_config.simulation),
        Register.on_start(behavior_executor, context),
    ]


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
