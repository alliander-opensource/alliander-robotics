# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import os

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from rcdt_tools.rviz import Rviz
from rcdt_tools.vizanti import Vizanti
from rcdt_utilities import launch_utils
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path


def add_arm(namespace: str, use_moveit: bool):
    print(f"Adding arm with namespace {namespace}")
    if use_moveit:
        Rviz.moveit_namespaces.append(namespace)
        Rviz.add_motion_planning_plugin(namespace)
        Rviz.add_planning_scene(namespace)
        Rviz.add_robot_state(namespace)
        Rviz.add_trajectory(namespace)


def add_vehicle(namespace: str, use_gps: bool, window_size: int):
    print(f"Adding vehicle with namespace {namespace}")
    if not use_gps:
        Rviz.add_map(f"/{namespace}/map")

    Rviz.add_map(f"/{namespace}/global_costmap/costmap")
    Rviz.add_path(f"/{namespace}/plan")

    Rviz.set_grid_size(window_size)
    Rviz.set_grid_frame(f"/{namespace}/base_footprint")

    Rviz.add_polygon(f"/{namespace}/polygon_slower")
    Rviz.add_polygon(f"/{namespace}/velocity_polygon_stop")

    Vizanti.add_platform_model(namespace)
    Vizanti.add_button("Trigger", f"/{namespace}/hardware/e_stop_trigger")
    Vizanti.add_button("Reset", f"/{namespace}/hardware/e_stop_reset")
    Vizanti.add_button(
        "Estop Status",
        f"/{namespace}/hardware/e_stop",
        "std_msgs/msg/Bool",
    )
    Vizanti.add_button("Stop", f"/{namespace}/waypoint_follower_controller/stop")
    Vizanti.add_initial_pose()
    Vizanti.add_goal_pose()
    Vizanti.add_waypoints(namespace)
    Vizanti.add_map("global_costmap", f"/{namespace}/global_costmap/costmap")
    Vizanti.add_path(f"/{namespace}/plan")


def add_lidar(namespace: str):
    Rviz.add_laser_scan(namespace)


def launch_setup(context: LaunchContext) -> list:
    use_rviz = os.environ.get("USE_RVIZ", default="false").lower() == "true"
    use_vizanti = os.environ.get("USE_VIZANTI", default="false").lower() == "true"

    use_moveit = os.environ.get("USE_MOVEIT", default="false").lower() == "true"
    use_gps = os.environ.get("USE_GPS", default="false").lower() == "true"
    window_size = int(os.environ.get("WINDOW_SIZE", default="10"))

    platforms = os.environ.get("PLATFORMS", default="")

    platforms = platforms.replace(" ", "").split(",")

    for platform in platforms:
        Rviz.add_platform_model(platform)
        match platform.lower():
            case "franka":
                add_arm("franka", use_moveit)
            case "panther":
                add_vehicle("panther", use_gps, window_size)
            case "lynx":
                add_vehicle("lynx", use_gps, window_size)
            case "ouster":
                add_lidar("ouster")
            case "velodyne":
                add_lidar("velodyne")

    nodes = []

    if use_rviz:
        Rviz.set_fixed_frame("map")
        Rviz.create_rviz_file()
        rviz = RegisteredLaunchDescription(
            get_file_path("rcdt_tools", ["launch"], "rviz.launch.py")
        )
        nodes.append(rviz)
    if use_vizanti:
        Vizanti.create_config_file()
        vizanti = RegisteredLaunchDescription(
            get_file_path("rcdt_tools", ["launch"], "vizanti.launch.py")
        )
        nodes.append(vizanti)

    utilities = RegisteredLaunchDescription(
        get_file_path("rcdt_utilities", ["launch"], "utils.launch.py")
    )
    nodes.append(utilities)

    return [
        Register.group(utilities, context),
        Register.group(rviz, context) if use_rviz else launch_utils.SKIP,
        Register.group(vizanti, context) if use_vizanti else launch_utils.SKIP,
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
