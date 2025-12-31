# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from _pytest.fixtures import SubRequest
from geometry_msgs.msg import TwistStamped
from rcdt_utilities.config_objects import Vehicle
from rclpy.node import Node
from sensor_msgs.msg import JointState

from ..utils import (
    assert_for_message,
    call_trigger_service,
    get_joint_position,
    publish_for_duration,
    wait_for_subscriber,
)

vehicle = Vehicle("panther", position=(0, 0, 0.2))
PLATFORMS = {vehicle.name: vehicle}


def test_joint_states_published(timeout: int) -> None:
    """Test that the joint states are published.

    Args:
        timeout (int): The timeout in seconds to wait for the joint states to be published.
    """
    assert_for_message(
        JointState, f"/{vehicle.namespace}/joint_states", timeout=timeout
    )


def test_e_stop_request_reset(
    request: SubRequest, test_node: Node, timeout: int
) -> None:
    """Test that the E-Stop request service can be called to unlock the Panther.

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
            service_name=f"/{vehicle.namespace}/hardware/e_stop_reset",
            timeout=timeout,
        )
        is True
    )


def test_driving(test_node: Node, timeout: int) -> None:
    """Test that the controllers work and the wheels have turned.

    Args:
        test_node (Node): The ROS 2 node to use for the test.
        timeout (int): The timeout in seconds to wait for the wheels to turn.
    """
    joint_value_before_driving = get_joint_position(
        vehicle.namespace, "fl_wheel_joint", timeout=timeout
    )

    pub = test_node.create_publisher(TwistStamped, f"/{vehicle.namespace}/cmd_vel", 10)
    wait_for_subscriber(pub, timeout)

    msg = TwistStamped()
    msg.twist.linear.x = 1.0

    publish_for_duration(node=test_node, publisher=pub, msg=msg)

    joint_value_after_driving = get_joint_position(
        vehicle.namespace, "fl_wheel_joint", timeout=timeout
    )

    delta = joint_value_after_driving - joint_value_before_driving

    assert delta != pytest.approx(0, abs=0.5), (
        f"The current joint value is {joint_value_after_driving}, but it should be different from {joint_value_before_driving}."
    )


def test_e_stop_request_trigger(
    request: SubRequest, test_node: Node, timeout: int
) -> None:
    """Test that the E-Stop request service can be called to lock the panther.

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
            service_name=f"/{vehicle.namespace}/hardware/e_stop_trigger",
            timeout=timeout,
        )
        is True
    )
