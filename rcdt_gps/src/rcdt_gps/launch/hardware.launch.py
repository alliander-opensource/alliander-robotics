# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import itertools

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.config_objects import GPS
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.register import Register

platform_arg = LaunchArgument("platform_config", "")

T = True
F = False

# Parameters based on https://github.com/ros-navigation/navigation2_tutorials/blob/rolling/nav2_gps_waypoint_follower_demo/config/dual_ekf_navsat_params.yaml


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    gps_config = GPS.from_str(platform_arg.string_value(context))

    nmea_driver = Node(
        package="nmea_navsat_driver",
        executable="nmea_socket_driver",
        name="gps",
        namespace=gps_config.namespace,
        parameters=[
            {
                "ip": gps_config.ip_address,
                "port": 5000,
                "frame_id": "gps",
                "tf_prefix": gps_config.parent.namespace,
            },
        ],
        remappings=[
            ("fix", "~/fix"),
            ("heading", "~/heading"),
            ("time_reference", "~/time_reference"),
            ("vel", "~/vel"),
        ],
    )

    navsat_transform_node = Node(
        package="robot_localization",
        executable="navsat_transform_node",
        namespace=namespace_gps,
        parameters=[
            {
                "publish_filtered_gps": True,
            }
        ],
        remappings=[("imu", f"/{namespace_vehicle}/imu/data")],
    )

    # Define EKF node that creates the tf between odom and map:
    ekf_global = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_global",
        namespace=namespace_gps,
        parameters=[
            {
                "two_d_mode": True,
                "publish_tf": True,
                "world_frame": "map",
                "map_frame": "map",
                "odom_frame": f"{namespace_vehicle}/odom",
                "base_link_frame": f"{namespace_vehicle}/base_footprint",
                "odom0": f"/{namespace_vehicle}/odometry/wheels",
                "odom0_config": list(
                    itertools.chain.from_iterable(
                        [
                            [F, F, F],  # [x_pos, y_pos, z_pos]
                            [F, F, F],  # [roll, pitch, yaw]
                            [T, T, T],  # [x_vel, y_vel, z_vel]
                            [F, F, T],  # [roll_rate, pitch_rate, yaw_rate]
                            [F, F, F],  # [x_accel, y_accel, z_accel]
                        ]
                    )
                ),
                "odom1": f"/{namespace_gps}/odometry/gps",
                "odom1_config": list(
                    itertools.chain.from_iterable(
                        [
                            [T, T, F],  # [x_pos, y_pos, z_pos]
                            [F, F, F],  # [roll, pitch, yaw]
                            [F, F, F],  # [x_vel, y_vel, z_vel]
                            [F, F, F],  # [roll_rate, pitch_rate, yaw_rate]
                            [F, F, F],  # [x_accel, y_accel, z_accel]
                        ]
                    )
                ),
                "imu0": f"/{namespace_vehicle}/imu/data",
                "imu0_config": list(
                    itertools.chain.from_iterable(
                        [
                            [F, F, F],  # [x_pos, y_pos, z_pos]
                            [F, F, T],  # [roll, pitch, yaw]
                            [F, F, F],  # [x_vel, y_vel, z_vel]
                            [F, F, F],  # [roll_rate, pitch_rate, yaw_rate]
                            [F, F, F],  # [x_accel, y_accel, z_accel]
                        ]
                    )
                ),
            }
        ],
    )

    return [
        Register.on_start(nmea_driver, context),
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
