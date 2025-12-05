# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import gc

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import LifecycleNode, Node, SetRemap
from rcdt_utilities.adapted_yaml import AdaptedYaml
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.launch_utils import SKIP
from rcdt_utilities.register import Register
from rcdt_utilities.ros_utils import get_file_path

namespace_vehicle_arg = LaunchArgument("namespace_vehicle", "")
namespace_lidar_arg = LaunchArgument("namespace_lidar", "")
namespace_gps_arg = LaunchArgument("namespace_gps", "")

use_collision_monitor_arg = LaunchArgument("collision_monitor", False, [True, False])
use_slam_arg = LaunchArgument("slam", False, [True, False])
use_navigation_arg = LaunchArgument("navigation", False, [True, False])
use_gps_arg = LaunchArgument("use_gps", False, [True, False])

window_size_arg = LaunchArgument("window_size", 10)
controller_arg = LaunchArgument(
    "controller",
    "vector_pursuit",
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
    "map", "simulation_map", ["simulation_map", "ipkw", "ipkw_buiten"]
)


def launch_setup(context: LaunchContext) -> list:  # noqa: PLR0915
    """Setup the launch description for the navigation stack.

    Args:
        context (LaunchContext): The launch context.

    Raises:
        ValueError: If GPS is enabled but no namespace is provided.

    Returns:
        list: A list of actions to be executed in the launch description.
    """
    # Retrieve launch argument values:
    namespace_vehicle = namespace_vehicle_arg.string_value(context)
    namespace_lidar = namespace_lidar_arg.string_value(context)
    namespace_gps = namespace_gps_arg.string_value(context)

    use_collision_monitor = use_collision_monitor_arg.bool_value(context)
    use_slam = use_slam_arg.bool_value(context)
    use_navigation = use_navigation_arg.bool_value(context)
    use_gps = use_gps_arg.bool_value(context)

    window_size = window_size_arg.int_value(context)
    controller = controller_arg.string_value(context)
    global_map = global_map_arg.string_value(context)

    # Define configuration:
    lifecycle_nodes_names = []
    use_map_localization = True
    plugins = ["static_layer", "obstacle_layer", "inflation_layer"]

    if use_collision_monitor:
        lifecycle_nodes_names.append("collision_monitor")
    if use_slam:
        lifecycle_nodes_names.append("slam_toolbox")
        use_map_localization = False
    if use_gps:
        if not namespace_gps:
            raise ValueError("Namespace for GPS must be provided when using GPS.")
        use_map_localization = False
    if use_navigation:
        if use_map_localization:
            lifecycle_nodes_names.extend(
                [
                    "map_server",
                    "amcl",
                ]
            )
        else:
            plugins.remove("static_layer")
        lifecycle_nodes_names.extend(
            [
                "controller_server",
                "planner_server",
                "behavior_server",
                "bt_navigator",
                "waypoint_follower",
            ]
        )

    # Define parameters:
    slam_params = AdaptedYaml(
        get_file_path("rcdt_panther", ["config"], "slam_params.yaml"),
        {
            "odom_frame": f"{namespace_vehicle}/odom",
            "base_frame": f"{namespace_vehicle}/base_footprint",
            "scan_topic": f"/{namespace_lidar}/scan",
        },
        root_key=namespace_vehicle,
    )

    amcl_params = AdaptedYaml(
        get_file_path("rcdt_panther", ["config", "nav2"], "amcl.yaml"),
        {
            "base_frame_id": f"{namespace_vehicle}/base_footprint",
            "odom_frame_id": f"{namespace_vehicle}/odom",
            "scan_topic": f"/{namespace_lidar}/scan",
        },
        root_key=namespace_vehicle,
    )

    local_costmap_params = AdaptedYaml(
        get_file_path("rcdt_panther", ["config", "nav2"], "local_costmap.yaml"),
        {
            "global_frame": f"{namespace_vehicle}/odom",
            "robot_base_frame": f"{namespace_vehicle}/base_footprint",
            "rolling_window": use_gps,
            "plugins": plugins,
        },
        root_key=namespace_vehicle,
    )

    global_costmap_params = AdaptedYaml(
        get_file_path("rcdt_panther", ["config", "nav2"], "global_costmap.yaml"),
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
        root_key=namespace_vehicle,
    )

    controller_server_params = AdaptedYaml(
        get_file_path("rcdt_panther", ["config", "nav2"], "controller_server.yaml"),
        {"odom_topic": f"/{namespace_vehicle}/odom"},
        root_key=namespace_vehicle,
    )

    behavior_server_params = AdaptedYaml(
        get_file_path("rcdt_panther", ["config", "nav2"], "behavior_server.yaml"),
        {
            "local_frame": f"{namespace_vehicle}/odom",
            "robot_base_frame": f"{namespace_vehicle}/base_footprint",
        },
        root_key=namespace_vehicle,
    )

    follow_path_params = AdaptedYaml(
        get_file_path(
            "rcdt_panther", ["config", "nav2", "controllers"], f"{controller}.yaml"
        ),
        {},
        root_key=namespace_vehicle,
    )

    bt_navigator_params = AdaptedYaml(
        get_file_path("rcdt_panther", ["config", "nav2"], "bt_navigator.yaml"),
        {
            "default_nav_to_pose_bt_xml": get_file_path(
                "rcdt_panther", ["config", "nav2"], "behavior_tree.xml"
            ),
            "robot_base_frame": f"{namespace_vehicle}/base_footprint",
            "odom_topic": f"/{namespace_vehicle}/odom",
        },
        root_key=namespace_vehicle,
    )

    planner_server_params = AdaptedYaml(
        get_file_path("rcdt_panther", ["config", "nav2"], "planner_server.yaml"),
        {},
        root_key=namespace_vehicle,
    )

    collision_monitor_params = AdaptedYaml(
        get_file_path("rcdt_panther", ["config", "nav2"], "collision_monitor.yaml"),
        {
            "base_frame_id": f"{namespace_vehicle}/base_footprint",
            "odom_frame_id": f"{namespace_vehicle}/odom",
            "cmd_vel_in_topic": f"/{namespace_vehicle}/cmd_vel_raw",
            "cmd_vel_out_topic": f"/{namespace_vehicle}/cmd_vel",
            "scan": {
                "topic": f"/{namespace_lidar}/scan",
            },
        },
        root_key=namespace_vehicle,
    )

    # Define nodes:
    _slam = LifecycleNode(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        parameters=[
            slam_params.file,
            {
                "use_lifecycle_manager": True,
            },
        ],
        namespace=namespace_vehicle,
        remappings=[("/map", f"/{namespace_vehicle}/map")],
    )

    _map_server = LifecycleNode(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        parameters=[
            {
                "yaml_filename": get_file_path(
                    "rcdt_panther", ["config", "maps"], str(global_map) + ".yaml"
                ),
                "topic_name": f"/{namespace_vehicle}/map",
            }
        ],
        namespace=namespace_vehicle,
    )

    _amcl = LifecycleNode(
        package="nav2_amcl",
        executable="amcl",
        name="amcl",
        parameters=[amcl_params.file],
        namespace=namespace_vehicle,
        remappings=[(f"/{namespace_vehicle}/initialpose", "/initialpose")],
    )

    _controller_server = LifecycleNode(
        package="nav2_controller",
        executable="controller_server",
        name="controller_server",
        parameters=[
            local_costmap_params.file,
            controller_server_params.file,
            follow_path_params.file,
        ],
        namespace=namespace_vehicle,
    )

    _planner_server = LifecycleNode(
        package="nav2_planner",
        executable="planner_server",
        name="planner_server",
        parameters=[
            global_costmap_params.file,
            planner_server_params.file,
        ],
        namespace=namespace_vehicle,
    )

    _behavior_server = LifecycleNode(
        package="nav2_behaviors",
        executable="behavior_server",
        name="behavior_server",
        parameters=[behavior_server_params.file],
        namespace=namespace_vehicle,
    )

    _bt_navigator = LifecycleNode(
        package="nav2_bt_navigator",
        executable="bt_navigator",
        name="bt_navigator",
        parameters=[bt_navigator_params.file],
        namespace=namespace_vehicle,
    )

    _collision_monitor = LifecycleNode(
        package="nav2_collision_monitor",
        executable="collision_monitor",
        name="collision_monitor",
        parameters=[collision_monitor_params.file],
        namespace=namespace_vehicle,
    )

    remappings = []
    if use_gps:
        remappings.append(("/gps/fix", f"/{namespace_gps}/fix"))
        remappings.append(("/fromLL", f"/{namespace_gps}/fromLL"))

    _waypoint_follower = LifecycleNode(
        package="nav2_waypoint_follower",
        executable="waypoint_follower",
        name="waypoint_follower",
        namespace=namespace_vehicle,
        remappings=remappings,
    )

    # Automatically collect the nodes to start, based on the names in lifecycle_nodes_names:
    lifecycle_nodes = []
    for obj in gc.get_objects():
        if isinstance(obj, LifecycleNode):
            state = obj.__getstate__()
            if state["_Node__node_name"] in lifecycle_nodes_names:
                lifecycle_nodes.append(obj)

    lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_navigation",
        parameters=[{"autostart": True}, {"node_names": lifecycle_nodes_names}],
        namespace=namespace_vehicle,
    )

    nav2_manager = Node(
        package="rcdt_panther",
        executable="nav2_manager.py",
        namespace=namespace_vehicle,
        remappings=remappings,
    )

    pub_topic = (
        f"/{namespace_vehicle}/cmd_vel"
        if not use_collision_monitor
        else f"/{namespace_vehicle}/cmd_vel_raw"
    )

    return [
        SetRemap(src="/cmd_vel", dst=pub_topic),
        *[Register.on_start(node, context) for node in lifecycle_nodes],
        Register.on_log(lifecycle_manager, "Managed nodes are active", context),
        Register.on_log(nav2_manager, "Controller is ready.", context)
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
            namespace_vehicle_arg.declaration,
            namespace_lidar_arg.declaration,
            namespace_gps_arg.declaration,
            use_collision_monitor_arg.declaration,
            use_slam_arg.declaration,
            use_navigation_arg.declaration,
            use_gps_arg.declaration,
            window_size_arg.declaration,
            controller_arg.declaration,
            global_map_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
