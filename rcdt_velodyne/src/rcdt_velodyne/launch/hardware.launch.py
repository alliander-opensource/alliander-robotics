# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.config_objects import Lidar
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.register import Register
from rcdt_utilities.ros_utils import get_file_path

config_arg = LaunchArgument("config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    config = Lidar.from_str(config_arg.string_value(context))

    frame_prefix = config.namespace + "/" if config.namespace else ""

    velodyne_driver_node = Node(
        package="velodyne_driver",
        executable="velodyne_driver_node",
        output="both",
        parameters=[
            {
                "model": "VLP16",
                "device_ip": config.ip_address,
                "frame_id": frame_prefix + "velodyne",
            }
        ],
        namespace=config.namespace,
    )

    velodyne_transform_node = Node(
        package="velodyne_pointcloud",
        executable="velodyne_transform_node",
        output="both",
        parameters=[
            {
                "calibration": get_file_path(
                    "velodyne_pointcloud", ["params"], "VLP16db.yaml"
                ),
                "model": "VLP16",
                "min_range": 0.1,
                "max_range": 130.0,
            }
        ],
        remappings=[("velodyne_points", "scan/points")],
        namespace=config.namespace,
    )

    return [
        Register.on_start(velodyne_driver_node, context),
        Register.on_start(velodyne_transform_node, context),
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
