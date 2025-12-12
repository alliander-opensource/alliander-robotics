# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import os

from launch import LaunchContext, LaunchDescription
from launch.actions import ExecuteProcess, OpaqueFunction
from launch_ros.actions import LifecycleNode, Node
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
        get_file_path("rcdt_ouster", ["launch"], "description.launch.py")
    )

    map_link = create_map_link("ouster", (0, 0, 0), (0, 0, 0))

    use_sim = simulation
    namespace = "ouster"
    target_frame = ""
    ip_device = ""
    ip_udp_destination = ""
    driver_node_name = "ouster_driver"

    sensor_frame = f"{namespace}/ouster"
    lidar_frame = f"{namespace}/os_lidar"
    imu_frame = f"{namespace}/os_imu"

    ouster_driver_node = LifecycleNode(
        package="ouster_ros",
        executable="os_driver",
        namespace=namespace,
        name=driver_node_name,
        parameters=[
            {
                "sensor_hostname": ip_device,
                "udp_dest": ip_udp_destination,
                "lidar_port": 7502,
                "imu_port": 7503,
                "lidar_mode": "1024x10",  # options: { 512x10, 512x20, 1024x10, 1024x20, 2048x10, 4096x5 }
                "sensor_frame": sensor_frame,
                "lidar_frame": lidar_frame,
                "imu_frame": imu_frame,
                "point_cloud_frame": lidar_frame,
                "proc_mask": "PCL",  # options: IMU|PCL|SCAN|IMG|RAW|TLM
                "metadata": "/tmp/ouster_metadata.json",  # Place the metadata in a temporary folder since we do not need it.
            }
        ],
        remappings=[
            ("points", "scan/points")
        ],  # Remap for the pointcloud_to_laserscan Node
        output="both",
    )

    configure_ouster_driver = ExecuteProcess(
        cmd=[
            "ros2",
            "lifecycle",
            "set",
            f"/{namespace}/{driver_node_name}",
            "configure",
        ],
        shell=False,
    )

    activate_ouster_driver = ExecuteProcess(
        cmd=[
            "ros2",
            "lifecycle",
            "set",
            f"/{namespace}/{driver_node_name}",
            "activate",
        ],
        shell=False,
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
                "range_max": 90.0,
            }
        ],
        namespace=namespace,
    )

    return [
        Register.group(description, context),
        Register.on_start(map_link, context),
        Register.on_start(ouster_driver_node, context) if not use_sim else SKIP,
        Register.on_exit(configure_ouster_driver, context) if not use_sim else SKIP,
        Register.on_exit(activate_ouster_driver, context) if not use_sim else SKIP,
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
