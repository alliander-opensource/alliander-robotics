# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


import launch_pytest
import pytest
from _pytest.fixtures import SubRequest
from launch import LaunchDescription
from rcdt_launch.platforms.arm import Arm
from rcdt_test.franka.utils import follow_joint_trajectory_goal
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path
from rcdt_utilities.test_utils import (
    assert_for_message,
    get_joint_position,
    wait_for_register,
)
from rclpy.node import Node
from sensor_msgs.msg import JointState

namespace = "franka"


@launch_pytest.fixture(scope="module")
def franka_core_launch(request: SubRequest) -> LaunchDescription:
    """Fixture to create launch file for the franka arm.

    Args:
        request (SubRequest): The pytest request object, used to access command line options

    Returns:
        LaunchDescription: The launch description for the franka arm.
    """
    Arm(platform="franka", position=[0, 0, 0], namespace=namespace)
    launch = RegisteredLaunchDescription(
        get_file_path("rcdt_launch", ["launch"], "bringup.launch.py"),
        launch_arguments={
            "rviz": "False",
            "simulation": request.config.getoption("simulation"),
        },
    )
    return Register.connect_context([launch])


@pytest.mark.launch(fixture=franka_core_launch)
def test_wait_for_register(timeout: int) -> None:
    """Test that the robot is registered in the system to start the tests.

    Args:
        timeout (int): The timeout in seconds to wait for the robot to register.
    """
    wait_for_register(timeout=timeout)


@pytest.mark.launch(fixture=franka_core_launch)
def test_joint_states_published(timeout: int) -> None:
    """Test that joint states are published.

    Args:
        timeout (int): The timeout in seconds to wait for the joint states to be published.
    """
    assert_for_message(JointState, f"{namespace}/joint_states", timeout=timeout)


@pytest.mark.launch(fixture=franka_core_launch)
def test_follow_joint_trajectory_goal(
    test_node: Node, joint_movement_tolerance: float, timeout: int
) -> None:
    """Test following a joint trajectory goal.

    Args:
        test_node (Node): The test node to use for the test.
        joint_movement_tolerance (float): The tolerance for joint movement.
        timeout (int): The timeout in seconds to wait for the joint trajectory goal to be followed.
    """
    positions = [0.15, -0.39, 0.1, -2.06, 0.0, 1.68, 1.01]

    follow_joint_trajectory_goal(
        test_node,
        positions=positions,
        controller=f"{namespace}/fr3_arm_controller",
        timeout=timeout,
    )
    for i in range(7):
        joint_value = get_joint_position(
            namespace=namespace, joint=f"fr3_joint{i + 1}", timeout=timeout
        )
        assert joint_value == pytest.approx(
            positions[i], abs=joint_movement_tolerance
        ), f"The joint value is {joint_value}"
