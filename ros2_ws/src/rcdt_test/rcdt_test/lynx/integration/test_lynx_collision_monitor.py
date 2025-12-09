# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


import time

import launch_pytest
import pytest
import rclpy
from _pytest.fixtures import SubRequest
from geometry_msgs.msg import TwistStamped
from launch import LaunchDescription
from rcdt_launch.environment_configuration import EnvironmentConfiguration
from rcdt_launch.platforms.lidar import Lidar
from rcdt_launch.platforms.vehicle import Vehicle
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path
from rcdt_utilities.test_utils import (
    assert_for_message,
    call_trigger_service,
    wait_for_register,
    wait_for_subscriber,
)
from rclpy.node import Node
from sensor_msgs.msg import JointState

namespace = "lynx"


@launch_pytest.fixture(scope="module")
def lynx_launch(request: SubRequest) -> LaunchDescription:
    """Fixture to create launch file for lynx robot.

    Args:
        request (SubRequest): The pytest request object, used to access command line options

    Returns:
        LaunchDescription: The launch description for the lynx robot.
    """
    EnvironmentConfiguration.world = "walls.sdf"
    vehicle = Vehicle(
        platform="lynx",
        position=[4.0, 0, 0.13],
        namespace=namespace,
        collision_monitor=True,
    )
    Lidar("ouster", [0.1, -0.1, 0.25], parent=vehicle)
    launch = RegisteredLaunchDescription(
        get_file_path("rcdt_launch", ["launch"], "bringup.launch.py"),
        launch_arguments={
            "rviz": "False",
            "simulation": request.config.getoption("simulation"),
        },
    )
    return Register.connect_context([launch])


@pytest.mark.launch(fixture=lynx_launch)
def test_wait_for_register(timeout: int) -> None:
    """Test that the lynx core is registered in the RCDT.

    Args:
        timeout (int): The timeout in seconds to wait for the lynx core to register.
    """
    wait_for_register(timeout=timeout)


@pytest.mark.launch(fixture=lynx_launch)
def test_joint_states_published(timeout: int) -> None:
    """Test that the joint states are published.

    Args:
        timeout (int): The timeout in seconds to wait for the joint states to be published.
    """
    assert_for_message(JointState, f"/{namespace}/joint_states", timeout=timeout)


@pytest.mark.launch(fixture=lynx_launch)
def test_e_stop_request_reset(
    request: SubRequest, test_node: Node, timeout: int
) -> None:
    """Test that the E-Stop request service can be called to unlock the Lynx.

    Args:
        request (SubRequest): The pytest request object, used to access command line options
        test_node (Node): The ROS 2 node to use for the test.
        timeout (int): The timeout in seconds to wait before failing the test.
    """
    if request.config.getoption("simulation"):
        pytest.skip("E-Stop is not available.")  # ty: ignore[call-non-callable]
    assert (
        call_trigger_service(
            node=test_node,
            service_name=f"/{namespace}/hardware/e_stop_reset",
            timeout=timeout,
        )
        is True
    )


@pytest.mark.launch(fixture=lynx_launch)
def test_collision_monitoring(test_node: Node, timeout: int) -> None:
    """Test that cmd_vel is reduced to 70% by the collision monitor.

    Args:
        test_node (Node): The ROS 2 node to use for the test.
        timeout (int): The timeout in seconds to wait for the wheels to turn.
    """
    input_velocity = 0.0001
    expected_output = input_velocity * 0.7

    publisher = test_node.create_publisher(
        TwistStamped, f"/{namespace}/cmd_vel_raw", 10
    )
    result = {}

    def callback_function_cmd_vel(msg: TwistStamped) -> None:
        """Callback function to handle messages from the state topic.

        Args:
            msg (TwistStamped): The message received from the state topic.
        """
        result["output_velocity"] = msg.twist.linear.x

    test_node.create_subscription(
        msg_type=TwistStamped,
        topic=f"/{namespace}/cmd_vel",
        callback=callback_function_cmd_vel,
        qos_profile=10,
    )

    wait_for_subscriber(publisher, timeout)
    msg = TwistStamped()
    msg.twist.linear.x = input_velocity

    publish_duration = 30  # seconds
    publish_rate_sec = 0.1  # seconds
    deadline = time.monotonic() + publish_duration

    while (
        time.monotonic() < deadline and result.get("output_velocity") != expected_output
    ):
        publisher.publish(msg)
        rclpy.spin_once(test_node, timeout_sec=publish_rate_sec)

    assert result.get("output_velocity") == expected_output, (
        f"Expected output velocity to be ~{expected_output}, got {result.get('output_velocity')}"
    )
