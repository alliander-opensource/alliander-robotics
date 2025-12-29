# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import itertools

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node, SetParameter
from rcdt_utilities.config_objects import GPS
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.launch_utils import SKIP, state_publisher_node, static_tf_node
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path

T, F = True, False

config_arg = LaunchArgument("config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    configuration = GPS.from_str(config_arg.string_value(context))

    state_publisher = state_publisher_node(
        namespace=configuration.namespace,
        platform="nmea",
        xacro="rcdt_nmea_navsat.urdf.xacro",
        xacro_arguments={
            "namespace": configuration.namespace,
            "parent": "" if configuration.parent.link else "world",
        },
    )

    parent = configuration.parent
    static_tf = static_tf_node(
        parent_frame=f"{parent.namespace}/{parent.link}" if parent.link else "map",
        child_frame=f"{configuration.namespace}/{parent.connects_to}",
        position=configuration.position,
        orientation=configuration.orientation,
    )

    hardware = RegisteredLaunchDescription(
        get_file_path("rcdt_nmea", ["launch"], "hardware.launch.py"),
        {"config": configuration.to_str()},
    )

    navsat_transform = Node(
        package="robot_localization",
        executable="navsat_transform_node",
        namespace=configuration.namespace,
        parameters=[
            {
                "publish_filtered_gps": True,
            }
        ],
        remappings=[("imu", f"/{configuration.parent.namespace}/imu/data")],
    )

    # Define EKF node that creates the tf between odom and map:
    ekf_global = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_global",
        namespace=configuration.parent.namespace,
        parameters=[
            {
                "two_d_mode": True,
                "publish_tf": True,
                "world_frame": "map",
                "map_frame": "map",
                "odom_frame": f"{configuration.parent.namespace}/odom",
                "base_link_frame": f"{configuration.parent.namespace}/base_footprint",
                "odom0": f"/{configuration.parent.namespace}/odometry/wheels",
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
                "odom1": f"/{configuration.namespace}/odometry/gps",
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
                "imu0": f"/{configuration.parent.namespace}/imu/data",
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
        # SetParameter(name="use_sim_time", value=configuration.simulation),
        Register.on_start(state_publisher, context),
        Register.on_start(static_tf, context),
        Register.group(hardware, context) if not configuration.simulation else SKIP,
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
            config_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
