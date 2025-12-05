# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import yaml
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node, SetRemap
from nav2_common.launch import RewrittenYaml
from pydantic.v1.utils import deep_update
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.launch_utils import SKIP
from rcdt_utilities.ros_utils import get_file_path, get_yaml
from rcdt_utilities.register import Register
import os

autostart_arg = LaunchArgument(
    "autostart",
    os.environ.get("AUTOSTART", default="True").lower() == "true",
    [True, False],
)

use_respawn_arg = LaunchArgument(
    "use_respawn",
    os.environ.get("USE_RESPAWN", default="True").lower() == "true",
    [True, False],
)

use_slam_arg = LaunchArgument(
    "slam", os.environ.get("USE_SLAM", default="False").lower() == "true", [True, False]
)

namespace_vehicle_arg = LaunchArgument(
    "namespace_vehicle", os.environ.get("NAMESPACE_VEHICLE", default="panther")
)
namespace_lidar_arg = LaunchArgument(
    "namespace_lidar", os.environ.get("NAMESPACE_LIDAR", default="")
)
namespace_gps_arg = LaunchArgument(
    "namespace_gps", os.environ.get("NAMESPACE_GPS", default="")
)
use_collision_monitor_arg = LaunchArgument(
    "collision_monitor",
    os.environ.get("USE_COLLISION_MONITOR", default="False").lower() == "true",
    [True, False],
)
use_navigation_arg = LaunchArgument(
    "navigation",
    os.environ.get("USE_NAVIGATION", default="False").lower() == "true",
    [True, False],
)
use_gps_arg = LaunchArgument(
    "use_gps",
    os.environ.get("USE_GPS", default="False").lower() == "true",
    [True, False],
)

window_size_arg = LaunchArgument(
    "window_size", os.environ.get("WINDOW_SIZE", default="10")
)
controller_arg = LaunchArgument(
    "controller",
    os.environ.get("CONTROLLER", default="vector_pursuit"),
    [
        "dwb",
        "graceful_motion",
        "mppi",
        "pure_pursuit",
        "rotation_shim",
        "vector_pursuit",
    ],
)
global_map_arg = LaunchArgument(
    "map",
    os.environ.get("GLOBAL_MAP", default=""),
    ["", "simulation_map", "ipkw", "ipkw_buiten"],
)


class AdaptedYaml:
    """Class to adapt a YAML file with parameter substitutions."""

    def __init__(self, namespaces: list[str], file: str, substitutions: dict) -> None:
        """Update parameters with substitutions and write to a namespaced YAML file.

        Args:
            namespaces (list[str]): List of namespaces to wrap the parameters.
            file (str): Path to the original YAML file.
            substitutions (dict): Dictionary of parameter substitutions.
        """
        self.namespaces = namespaces
        self.params = deep_update(get_yaml(file), substitutions)
        self.file: str
        self.write_yaml()

    def write_yaml(self) -> None:
        """Write parameters to a namespaced YAML file."""
        self.namespaces.append("ros__parameters")
        self.namespaces.reverse()
        file = "params.yml"
        for namespace in self.namespaces:
            self.params = {namespace: self.params}
            if namespace != "ros__parameters":
                file = namespace + "_" + file
        self.file = "/tmp/" + file
        with open(self.file, "w", encoding="utf-8") as outfile:
            yaml.dump(self.params, outfile, default_flow_style=False)


def launch_setup(context: LaunchContext) -> list:  # noqa: PLR0915
    """Setup the launch description for the navigation stack.

    Args:
        context (LaunchContext): The launch context.

    Raises:
        ValueError: If GPS is enabled but no namespace is provided.

    Returns:
        list: A list of actions to be executed in the launch description.
    """
    autostart = autostart_arg.bool_value(context)
    use_respawn = use_respawn_arg.bool_value(context)
    use_slam = use_slam_arg.bool_value(context)
    namespace_vehicle = namespace_vehicle_arg.string_value(context)
    namespace_lidar = namespace_lidar_arg.string_value(context)
    namespace_gps = namespace_gps_arg.string_value(context)
    use_collision_monitor = use_collision_monitor_arg.bool_value(context)
    use_navigation = use_navigation_arg.bool_value(context)
    use_gps = use_gps_arg.bool_value(context)
    window_size = window_size_arg.int_value(context)
    controller = controller_arg.string_value(context)
    global_map = global_map_arg.string_value(context)

    lifecycle_nodes = []

    if use_collision_monitor:
        lifecycle_nodes.append("collision_monitor")

    if use_gps:
        if not namespace_gps:
            raise ValueError("Namespace for GPS must be provided when using GPS.")
    elif use_slam:
        lifecycle_nodes.append("slam_toolbox")
    elif use_navigation:
        lifecycle_nodes.append("map_server")
        lifecycle_nodes.append("amcl")

    if use_navigation:
        lifecycle_nodes.extend(
            [
                "controller_server",
                "planner_server",
                "behavior_server",
                "bt_navigator",
                "waypoint_follower",
            ]
        )

    slam_params = RewrittenYaml(
        get_file_path("rcdt_nav2", ["config"], "slam_params.yaml"),
        {
            "odom_frame": f"{namespace_vehicle}/odom",
            "base_frame": f"{namespace_vehicle}/base_footprint",
            "scan_topic": f"/{namespace_lidar}/scan",
        },
        root_key=namespace_vehicle,
    )

    amcl_params = RewrittenYaml(
        get_file_path("rcdt_nav2", ["config", "nav2"], "amcl.yaml"),
        {
            "base_frame_id": f"{namespace_vehicle}/base_footprint",
            "odom_frame_id": f"{namespace_vehicle}/odom",
            "scan_topic": f"/{namespace_lidar}/scan",
        },
        root_key=namespace_vehicle,
    )

    plugins = ["obstacle_layer", "inflation_layer"]
    if not use_gps:
        plugins.append("static_layer")

    local_costmap_params = AdaptedYaml(
        [namespace_vehicle, "local_costmap", "local_costmap"],
        get_file_path("rcdt_nav2", ["config", "nav2"], "local_costmap.yaml"),
        {
            "global_frame": f"{namespace_vehicle}/odom",
            "robot_base_frame": f"{namespace_vehicle}/base_footprint",
            "rolling_window": use_gps,
            "plugins": plugins,
        },
    )

    global_costmap_params = AdaptedYaml(
        [namespace_vehicle, "global_costmap", "global_costmap"],
        get_file_path("rcdt_nav2", ["config", "nav2"], "global_costmap.yaml"),
        {
            "robot_base_frame": f"{namespace_vehicle}/base_footprint",
            "rolling_window": use_gps,
            "width": window_size,
            "height": window_size,
            "plugins": plugins,
            "obstacle_layer": {
                "scan": {
                    "topic": f"/{namespace_lidar}/scan",
                    "obstacle_max_range": float(window_size),
                    "raytrace_max_range": float(window_size),
                }
            },
        },
    )

    controller_server_params = RewrittenYaml(
        get_file_path("rcdt_nav2", ["config", "nav2"], "controller_server.yaml"),
        {"odom_topic": f"/{namespace_vehicle}/odom"},
        root_key=namespace_vehicle,
    )

    behavior_server_params = RewrittenYaml(
        get_file_path("rcdt_nav2", ["config", "nav2"], "behavior_server.yaml"),
        {
            "local_frame": f"{namespace_vehicle}/odom",
            "robot_base_frame": f"{namespace_vehicle}/base_footprint",
        },
        root_key=namespace_vehicle,
    )

    follow_path_params = RewrittenYaml(
        get_file_path(
            "rcdt_nav2", ["config", "nav2", "controllers"], f"{controller}.yaml"
        ),
        {},
        root_key=namespace_vehicle,
    )

    bt_navigator_params = RewrittenYaml(
        get_file_path("rcdt_nav2", ["config", "nav2"], "bt_navigator.yaml"),
        {
            "default_nav_to_pose_bt_xml": get_file_path(
                "rcdt_nav2", ["config", "nav2"], "behavior_tree.xml"
            ),
            "robot_base_frame": f"{namespace_vehicle}/base_footprint",
            "odom_topic": f"/{namespace_vehicle}/odom",
        },
        root_key=namespace_vehicle,
    )

    planner_server_params = RewrittenYaml(
        get_file_path("rcdt_nav2", ["config", "nav2"], "planner_server.yaml"),
        {},
        root_key=namespace_vehicle,
    )

    collision_monitor_params = RewrittenYaml(
        get_file_path("rcdt_nav2", ["config", "nav2"], "collision_monitor.yaml"),
        {
            "base_frame_id": f"{namespace_vehicle}/base_footprint",
            "odom_frame_id": f"{namespace_vehicle}/odom",
            "cmd_vel_in_topic": f"/{namespace_vehicle}/cmd_vel_raw",
            "cmd_vel_out_topic": f"/{namespace_vehicle}/cmd_vel",
            "topic": f"/{namespace_lidar}/scan",
        },
        root_key=namespace_vehicle,
    )

    map_tf_publisher = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_tf_world",
        arguments=[
            "--frame-id",
            "map",
            "--child-frame-id",
            f"{namespace_vehicle}/odom",
            "--x",
            "0",
            "--y",
            "0",
            "--z",
            "0",
            "--roll",
            "0",
            "--pitch",
            "0",
            "--yaw",
            "0",
        ],
    )

    slam = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        parameters=[
            slam_params,
            {
                "use_lifecycle_manager": True,
            },
        ],
        namespace=namespace_vehicle,
        remappings=[("/map", f"/{namespace_vehicle}/map")],
    )

    map_server, amcl = None, None
    if global_map:
        map_server = Node(
            package="nav2_map_server",
            executable="map_server",
            parameters=[
                {
                    "yaml_filename": get_file_path(
                        "rcdt_nav2", ["config", "maps"], str(global_map) + ".yaml"
                    ),
                    "topic_name": f"/{namespace_vehicle}/map",
                }
            ],
            namespace=namespace_vehicle,
        )

        amcl = Node(
            package="nav2_amcl",
            executable="amcl",
            parameters=[amcl_params],
            namespace=namespace_vehicle,
            remappings=[(f"/{namespace_vehicle}/initialpose", "/initialpose")],
        )

    controller_server = Node(
        package="nav2_controller",
        executable="controller_server",
        output="screen",
        respawn=use_respawn,
        respawn_delay=2.0,
        parameters=[
            local_costmap_params.file,
            controller_server_params,
            follow_path_params,
        ],
        namespace=namespace_vehicle,
    )

    planner_server = Node(
        package="nav2_planner",
        executable="planner_server",
        name="planner_server",
        output="screen",
        respawn=use_respawn,
        respawn_delay=2.0,
        parameters=[global_costmap_params.file, planner_server_params],
        namespace=namespace_vehicle,
    )

    behavior_server = Node(
        package="nav2_behaviors",
        executable="behavior_server",
        name="behavior_server",
        output="screen",
        respawn=use_respawn,
        respawn_delay=2.0,
        parameters=[behavior_server_params],
        namespace=namespace_vehicle,
    )

    bt_navigator = Node(
        package="nav2_bt_navigator",
        executable="bt_navigator",
        name="bt_navigator",
        output="screen",
        respawn=use_respawn,
        respawn_delay=2.0,
        parameters=[bt_navigator_params],
        remappings=[(f"/{namespace_vehicle}/goal_pose", "/goal_pose")],
        namespace=namespace_vehicle,
    )

    collision_monitor_node = Node(
        package="nav2_collision_monitor",
        executable="collision_monitor",
        name="collision_monitor",
        output="screen",
        respawn=use_respawn,
        respawn_delay=2.0,
        parameters=[collision_monitor_params],
        namespace=namespace_vehicle,
    )

    lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_navigation",
        output="screen",
        parameters=[{"autostart": autostart}, {"node_names": lifecycle_nodes}],
        namespace=namespace_vehicle,
    )

    remappings = []
    if use_gps:
        remappings.append(("/gps/fix", f"/{namespace_gps}/fix"))
    waypoint_follower = Node(
        package="nav2_waypoint_follower",
        executable="waypoint_follower",
        namespace=namespace_vehicle,
        remappings=remappings,
    )

    waypoint_follower_controller = Node(
        package="rcdt_nav2",
        executable="nav2_manager.py",
        namespace=namespace_vehicle,
    )

    pub_topic = (
        f"/{namespace_vehicle}/cmd_vel"
        if not use_collision_monitor
        else f"/{namespace_vehicle}/cmd_vel_raw"
    )

    return [
        SetRemap(src="/cmd_vel", dst=pub_topic),
        Register.on_start(slam, context) if use_slam else SKIP,
        Register.on_start(map_tf_publisher, context) if not use_gps else SKIP,
        Register.on_start(map_server, context) if map_server is not None else SKIP,
        Register.on_start(amcl, context) if amcl is not None else SKIP,
        Register.on_start(controller_server, context) if use_navigation else SKIP,
        Register.on_start(planner_server, context) if use_navigation else SKIP,
        Register.on_start(behavior_server, context) if use_navigation else SKIP,
        Register.on_start(bt_navigator, context) if use_navigation else SKIP,
        Register.on_start(waypoint_follower, context) if use_navigation else SKIP,
        Register.on_start(collision_monitor_node, context)
        if use_collision_monitor
        else SKIP,
        Register.on_log(lifecycle_manager, "Managed nodes are active", context)
        if lifecycle_nodes
        else SKIP,
        Register.on_log(waypoint_follower_controller, "Controller is ready.", context)
        if use_navigation
        else SKIP,
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the navigation stack.

    Returns:
        LaunchDescription: The launch description containing the actions to be executed.
    """
    return LaunchDescription(
        [
            use_collision_monitor_arg.declaration,
            autostart_arg.declaration,
            use_respawn_arg.declaration,
            use_slam_arg.declaration,
            namespace_vehicle_arg.declaration,
            namespace_lidar_arg.declaration,
            namespace_gps_arg.declaration,
            use_navigation_arg.declaration,
            use_gps_arg.declaration,
            window_size_arg.declaration,
            controller_arg.declaration,
            global_map_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
