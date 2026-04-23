# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from alliander_utilities.config_objects import GPS
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.register import Register
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    gps_config = GPS.from_str(platform_arg.string_value(context))

    nmea_driver = Node(
        package="nmea_navsat_driver",
        executable="nmea_socket_driver",
        name="gps",
        namespace=gps_config.namespace,
        parameters=[
            {
                "ip": gps_config.ip_address,
                "port": 5000,
                "frame_id": "base_link",
                "tf_prefix": gps_config.namespace,
            },
        ],
        remappings=[
            ("fix", "~/fix"),
            ("heading", "~/heading"),
            ("time_reference", "~/time_reference"),
            ("vel", "~/vel"),
        ],
    )

    return [
        Register.on_start(nmea_driver, context),
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
