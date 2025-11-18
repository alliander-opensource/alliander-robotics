# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from _pytest.fixtures import SubRequest
from geometry_msgs.msg import Pose
from rcdt_utilities.test_utils import (
    assert_for_message,
    assert_joy_topic_switch,
    assert_movements_with_joy,
    call_trigger_service,
    wait_for_register,
)
from rclpy.node import Node
from sensor_msgs.msg import JointState


def get_tests(namespace: str) -> dict:
    """Test class for the Panther.

    This class contains all the tests that are run in the Panther test suite.
    It dynamically creates test methods based on the defined functions.

    Args:
        namespace (str): The namespace of the robot.

    Returns:
        dict: A dictionary of test methods.
    """

    def test_wait_for_register(_self: object, timeout: int) -> None:
        """Wait for the Panther to register.

        Args:
            _self (object): The test class instance.
            timeout (int): The timeout in seconds to wait before failing the test.
        """
        wait_for_register(timeout=timeout)

    def test_joint_states_published(_self: object, timeout: int) -> None:
        """Test that the joint states are published.

        Args:
            _self (object): The test class instance.
            timeout (int): The timeout in seconds to wait before failing the test.
        """
        assert_for_message(JointState, f"/{namespace}/joint_states", timeout=timeout)

    def test_e_stop_request_reset(
        _self: object, request: SubRequest, test_node: Node, timeout: int
    ) -> None:
        """Test that the E-Stop request service can be called to unlock the Panther.

        Args:
            _self (object): The test class instance.
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

    def test_switch_joy_to_panther_topic(
        _self: object, test_node: Node, timeout: int
    ) -> None:
        """Test that the joy topic switches to the Panther topic.

        Args:
            _self (object): The test class instance.
            test_node (Node): The ROS 2 node to use for the test.
            timeout (int): The timeout in seconds to wait before failing the test.
        """
        assert_joy_topic_switch(
            node=test_node,
            expected_topic=f"/{namespace}/joy",
            button_config=[0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            timeout=timeout,
        )

    def test_move_panther_with_joy(
        _self: object, test_node: Node, timeout: int
    ) -> None:
        """Test that the Panther can be moved with the joy topic.

        Args:
            _self (object): The test class instance.
            test_node (Node): The ROS 2 node to use for the test.
            timeout (int): The timeout in seconds to wait before failing the test.
        """

        def compare_fn(p1: Pose, p2: Pose) -> float:
            return p2.position.x - p1.position.x

        assert_movements_with_joy(
            node=test_node,
            joy_axes=[0.0, 0.1, 0.0, 0.0, 0.0],
            compare_fn=compare_fn,
            threshold=0.001,
            description="x position",
            frame_base=f"{namespace}/base_link",
            frame_target=f"{namespace}/odom",
            timeout=timeout,
        )

    def test_rotate_panther_with_joy(
        _self: object, test_node: Node, timeout: int
    ) -> None:
        """Test that the Panther can be rotated with the joy topic.

        Args:
            _self (object): The test class instance.
            test_node (Node): The ROS 2 node to use for the test.
            timeout (int): The timeout in seconds to wait before failing the test.
        """

        def compare_fn(p1: Pose, p2: Pose) -> float:
            return p2.orientation.w - p1.orientation.w

        assert_movements_with_joy(
            node=test_node,
            joy_axes=[0.0, 0.0, 0.1, 0.0, 0.0],
            compare_fn=compare_fn,
            threshold=0.0001,
            description="orientation.w",
            frame_base=f"{namespace}/base_link",
            frame_target=f"{namespace}/odom",
            timeout=timeout,
        )

    def test_e_stop_request_trigger(
        _self: object, request: SubRequest, test_node: Node, timeout: int
    ) -> None:
        """Test that the E-Stop request service can be called to lock the panther.

        Args:
            _self (object): The test class instance.
            request (SubRequest): The pytest request object, used to access command line options
            test_node (Node): The ROS 2 node to use for the test.
            timeout (int): The timeout in seconds to wait before failing the test.
        """
        if request.config.getoption("simulation"):
            pytest.skip("E-Stop is not available.")  # ty: ignore[call-non-callable]
        assert (
            call_trigger_service(
                node=test_node,
                service_name=f"/{namespace}/hardware/e_stop_trigger",
                timeout=timeout,
            )
            is True
        )

    tests = {
        name: obj
        for name, obj in locals().items()
        if callable(obj) and name.startswith("test_")
    }
    return tests
