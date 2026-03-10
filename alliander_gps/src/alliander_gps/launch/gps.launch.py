# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import itertools

from alliander_utilities.adapted_yaml import AdaptedYaml
from alliander_utilities.config_objects import GPS
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.launch_utils import SKIP, state_publisher_node, static_tf_node
from alliander_utilities.register import Register, RegisteredLaunchDescription
from alliander_utilities.ros_utils import get_file_path
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node, SetParameter

T, F = True, False

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    gps_config = GPS.from_str(platform_arg.string_value(context))

    state_publisher = state_publisher_node(
        namespace=gps_config.namespace,
        platform="nmea_gps",
        xacro="nmea_navsat.urdf.xacro",
        xacro_arguments={
            "namespace": gps_config.namespace,
            "parent": "" if gps_config.parent.link else "world",
        },
    )

    parent = gps_config.parent
    static_tf = static_tf_node(
        parent_frame=f"{parent.namespace}/{parent.link}" if parent.link else "map",
        child_frame=f"{gps_config.namespace}/{parent.connects_to}",
        position=gps_config.position,
        orientation=gps_config.orientation,
    )

    hardware = RegisteredLaunchDescription(
        get_file_path("alliander_gps", ["launch"], "hardware.launch.py"),
        {"platform_config": gps_config.to_str()},
    )

    ekf_global_params = AdaptedYaml(
        get_file_path("alliander_gps", ["config"], "ekf_global.yaml"),
        {
            "odom_frame": f"{gps_config.parent.namespace}/odom",
            "base_link_frame": f"{gps_config.parent.namespace}/base_footprint",
            "odom0": f"/{gps_config.parent.namespace}/odometry/wheels",
            "odom1": f"/{gps_config.namespace}/odometry/gps",
            "imu0": f"/{gps_config.parent.namespace}/imu/data",
        },
        root_key=gps_config.parent.namespace,
    )
    navsat_transform_params = AdaptedYaml(
        get_file_path("alliander_gps", ["config"], "navsat_transform.yaml"),
        {},
        root_key=gps_config.parent.namespace,
    )

    navsat_transform = Node(
        package="robot_localization",
        executable="navsat_transform_node",
        name="navsat_transform",
        namespace=gps_config.namespace,
        parameters=[navsat_transform_params.file],
        remappings=[
            ("imu", f"/{gps_config.parent.namespace}/imu/data"),
            (
                "odometry/filtered",
                f"/{gps_config.parent.namespace}/odometry/global",
            ),
        ],
    )

    # Define EKF node that creates the tf between odom and map:
    ekf_global = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_global",
        namespace=gps_config.parent.namespace,
        parameters=[ekf_global_params.file],
        remappings=[
            ("odometry/filtered", f"/{gps_config.parent.namespace}/odometry/global"),
        ],
    )

    return [
        SetParameter(name="use_sim_time", value=gps_config.simulation),
        Register.on_start(state_publisher, context),
        Register.on_start(static_tf, context),
        Register.group(hardware, context) if not gps_config.simulation else SKIP,
        Register.on_start(navsat_transform, context) if parent.link else SKIP,
        Register.on_start(ekf_global, context) if parent.link else SKIP,
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
