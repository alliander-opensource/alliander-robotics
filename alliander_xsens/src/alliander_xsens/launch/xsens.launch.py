# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import time

from alliander_utilities.config_objects import IMU
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.launch_utils import SKIP, state_publisher_node, static_tf_node
from alliander_utilities.register import Register
from alliander_utilities.ros_utils import get_file_path
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from serial.tools import list_ports

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    imu_config = IMU.from_str(platform_arg.string_value(context))

    vid = "2639"
    pid = "0301"
    imu_device = None

    while imu_device is None and not imu_config.simulation:
        for device in list_ports.grep(f"{vid}:{pid}"):
            print(f"Found IMU device {device}")
            imu_device = device.name
        if imu_device is None:
            print(
                f"No Xsens IMU device (VID:PID {vid}:{pid}) found yet, make sure one is connected."
            )
            time.sleep(1.0)

    state_publisher = state_publisher_node(
        namespace=imu_config.namespace,
        platform="xsens",
        xacro="xsens.urdf.xacro",
        xacro_arguments={
            "parent": "" if imu_config.parent.link else "world",
        },
    )

    parent = imu_config.parent
    static_tf = static_tf_node(
        parent_frame=f"{parent.namespace}/{parent.link}" if parent.link else "map",
        child_frame=f"{imu_config.namespace}/{parent.connects_to}",
        position=imu_config.position,
        orientation=imu_config.orientation,
    )

    parameter_file = get_file_path("alliander_xsens", ["config"], "xsens_mti_node.yaml")
    hardware = Node(
        package="xsens_mti_ros2_driver",
        executable="xsens_mti_node",
        parameters=[parameter_file],
        remappings=[
            ("/imu/acceleration", "imu/acceleration"),
            ("/imu/angular_velocity", "imu/angular_velocity"),
            ("/imu/mag", "imu/mag"),
        ],
        namespace=imu_config.namespace,
    )

    imu_bridge_node = Node(
        package="alliander_xsens",
        executable="imu_bridge_node",
        remappings=[
            ("/topic_in_linear_acceleration", "imu/acceleration"),
            ("/topic_in_angular_velocity", "imu/angular_velocity"),
            ("/topic_out_imu", "imu/data_raw"),
        ],
        namespace=imu_config.namespace,
    )

    madgwick_filter_node = Node(
        package="imu_filter_madgwick",
        executable="imu_filter_madgwick_node",
        remappings=[],
        namespace=imu_config.namespace,
    )

    return [
        Register.on_start(state_publisher, context),
        Register.on_start(static_tf, context),
        Register.on_start(imu_bridge_node, context),
        Register.on_start(madgwick_filter_node, context)
        if not imu_config.simulation
        else SKIP,
        # there seems to be a delay before the IMU is available for
        # xsens_mti_node, so wait until madgwick filter is started
        Register.on_log(
            hardware,
            "Still waiting for data on topics imu/data_raw and imu/mag...",
            context,
        )
        if not imu_config.simulation
        else SKIP,
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the Panther robot.

    Returns:
        LaunchDescription: The launch description for the Panther robot.
    """
    return LaunchDescription(
        [
            platform_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
