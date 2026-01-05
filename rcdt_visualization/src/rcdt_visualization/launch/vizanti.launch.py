# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.register import Register


def launch_setup(context: LaunchContext) -> list:
    """The launch setup function.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: A list of launch actions to be executed.
    """
    # https://github.com/v-kiniv/rws
    rws_server_node = Node(
        package="rws",
        executable="rws_server",
        name="vizanti_rws_server",
        output="screen",
        parameters=[
            {"rosbridge_compatible ": True},
            {"port": 5001},
            {"watchdog": True},
        ],
        respawn=True,
    )

    flask_node = Node(
        name="vizanti_flask_node",
        package="vizanti_server",
        executable="server.py",
        output="screen",
        parameters=[
            {"host": "0.0.0.0"},
            {"port": 5000},
            {"port_rosbridge": 5001},
            {"flask_debug": True},
            {"base_url": ""},
            {"compression": "cbor"},
            {"default_widget_config": "/tmp/vizanti.json"},
        ],
    )

    tf_handler_node = Node(
        name="vizanti_tf_handler_node",
        package="vizanti_cpp",
        executable="tf_consolidator",
        output="screen",
    )

    service_handler_node = Node(
        name="vizanti_service_handler_node",
        package="vizanti_server",
        executable="service_handler.py",
        output="screen",
    )

    return [
        Register.on_start(rws_server_node, context),
        Register.on_start(flask_node, context),
        Register.on_start(tf_handler_node, context),
        Register.on_log(service_handler_node, "Service handler ready.", context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the navigation stack.

    Returns:
        LaunchDescription: The launch description containing the actions to be executed.
    """
    return LaunchDescription(
        [
            OpaqueFunction(function=launch_setup),
        ]
    )
