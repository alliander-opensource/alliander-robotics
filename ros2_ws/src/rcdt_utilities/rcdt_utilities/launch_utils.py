# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
from launch import LaunchDescriptionEntity
from launch_ros.actions import Node
from rcdt_launch.environment_configuration import EnvironmentConfiguration
from rcdt_launch.platforms.arm import Arm
from rcdt_launch.platforms.vehicle import Vehicle

from rcdt_utilities.register import RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path

SKIP = LaunchDescriptionEntity()


def reset() -> None:
    """Reset the platform class to its initial state."""
    EnvironmentConfiguration.platforms = []
    EnvironmentConfiguration.platform_indices = {}
    EnvironmentConfiguration.names = []
    EnvironmentConfiguration.bridge_topics = []


def create_state_publishers() -> list[Node]:
    """Create state publisher nodes for all platforms.

    Returns:
        list[Node]: A list of all state publisher nodes.
    """
    nodes = []
    for platform in EnvironmentConfiguration.platforms:
        node = platform.create_state_publisher()
        if isinstance(node, Node):
            nodes.append(node)
    return nodes


def order_platforms() -> None:
    """Order the platforms in a specific order.

    This is required, since a child platform can only be spawned after its parent platform is spawned.
    Currently the order is hardcoded as [vehicles -> arms -> sensors] to fullfill this requirement.
    This method possibly requires more logic when other platforms are added in the future.

    Raises:
        ValueError: If an unknown platform is encountered.
    """
    order = [
        "panther",
        "lynx",
        "franka",
        "velodyne",
        "ouster",
        "realsense",
        "zed",
        "nmea",
        "axis",
    ]

    for platform in EnvironmentConfiguration.platforms:
        if platform.platform_type not in order:
            raise ValueError(f"Unknown platform to order: {platform.platform_type}")

    EnvironmentConfiguration.platforms = sorted(
        EnvironmentConfiguration.platforms,
        key=lambda platform: order.index(platform.platform_type),
    )


def create_gazebo_launch(load_gazebo_ui: bool) -> RegisteredLaunchDescription:
    """Create the Gazebo launch description.

    Args:
        load_gazebo_ui (bool): Whether to load the Gazebo UI or not.

    Returns:
        RegisteredLaunchDescription: The Gazebo launch description.
    """
    platforms = []
    positions = []
    orientations = []
    parents = []
    parent_links = []

    for platform in EnvironmentConfiguration.platforms:
        platforms.append(platform.namespace)
        positions.append(",".join(map(str, platform.position)))
        orientations.append(",".join(map(str, platform.orientation)))
        parent = platform.parent
        if parent is not None:
            parents.append(parent.namespace)
            parent_links.append(platform.parent_link)
        else:
            parents.append("none")
            parent_links.append("none")

    return RegisteredLaunchDescription(
        get_file_path("rcdt_gazebo", ["launch"], "gazebo_robot.launch.py"),
        launch_arguments={
            "load_gazebo_ui": str(load_gazebo_ui),
            "world": EnvironmentConfiguration.world,
            "platforms": " ".join(platforms),
            "positions": " ".join(positions),
            "orientations": " ".join(orientations),
            "parents": " ".join(parents),
            "parent_links": " ".join(parent_links),
            "bridge_topics": " ".join(EnvironmentConfiguration.bridge_topics),
        },
    )


def create_hardware_interfaces() -> list[RegisteredLaunchDescription]:
    """Create hardware interface launch descriptions for the platforms.

    Returns:
        list[RegisteredLaunchDescription]: A list of all hardware interface launch descriptions.
    """
    hardware_interfaces = []
    if EnvironmentConfiguration.simulation:
        return hardware_interfaces

    for platform in EnvironmentConfiguration.platforms:
        if isinstance(platform, Arm) and platform.platform_type == "franka":
            hardware_interfaces.append(
                RegisteredLaunchDescription(
                    get_file_path("rcdt_franka", ["launch"], "robot.launch.py"),
                    launch_arguments={
                        "namespace": platform.namespace,
                        "ip_address": platform.ip_address,
                    },
                )
            )
    return hardware_interfaces


def create_parent_links() -> list[Node]:
    """Create a list of nodes that link all the platforms to their parent.

    Returns:
        list[Node]: A list of all the required static_transform_publisher nodes.
    """
    nodes = []
    for platform in EnvironmentConfiguration.platforms:
        if platform.parent is not None:
            nodes.append(platform.create_parent_link())
    return nodes


def create_controllers() -> list[RegisteredLaunchDescription]:
    """Create controllers for all platforms.

    Returns:
        list[RegisteredLaunchDescription]: A list of all controller launch descriptions.
    """
    controllers = []
    for platform in EnvironmentConfiguration.platforms:
        if not EnvironmentConfiguration.simulation and platform.platform_type in {
            "lynx",
            "panther",
        }:
            continue
        if platform.controller_path is not None:
            controllers.append(platform.create_controller())
    return controllers


def create_launch_descriptions() -> list[RegisteredLaunchDescription]:
    """Create launch descriptions for all platforms.

    Note that the launch descriptions for the platforms are launched in reversed order.
    This is done so that the nodes required for sensors (childs) are launched first.
    Next we launch nodes required for the parent platforms (like Nav2), which depend on the sensors.

    Returns:
        list[RegisteredLaunchDescription]: A list of all launch descriptions.
    """
    launch_descriptions = []
    for platform in reversed(EnvironmentConfiguration.platforms):
        launch_description = platform.create_launch_description()
        if launch_description != []:
            launch_descriptions.extend(launch_description)
    return launch_descriptions


def create_joystick_nodes() -> list[Node]:
    """Create joystick nodes for all platforms.

    Returns:
        list[Node]: A list of all joystick nodes.

    Raises:
        ValueError: If more than one vehicle or arm is linked to the joystick.
    """
    nodes = []

    # At the moment, we only support one vehicle and one arm being linked to the joystick.
    # The vehicle (base) is linked to the B button and the arm to the A button.
    # The X button is always available to stop joystick control of all platforms.
    buttons = [2]  # X button (to stop)
    services = [False]
    topics = [""]
    vehicle_linked = False
    arm_linked = False
    for platform in EnvironmentConfiguration.platforms:
        button = None
        if isinstance(platform, Vehicle):
            if vehicle_linked:
                raise ValueError("Only one vehicle can be linked to the joystick.")
            button = 1  # B button (for base)
            vehicle_linked = True
        elif isinstance(platform, Arm):
            if arm_linked:
                raise ValueError("Only one arm can be linked to the joystick.")
            button = 0  # A button (for arm)
            arm_linked = True
        if button is not None:
            buttons.append(button)
            services.append(False)
            topics.append(f"/{platform.namespace}/joy")
            nodes.extend(platform.joystick_nodes())

    # If none of the platforms require joystick nodes, return:
    if len(nodes) == 0:
        return nodes

    # Add the general joystick node:
    nodes.append(
        Node(
            package="joy",
            executable="game_controller_node",
            parameters=[
                {"sticky_buttons": True},
            ],
        )
    )

    # Add the joy topic manager node:
    nodes.append(
        Node(
            package="rcdt_joystick",
            executable="joy_topic_manager.py",
            parameters=[
                {"buttons": buttons},
                {"services": services},
                {"topics": topics},
            ],
        )
    )
    return nodes


def create_map_links() -> list[Node]:
    """Create a list of nodes that link all the platforms to the 'map' frame.

    Returns:
        list[Node]: A list of all the static_transform_publisher nodes linking the platforms to the 'map' frame.
    """
    nodes = []
    for platform in EnvironmentConfiguration.platforms:
        if platform.parent is None:
            node = platform.create_map_link()
            if isinstance(node, Node):
                nodes.append(node)
    return nodes
