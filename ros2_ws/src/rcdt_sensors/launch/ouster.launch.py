# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import ExecuteProcess, OpaqueFunction
from launch_ros.actions import LifecycleNode, Node
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.launch_utils import SKIP
from rcdt_utilities.register import Register

use_sim_arg = LaunchArgument("simulation", True, [True, False])
namespace_arg = LaunchArgument("namespace", "ouster")
target_frame_arg = LaunchArgument("target_frame", "")
ip_device_arg = LaunchArgument("ip_device", "")  # IP address of the Ouster LiDAR
ip_udp_destination_arg = LaunchArgument(
    "ip_udp_destination", ""
)  # Data destination address (host computer)


def launch_setup(context: LaunchContext) -> list:
    """Setup the launch description for the Ouster lidar.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: A list of actions to be executed.
    """
    use_sim = use_sim_arg.bool_value(context)
    namespace = namespace_arg.string_value(context)
    target_frame = target_frame_arg.string_value(context)
    ip_device = ip_device_arg.string_value(context)
    ip_udp_destination = ip_udp_destination_arg.string_value(context)
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
        Register.on_start(ouster_driver_node, context) if not use_sim else SKIP,
        Register.on_exit(configure_ouster_driver, context) if not use_sim else SKIP,
        Register.on_exit(activate_ouster_driver, context) if not use_sim else SKIP,
        Register.on_start(pointcloud_to_laserscan_node, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the realsense camera.

    Returns:
        LaunchDescription: The launch description for the realsense camera.
    """
    return LaunchDescription(
        [
            use_sim_arg.declaration,
            namespace_arg.declaration,
            target_frame_arg.declaration,
            ip_device_arg.declaration,
            ip_udp_destination_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
