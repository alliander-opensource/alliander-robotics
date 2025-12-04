# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import contextlib
import copy
import itertools
import sys
import time
from functools import partial
from typing import Callable

import launch_pytest
import pytest
import rclpy
import termcolor
from _pytest.fixtures import SubRequest
from geographic_msgs.msg import GeoPath, GeoPoseStamped
from geometry_msgs.msg import PoseStamped, TransformStamped
from launch import LaunchDescription
from rcdt_launch.environment_configuration import EnvironmentConfiguration
from rcdt_launch.platforms.gps import GPS
from rcdt_launch.platforms.lidar import Lidar
from rcdt_launch.platforms.vehicle import Vehicle
from rcdt_utilities.launch_utils import reset
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path
from rcdt_utilities.test_utils import (
    assert_for_message,
    call_trigger_service,
    wait_for_register,
    wait_for_subscriber,
)
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import JointState, NavSatFix
from tf2_ros import TransformException  # ty: ignore[unresolved-import]
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener

launch_fixtures = []


def get_tests(namespace_vehicle: str, namespace_gps: str) -> dict:  # noqa: PLR0915
    """Get the Nav2 tests.

    Args:
        namespace_vehicle (str): The namespace of the vehicle.
        namespace_gps (str): The namespace of the GPS.

    Returns:
        dict: A dictionary containing the tests.
    """

    def test_wait_for_register(_self: object, timeout: int) -> None:
        """Test that the panther core is registered in the RCDT.

        Args:
            _self (object): The test class instance.
            timeout (int): The timeout in seconds.
        """
        wait_for_register(timeout=timeout)

    def test_joint_states_published(_self: object, timeout: int) -> None:
        """Test that the joint states are published.

        Args:
            _self (object): The test class instance.
            timeout (int): The timeout in seconds.
        """
        assert_for_message(
            JointState, f"/{namespace_vehicle}/joint_states", timeout=timeout
        )

    def test_e_stop_request_reset(
        _self: object, request: SubRequest, test_node: Node, timeout: int
    ) -> None:
        """Test that the E-Stop request service can be called to unlock the Panther.

        Args:
            _self (object): The test class instance.
            request (SubRequest): The pytest request object, used to access command line options
            test_node (Node): The ROS 2 node to use for the test.
            timeout (int): The timeout in seconds.
        """
        if request.config.getoption("simulation"):
            pytest.skip("E-Stop is not available.")  # ty: ignore[call-non-callable]
        assert (
            call_trigger_service(
                node=test_node,
                service_name=f"/{namespace_vehicle}/hardware/e_stop_reset",
                timeout=timeout,
            )
            is True
        )

    def test_goal_pose(
        _self: object,
        test_node: Node,
        navigation_distance_tolerance: float,
        timeout: int,
    ) -> None:
        """Test that navigation to a goal pose is successful.

        Args:
            _self (object): The test class instance.
            test_node (Node): The ROS 2 node to use for the test.
            navigation_distance_tolerance (float): The tolerance for navigation.
            timeout (int): The timeout in seconds.

        Raises:
            TimeoutError: When a timeout occurs.
        """
        # 1) Obtain current pose in map frame:
        tf_buffer = Buffer()
        TransformListener(tf_buffer, test_node)
        current_pose = TransformStamped()

        start_time = time.time()
        while current_pose == TransformStamped():
            rclpy.spin_once(test_node, timeout_sec=0)
            with contextlib.suppress(TransformException):
                current_pose = tf_buffer.lookup_transform(
                    "map", f"{namespace_vehicle}/base_link", Time()
                )
            if time.time() - start_time > timeout:
                raise TimeoutError()

        # 2) Publish goal pose 1 meter in front of current position:
        goal_pose = PoseStamped()
        goal_pose.header.frame_id = "map"
        goal_pose.pose.position.x = current_pose.transform.translation.x + 1
        goal_pose.pose.position.y = current_pose.transform.translation.y
        goal_pose.pose.position.z = current_pose.transform.translation.z

        publisher = test_node.create_publisher(PoseStamped, "/goal_pose", 10)
        wait_for_subscriber(publisher, timeout)
        publisher.publish(goal_pose)
        test_node.get_logger().info("Published goal pose for navigation.")

        # 3) Wait until goal is reached within tolerance:
        start_time = time.time()
        distance: float = sys.float_info.max
        while distance > navigation_distance_tolerance:
            rclpy.spin_once(test_node, timeout_sec=0)
            with contextlib.suppress(TransformException):
                current_pose = tf_buffer.lookup_transform(
                    "map", f"{namespace_vehicle}/base_link", Time()
                )
            distance = abs(
                current_pose.transform.translation.x - goal_pose.pose.position.x
            )
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"Distance is {distance} while tolerance is {navigation_distance_tolerance}."
                )

        # 4) Stop navigation, since the goal can be reached before the navigation is finished due to tolerance:
        assert call_trigger_service(
            test_node, f"/{namespace_vehicle}/nav2_manager/stop", timeout
        )

    def test_gps_navigation(
        _self: object, test_node: Node, navigation_degree_tolerance: float, timeout: int
    ) -> None:
        """Test that GPS navigation to a goal pose is successful.

        Args:
            _self (object): The test class instance.
            test_node (Node): The ROS 2 node to use for the test.
            navigation_degree_tolerance (float): The tolerance for navigation.
            timeout (int): The timeout in seconds.

        Raises:
            TimeoutError: When a timeout occurs.
        """
        # 1) Obtain current GPS location:
        current_nav_sat = NavSatFix()

        def callback(msg: NavSatFix) -> None:
            current_nav_sat.latitude = msg.latitude
            current_nav_sat.longitude = msg.longitude

        test_node.create_subscription(
            NavSatFix, f"/{namespace_gps}/gps/fix", callback, 10
        )

        start_time = time.time()
        while current_nav_sat == NavSatFix():
            rclpy.spin_once(test_node, timeout_sec=0)
            if time.time() - start_time > timeout:
                raise TimeoutError("Timeout while waiting for current GPS location.")

        # 2) Publish goal GPS location 1e-5 degrees north of current location:
        goal_nav_sat = copy.deepcopy(current_nav_sat)
        goal_nav_sat.latitude += 1e-5

        publisher = test_node.create_publisher(GeoPath, "/gps_waypoints", 10)
        wait_for_subscriber(publisher, timeout)
        goal_msg = GeoPath()
        goal_pose = GeoPoseStamped()
        goal_pose.pose.position.latitude = goal_nav_sat.latitude
        goal_pose.pose.position.longitude = goal_nav_sat.longitude
        goal_msg.poses.append(goal_pose)
        publisher.publish(goal_msg)

        # 3) Wait until goal is reached within tolerance:
        start_time = time.time()
        distance: float = sys.float_info.max
        while distance > navigation_degree_tolerance:
            rclpy.spin_once(test_node, timeout_sec=0)
            distance = abs(current_nav_sat.latitude - goal_nav_sat.latitude)
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"Distance is {distance} while tolerance is {navigation_degree_tolerance}."
                )

        # 4) Stop navigation, since the goal can be reached before the navigation is finished due to tolerance:
        assert call_trigger_service(
            test_node, f"/{namespace_vehicle}/nav2_manager/stop", timeout
        )

    # Collect all test methods defined above
    tests = {
        name: obj
        for name, obj in locals().items()
        if callable(obj) and name.startswith("test_")
    }
    return tests


@launch_pytest.fixture(scope="class")
def launch_fixture_wrapper(request: SubRequest) -> Callable:
    """Wrapper fixture to select the dynamically created launch fixture.

    Args:
        request (SubRequest): The pytest request object, used to access command line options.

    Returns:
        Callable: The selected launch fixture.
    """
    return launch_fixtures.pop(0)(request)


def launch_fixture(
    request: SubRequest, platforms: tuple[str, str, str]
) -> LaunchDescription:
    """Fixture to launch the selected platforms.

    Args:
        request (SubRequest): The pytest request object, used to access command line options.
        platforms (tuple[str, str, str]): The platforms to launch.

    Returns:
        LaunchDescription: The launch description containing the platform setups.
    """
    reset()
    print(termcolor.colored(f"Start Nav2 test with {platforms}", "green"))

    vehicle_platform, lidar_platform, gps_platform = platforms
    vehicle = Vehicle(
        platform=vehicle_platform,
        position=[0, 0, 0.2],
        namespace=vehicle_platform,
        navigation=True,
        use_gps=True,
    )
    Lidar(
        platform=lidar_platform,
        position=[0.13, -0.13, 0.35],
        parent=vehicle,
        namespace=lidar_platform,
    )
    GPS(
        platform=gps_platform,
        position=[0, 0, 0.35],
        parent=vehicle,
        namespace=gps_platform,
    )
    EnvironmentConfiguration.world = "map_5.940906_51.966960"

    launch = RegisteredLaunchDescription(
        get_file_path("rcdt_launch", ["launch"], "bringup.launch.py"),
        launch_arguments={
            "rviz": "False",
            "simulation": request.config.getoption("simulation"),
        },
    )
    return Register.connect_context([launch])


vehicle_list = ["panther"]
lidar_list = ["velodyne", "ouster"]
gps_list = ["nmea"]

# Dynamically create test classes for each combination of platforms
for platforms in itertools.product(vehicle_list, lidar_list, gps_list):
    vehicle_platform, lidar_platform, gps_platform = platforms

    launch_fixtures.append(partial(launch_fixture, platforms=platforms))

    test_class = type(
        f"TestNav2_{vehicle_platform}_{lidar_platform}_{gps_platform}",
        (object,),
        get_tests(vehicle_platform, gps_platform),
    )
    pytest.mark.launch(fixture=launch_fixture_wrapper)(test_class)
    globals()[test_class.__name__] = test_class
