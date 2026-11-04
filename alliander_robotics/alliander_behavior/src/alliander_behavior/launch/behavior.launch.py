# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


from alliander_utilities.config_objects import Vehicle
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.register import Register
from alliander_utilities.ros_utils import get_file_path
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node, SetParameter

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:  # noqa: PLR0912, PLR0915
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    # TODO: make this generic, not only for Vehicles
    vehicle_config = Vehicle.from_str(platform_arg.string_value(context))
    namespace = vehicle_config.namespace
    bt_config = vehicle_config.bt_config

    task_planner_node = Node(
        package="alliander_behavior",
        executable="autonomous_navigation_node",
        namespace=namespace,
        # arguments=["--ros-args", "--log-level", "DEBUG"],
        parameters=[
            # ID of BehaviorTree that you want to run
            {"tree_name": bt_config.tree},
            # Doing this here rather in C++ code to levarage alliander_utilities
            {"config_dir": get_file_path("alliander_behavior", ["config"], "")},
            {"server_timeout_ms": 10000},
            # Topics/services/actions here to change them in the XML files
            {"waypoints_topic": "/gps_waypoints"},
            {"battery_topic": f"/{namespace}/battery/battery_status"},
            {"status_topic": f"/{namespace}/status"},
            {"dock_action": f"/{namespace}/dock_robot"},
            {"undock_action": f"/{namespace}/undock_robot"},
            {"navigate_to_pose_action": f"/{namespace}/navigate_to_pose"},
            {"fromll_service": f"/{namespace}/fromLL"},
            {"stop_nav_service": f"/{namespace}/navigation/stop"},
        ],
    )
    return [
        SetParameter(name="use_sim_time", value=vehicle_config.simulation),
        Register.on_start(task_planner_node, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the behavior tree stack.

    Returns:
        LaunchDescription: The launch description containing the actions to be executed.
    """
    return LaunchDescription(
        [
            platform_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
