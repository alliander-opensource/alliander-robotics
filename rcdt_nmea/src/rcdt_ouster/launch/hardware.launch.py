# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.config_objects import GPS
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.register import Register

config_arg = LaunchArgument("config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    configuration = GPS.from_str(config_arg.string_value(context))

    nmea_driver = Node(
        package="nmea_navsat_driver",
        executable="nmea_socket_driver",
        name="gps",
        namespace=configuration.namespace,
        parameters=[
            {
                "ip": configuration.ip_address,
                "port": 5000,
                "frame_id": "gps",
                "tf_prefix": configuration.parent.namespace,
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
            config_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
