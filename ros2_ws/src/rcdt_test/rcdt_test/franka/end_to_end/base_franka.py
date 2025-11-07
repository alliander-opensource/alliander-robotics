# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


import pytest
from geometry_msgs.msg import Pose
from rcdt_utilities.launch_utils import assert_for_message
from rcdt_utilities.test_utils import (
    assert_joy_topic_switch,
    assert_movements_with_joy,
    publish_for_duration,
    wait_for_register,
    wait_for_subscriber,
    wait_until_reached_joint,
)
from rclpy.node import Node
from sensor_msgs.msg import JointState, Joy


def get_tests(namespace: str) -> dict:
    """Test class for the Franka robot.

    Args:
        namespace (str): The namespace of the robot.

    Returns:
        dict: A dictionary containing the test methods.
    """

    def test_wait_for_register(_self: object, timeout: int) -> None:
        """Test that the robot is registered in the system to start the tests.

        Args:
            _self (object): The test class instance.
            timeout (int): The timeout in seconds to wait for the robot to register.
        """
        wait_for_register(timeout=timeout)

    def test_joint_states_published(_self: object, timeout: int) -> None:
        """Test that joint states are published.

        Args:
            _self (object): The test class instance.
            timeout (int): The timeout in seconds to wait for the joint states to be published.
        """
        assert_for_message(JointState, f"/{namespace}/joint_states", timeout=timeout)

    def test_switch_joy_to_franka_topic(
        _self: object, test_node: Node, timeout: int
    ) -> None:
        """Test to see if the switch to Franka mode is correct.

        Args:
            _self (object): The test class instance.
            test_node (Node): The test node to use for the test.
            timeout (int): The timeout in seconds to wait for the joy topic to switch.
        """
        assert_joy_topic_switch(
            node=test_node,
            expected_topic=f"/{namespace}/joy",
            button_config=[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            timeout=timeout,
        )

    @pytest.mark.parametrize(
        "buttons, expected_value",
        [
            ([1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0], 0.04),
            ([1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1], 0.0),
        ],
    )
    def test_joy_gripper_node(
        _self: object,
        buttons: list[int],
        expected_value: float,
        test_node: Node,
        finger_joint_fault_tolerance: float,
        timeout: int,
    ) -> None:
        """Test the gripper node with the joystick.

        Args:
            _self (object): The test class instance.
            buttons (list[int]): The button configuration to use for the test.
            expected_value (float): The expected value of the finger joint after the test.
            test_node (Node): The test node to use for the test.
            finger_joint_fault_tolerance (float): The tolerance for the finger joint fault.
            timeout (int): The timeout in seconds to wait for the gripper node to respond.
        """
        pub = test_node.create_publisher(Joy, "/joy", 10)
        wait_for_subscriber(pub, timeout)

        msg = Joy()
        msg.buttons = buttons

        publish_for_duration(node=test_node, publisher=pub, msg=msg)

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

    @pytest.mark.parametrize(
        "axes, direction",
        [
            ([0.1, 0.0, 0.0, 0.0, 0.0], "y"),
            ([0.0, 0.1, 0.0, 0.0, 0.0], "x"),
            ([0.0, 0.0, 0.0, 0.1, 0.0], "z"),
        ],
    )
    def test_move_arm_with_joy(
        _self: object,
        axes: list[float],
        direction: str,
        test_node: Node,
        timeout: int,
        movement_threshold: float = 0.001,
    ) -> None:
        """Test moving the arm with the joystick.

        Args:
            _self (object): The test class instance.
            axes (list[float]): The joystick axes to use for the test.
            direction (str): The direction to move the arm in ("x", "y", or "z").
            test_node (Node): The test node to use for the test.
            timeout (int): The timeout in seconds to wait for the arm to move.
            movement_threshold (float): The threshold for movement detection.
        """

        def compare_fn(p1: Pose, p2: Pose) -> float:
            """Compare the positions of two poses based on the specified direction.

            Args:
                p1 (Pose): The first pose to compare.
                p2 (Pose): The second pose to compare.

            Returns:
                float: The difference in the specified direction between the two poses.
            """
            return getattr(p2.position, direction) - getattr(p1.position, direction)

        assert_movements_with_joy(
            node=test_node,
            joy_axes=axes,
            compare_fn=compare_fn,
            threshold=movement_threshold,
            description=f"{direction} position",
            frame_base=f"{namespace}/fr3_hand",
            frame_target=f"{namespace}/fr3_link0",
            timeout=timeout,
        )

    # Collect all test methods defined above
    tests = {
        name: obj
        for name, obj in locals().items()
        if callable(obj) and name.startswith("test_")
    }
    return tests
