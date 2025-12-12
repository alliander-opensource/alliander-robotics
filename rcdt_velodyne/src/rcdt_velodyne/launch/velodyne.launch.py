# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import os

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.launch_utils import SKIP
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path


def create_map_link(namespace: str, position: tuple, orientation: tuple) -> Node:
    """Create a static_transform_publisher node that links the platform to the map.

    Returns:
        Node: A static_transform_publisher node that links the platform with the world or None if not applicable.
    """
    return Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_tf_world",
        arguments=[
            "--frame-id",
            "map",
            "--child-frame-id",
            f"{namespace}/base_link",
            "--x",
            f"{position[0]}",
            "--y",
            f"{position[1]}",
            "--z",
            f"{position[2]}",
            "--roll",
            f"{orientation[0]}",
            "--pitch",
            f"{orientation[1]}",
            "--yaw",
            f"{orientation[2]}",
        ],
    )


def launch_setup(context: LaunchContext) -> list:
    simulation = os.environ.get("SIMULATION", default="False").lower() == "true"

    description = RegisteredLaunchDescription(
        get_file_path("rcdt_velodyne", ["launch"], "description.launch.py")
    )

    map_link = create_map_link("velodyne", (0, 0, 0), (0, 0, 0))

    use_sim = simulation
    namespace = "velodyne"
    target_frame = ""
    ip_address = ""

    frame_prefix = namespace + "/" if namespace else ""

    velodyne_driver_node = Node(
        package="velodyne_driver",
        executable="velodyne_driver_node",
        output="both",
        parameters=[
            {
                "model": "VLP16",
                "device_ip": ip_address,
                "frame_id": frame_prefix + "velodyne",
            }
        ],
        namespace=namespace,
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
        namespace=namespace,
    )

    pointcloud_to_laserscan_node = Node(
        package="pointcloud_to_laserscan",
        executable="pointcloud_to_laserscan_node",
        remappings=[
            ("cloud_in", f"/{namespace}/scan/points"),
            ("scan", f"/{namespace}/scan"),
        ],
        parameters=[
            {
                "target_frame": target_frame,
                "min_height": 0.1,
                "max_height": 2.0,
                "range_min": 0.05,
                "range_max": 100.0,
            }
        ],
        namespace=namespace,
    )

    return [
        Register.group(description, context),
        Register.on_start(map_link, context),
        Register.on_start(velodyne_driver_node, context) if not use_sim else SKIP,
        Register.on_start(velodyne_transform_node, context) if not use_sim else SKIP,
        Register.on_start(pointcloud_to_laserscan_node, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the Panther robot.

    Returns:
        LaunchDescription: The launch description for the Panther robot.
    """
    return LaunchDescription(
        [
            OpaqueFunction(function=launch_setup),
        ]
    )
