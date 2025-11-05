# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


import launch_pytest
import pytest
from _pytest.fixtures import SubRequest
from launch import LaunchDescription
from rcdt_launch.robot import Arm
from rcdt_utilities.launch_utils import assert_for_message, get_file_path
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.test_utils import (
    call_trigger_action,
    wait_for_register,
    wait_until_reached_joint,
)
from rclpy.node import Node
from sensor_msgs.msg import JointState

namespace = "franka"


@launch_pytest.fixture(scope="module")
def franka_and_gripper_launch(request: SubRequest) -> LaunchDescription:
    """Fixture to create launch file for the franka core, controllers, and gripper services.

    Args:
        request (SubRequest): The pytest request object, used to access command line options

    Returns:
        LaunchDescription: The launch description for the franka core, controllers, and gripper services.
    """
    Arm(platform="franka", position=[0, 0, 0], namespace=namespace, gripper=True)
    launch = RegisteredLaunchDescription(
        get_file_path("rcdt_launch", ["launch"], "robots.launch.py"),
        launch_arguments={
            "rviz": "False",
            "simulation": request.config.getoption("simulation"),
        },
    )
    return Register.connect_context([launch])


@pytest.mark.launch(fixture=franka_and_gripper_launch)
def test_wait_for_register(timeout: int) -> None:
    """Test that the robot is registered in the system to start the tests.

    Args:
        timeout (int): The timeout in seconds before stopping the test.
    """
    wait_for_register(timeout=timeout)


@pytest.mark.launch(fixture=franka_and_gripper_launch)
def test_joint_states_published(timeout: int) -> None:
    """Test that joint states are published.

    Args:
        timeout (int): The timeout in seconds before stopping the test.
    """
    assert_for_message(JointState, f"{namespace}/joint_states", timeout=timeout)


@pytest.mark.launch(fixture=franka_and_gripper_launch)
@pytest.mark.parametrize(
    "action, expected_value",
    [
        (f"{namespace}/gripper/close", 0.00),
        (f"{namespace}/gripper/open", 0.04),
    ],
)
def test_gripper_action(
    action: str,
    expected_value: float,
    test_node: Node,
    finger_joint_fault_tolerance: float,
    timeout: int,
) -> None:
    """Test gripper open/close action and verify joint state.

    Args:
        action (str): The action to call.
        expected_value (float): The expected joint value after the action.
        test_node (Node): The test node to use for the test.
        finger_joint_fault_tolerance (float): The tolerance for the finger joint position.
        timeout (int): The timeout in seconds before stopping the test.
    """
    assert call_trigger_action(test_node, action, timeout=timeout) is True
    reached_goal, joint_value = wait_until_reached_joint(
        namespace=namespace,
        joint="fr3_finger_joint1",
        expected_value=expected_value,
        tolerance=finger_joint_fault_tolerance,
        timeout_sec=timeout,
    )
    assert reached_goal is True, (
        f"The joint did not reach the joint. Currently {joint_value}, expected {expected_value}"
    )
