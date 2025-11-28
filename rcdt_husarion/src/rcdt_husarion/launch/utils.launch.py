# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchDescription
from launch_ros.actions import Node
from rcdt_launch.environment_configuration import EnvironmentConfiguration
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path
from launch_ros.actions import Node


def create_map_link(self) -> Node | None:
    """Create a static_transform_publisher node that links the platform to the map.

    If the platform is a Vehicle that is using SLAM or navigation, None is returned.
    In this case, a localization node will make the link to the 'map' frame.
    If a vehicle is not using SLAM or navigation, the 'odom' frame is directly linked to the 'map' frame.

    Returns:
        Node | None: A static_transform_publisher node that links the platform with the world or None if not applicable.
    """
    if self.navigation or self.slam or self.use_gps:
        return None
    child_frame = f"{self.namespace}/odom"

    return Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_tf_world",
        arguments=[
            "--frame-id",
            "map",
            "--child-frame-id",
            child_frame,
            "--x",
            f"{self.position[0]}",
            "--y",
            f"{self.position[1]}",
            "--z",
            f"{self.position[2]}",
            "--roll",
            f"{self.orientation[0]}",
            "--pitch",
            f"{self.orientation[1]}",
            "--yaw",
            f"{self.orientation[2]}",
        ],
    )


def create_nav2_launch(self) -> RegisteredLaunchDescription:
    """Create the Nav2 launch description.

    Returns:
        RegisteredLaunchDescription: The launch description for the Nav2.

    Raises:
        ValueError: If no lidar is attached to the vehicle.
    """
    return RegisteredLaunchDescription(
        get_file_path("rcdt_panther", ["launch"], "nav2.launch.py"),
    )


def create_state_publisher() -> Node | None:
    """Create a state publisher node for the robot.

    Returns:
        Node | None: The state publisher node for the robot or None if not applicable.
    """
    if not EnvironmentConfiguration.simulation:
        return None

    return Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        namespace=self.namespace,
        parameters=[
            self.robot_description,
            {"frame_prefix": self.frame_prefix},
            {"publish_frequency": 1000.0},
        ],
    )


def joystick_nodes(self) -> list[Node]:
    """Return the required nodes to control the platform with a joystick.

    Returns:
        list[Node]: The joystick nodes for the platform.
    """
    nodes: list[Node] = []

    pub_topic = f"/{self.namespace}/cmd_vel"
    if self.collision_monitor:
        pub_topic += "_raw"
    if self.platform_type == "panther":
        nodes.append(
            Node(
                package="rcdt_joystick",
                executable="joy_to_twist.py",
                parameters=[
                    {"sub_topic": f"/{self.namespace}/joy"},
                    {"pub_topic": pub_topic},
                    {"config_pkg": "rcdt_panther"},
                ],
                namespace=self.namespace,
            )
        )

    return nodes


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([Register.on_start(create_state_publisher(), context)])
