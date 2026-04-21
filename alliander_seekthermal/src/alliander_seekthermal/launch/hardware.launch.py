# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import subprocess
import sys

from alliander_utilities.config_objects import Camera
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.register import Register
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node

platform_arg = LaunchArgument("platform_config", "")


def get_camera_address(target_mac: str) -> str | None:
    """Gets the camera's IP address based on vendor OUI.

    Args:
        target_mac (str): target MAC address to look for (OUI only recommended).

    Returns:
        str | None: IP address if MAC address is found, None otherwise.
    """
    target_mac = target_mac.lower()
    result = subprocess.run(["ip", "neigh", "show"], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if target_mac in line.lower():
            return line.split()[0]
    return None


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    camera_config = Camera.from_str(platform_arg.string_value(context))

    frame_prefix = camera_config.namespace + "/" if camera_config.namespace else ""

    # look for OUI (Organizationally Unique Identifier) only
    ip_address = get_camera_address("ec:9a:0c:60")

    if ip_address is None:
        print(
            "Unable to find IP address of Seek Thermal camera (OUI EC:9A:0C:60). Make sure device is connected and pingable."
        )
        sys.exit(1)

    seekthermal_bridge_node = Node(
        package="alliander_seekthermal",
        executable="alliander_seekthermal.py",
        output="both",
        parameters=[
            {
                "ip_address": ip_address,
                "frame_id": frame_prefix + "seekthermal",
            }
        ],
        namespace=camera_config.namespace,
    )

    return [
        Register.on_start(seekthermal_bridge_node, context),
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
