# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.launch_utils import SKIP
from rcdt_utilities.register import Register

use_sim_arg = LaunchArgument("simulation", True, [True, False])
namespace_arg = LaunchArgument("namespace", default_value="")
ip_address_arg = LaunchArgument("ip_address", "")


def launch_setup(context: LaunchContext) -> list:
    """Launch the nmea_socket_driver node from the nmea_navsat_driver package.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: A list of actions to be executed in the launch description.
    """
    use_sim = use_sim_arg.bool_value(context)
    namepace = namespace_arg.string_value(context)
    ip_address = ip_address_arg.string_value(context)

    nmea_driver = Node(
        package="nmea_navsat_driver",
        executable="nmea_socket_driver",
        name="gps",
        namespace=namepace,
        parameters=[
            {
                "ip": ip_address,
                "port": 5000,
                "frame_id": "gps",
                "tf_prefix": namepace,
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
        Register.on_start(nmea_driver, context) if not use_sim else SKIP,
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the realsense camera.

    Returns:
        LaunchDescription: The launch description for the realsense camera.
    """
    return LaunchDescription(
        [
            namespace_arg.declaration,
            ip_address_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
