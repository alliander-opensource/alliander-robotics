# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import ExecuteProcess, OpaqueFunction
from launch_ros.actions import LifecycleNode
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.register import Register

namespace_arg = LaunchArgument("namespace", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    namespace = namespace_arg.string_value(context)
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

    return [
        Register.on_start(ouster_driver_node, context),
        Register.on_exit(configure_ouster_driver, context),
        Register.on_exit(activate_ouster_driver, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description.

    Returns:
        LaunchDescription: The launch description.
    """
    return LaunchDescription(
        [
            namespace_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
