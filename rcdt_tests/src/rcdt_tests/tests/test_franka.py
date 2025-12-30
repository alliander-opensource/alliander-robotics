import pytest
from rcdt_utilities.config_objects import Arm
from rclpy.node import Node
from sensor_msgs.msg import JointState

from ..utils import (
    assert_for_message,
    call_move_to_configuration_service,
    call_trigger_action,
    follow_joint_trajectory_goal,
    get_joint_position,
    wait_until_reached_joint,
)

arm = Arm("franka", gripper=True, moveit=True)
PLATFORMS = {arm.name: arm}


def test_joint_states_published() -> None:
    """Test that joint states are published."""
    assert_for_message(JointState, f"/{arm.namespace}/joint_states", timeout=100)


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
        controller=f"{arm.namespace}/fr3_arm_controller",
        timeout=timeout,
    )
    for i in range(7):
        joint_value = get_joint_position(
            namespace=arm.namespace, joint=f"fr3_joint{i + 1}", timeout=timeout
        )
        assert joint_value == pytest.approx(
            positions[i], abs=joint_movement_tolerance
        ), f"The joint value is {joint_value}"


@pytest.mark.parametrize(
    "action, expected_value",
    [
        (f"{arm.namespace}/gripper/close", 0.00),
        (f"{arm.namespace}/gripper/open", 0.04),
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
        namespace=arm.namespace,
        joint="fr3_finger_joint1",
        expected_value=expected_value,
        tolerance=finger_joint_fault_tolerance,
        timeout_sec=timeout,
    )
    assert reached_goal is True, (
        f"The joint did not reach the joint. Currently {joint_value}, expected {expected_value}"
    )


def test_move_to_drop_configuration(
    test_node: Node, joint_movement_tolerance: float, timeout: int
) -> None:
    """Test that MoveIt can move to a configuration.

    Args:
        test_node (Node): The test node to use for the test.
        joint_movement_tolerance (float): The tolerance for joint movement.
        timeout (int): The timeout in seconds before stopping the test.
    """
    assert call_move_to_configuration_service(
        test_node, arm.namespace, "drop", timeout=timeout
    ), "Failed to call move_to_configuration service."
    drop_values = [-1.57079632679, -0.65, 0, -2.4, 0, 1.75, 0.78539816339]
    for i in range(7):
        joint_value = get_joint_position(
            namespace=arm.namespace, joint=f"fr3_joint{i + 1}", timeout=timeout
        )
        assert joint_value == pytest.approx(
            drop_values[i], abs=joint_movement_tolerance
        ), f"The joint value is {joint_value}, while expecting {drop_values[i]}"
