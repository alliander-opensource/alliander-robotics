# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


import time
from typing import Any, Type

import pytest
import rclpy
from alliander_interfaces.action import TriggerAction
from alliander_interfaces.srv import StringSrv
from builtin_interfaces.msg import Duration
from control_msgs.action import FollowJointTrajectory
from launch_testing_ros.wait_for_topics import WaitForTopics
from lifecycle_msgs.srv import GetState
from rclpy.action import ActionClient
from rclpy.action.client import ClientGoalHandle
from rclpy.client import Client
from rclpy.logging import get_logger
from rclpy.node import Node
from rclpy.publisher import Publisher
from rclpy.task import Future
from sensor_msgs.msg import JointState
from std_srvs.srv import Trigger
from trajectory_msgs.msg import JointTrajectoryPoint

logger = get_logger("test_utils")


def publish_for_duration(
    node: Node,
    publisher: Publisher,
    msg: Any,
    publish_duration: float = 1.0,
    rate_sec: float = 0.1,
) -> None:
    """Publishes a message at a specified rate for a given duration.

    Args:
        node (Node): The rclpy node to use for publishing.
        publisher (Publisher): The publisher to send messages through.
        msg (Any): The message to publish.
        publish_duration (float): Duration in seconds to publish the message.
        rate_sec (float): Frequency in seconds at which to publish the message.
    """
    deadline = time.monotonic() + publish_duration

    while time.monotonic() < deadline:
        publisher.publish(msg)
        rclpy.spin_once(node, timeout_sec=rate_sec)


def wait_for_subscriber(pub: Publisher, timeout: int) -> None:
    """Wait for a subscriber to be ready for a given publisher.

    Args:
        pub (Publisher): The publisher to wait for.
        timeout (int): The maximum time to wait for a subscriber in seconds.

    Raises:
        TimeoutError: If no subscriber is found within the timeout period.

    """
    start_time = time.time()
    while pub.get_subscription_count() == 0:
        if time.time() > (start_time + timeout):
            raise TimeoutError()
        time.sleep(0.1)


def wait_for_node_active(node: Node, lifecycle_node_name: str, timeout: float) -> None:
    """Wait for a subscriber to be ready for a given publisher.

    Args:
        node (Node): The publisher to wait for.
        lifecycle_node_name (str): The name of the lifecycle node to wait for.
        timeout (float): The maximum time to wait for a subscriber in seconds.

    Raises:
        TimeoutError: If no subscriber is found within the timeout period.

    """
    client = node.create_client(GetState, f"{lifecycle_node_name}/get_state")

    if not client.wait_for_service(timeout_sec=timeout):
        raise TimeoutError(f"Service {lifecycle_node_name} not available")

    start_time = time.time()

    while True:
        request = GetState.Request()
        future = client.call_async(request)

        rclpy.spin_until_future_complete(node, future, timeout_sec=1.0)

        if future.result() is not None:
            state_id = future.result().current_state.id
            state_label = future.result().current_state.label

            node.get_logger().info(
                f"{lifecycle_node_name} state: {state_label}"
            )

            active_state = 3
            if state_id == active_state:
                return

        if time.time() - start_time > timeout:
            raise TimeoutError(
                f"{lifecycle_node_name} did not become ACTIVE"
            )

        time.sleep(0.5)


def get_joint_position(namespace: str, joint: str, timeout: int) -> float:
    """Get the position of a joint from the joint states topic.

    Args:
        namespace (str): The name space of the platform.
        joint (str): The name of the joint.
        timeout (int): Timeout in seconds to wait for the joint states topic.

    Returns:
        float: The position of the joint.
    """
    topic_list = [(f"{namespace}/joint_states", JointState)]
    wait_for_topics = WaitForTopics(topic_list, timeout=timeout)
    assert wait_for_topics.wait(), "Did not receive JointState."
    msg: JointState = wait_for_topics.received_messages(f"{namespace}/joint_states")[0]
    idx = msg.name.index(joint)
    position = msg.position[idx]
    wait_for_topics.shutdown()
    return position


def check_joint_positions(
    namespace: str,
    names: list,
    expected_positions: list,
    tolerance: float,
    timeout: int,
) -> None:
    """Check whether the joint positions match the expected positions within a tolerance.

    Args:
        namespace (str): The name space of the platform.
        names (list): The names of the joints.
        expected_positions (list): The expected positions of the joints.
        tolerance (float): The tolerance for the joint positions.
        timeout (int): Timeout in seconds to wait for the joint states topic.
    """
    topic_list = [(f"{namespace}/joint_states", JointState)]
    wait_for_topics = WaitForTopics(topic_list, timeout=timeout)
    assert wait_for_topics.wait(), "Did not receive JointState."
    msg: JointState = wait_for_topics.received_messages(f"{namespace}/joint_states")[0]
    wait_for_topics.shutdown()

    for joint_name, expected_position in zip(names, expected_positions, strict=False):
        idx = msg.name.index(joint_name)
        position = msg.position[idx]
        assert position == pytest.approx(expected_position, abs=tolerance), (
            f"Joint {joint_name} has position {position} while {expected_position} was expected."
        )


def create_ready_service_client(
    node: Node, srv_type: Type, service_name: str, timeout_sec: int
) -> Client:
    """Create and wait for a service client to become available.

    Args:
        node (Node): The rclpy node to use for client creation.
        srv_type (Type): The service type (e.g., `ListControllers`).
        service_name (str): Fully qualified name of the service.
        timeout_sec (int): Timeout to wait for the service.

    Returns:
        Client: Ready service client.

    Raises:
        RuntimeError: If the service is not available within timeout.
    """
    client = node.create_client(srv_type, service_name)
    start_time = time.time()
    while not client.service_is_ready():
        rclpy.spin_once(node, timeout_sec=0)
        if time.time() > (start_time + timeout_sec):
            raise RuntimeError(f"Service {service_name} not available")
    return client


def call_trigger_service(node: Node, service_name: str, timeout: int) -> bool:
    """Call a trigger service and return True if the service was called successfully.

    Args:
        node (Node): The rclpy node used to create the service client.
        service_name (str): The fully qualified name of the service.
        timeout (int): Timeout in seconds to wait for the service.

    Returns:
        bool: True if the service call was successful, False otherwise.
    """
    client = create_ready_service_client(node, Trigger, service_name, timeout)

    future = client.call_async(Trigger.Request())
    rclpy.spin_until_future_complete(node, future=future, timeout_sec=timeout)
    return future.result() is not None


def call_trigger_action(node: Node, action_name: str, timeout: int) -> bool:
    """Call a trigger action and return True if the action was called successfully.

    Args:
        node (Node): The rclpy node used to create the action client.
        action_name (str): The fully qualified name of the action.
        timeout (int): Timeout in seconds to wait for the action server.

    Returns:
        bool: True if the action call was successful, False otherwise.
    """
    client = create_ready_action_client(node, TriggerAction, action_name, timeout)
    future_goal_handle = client.send_goal_async(TriggerAction.Goal())
    start_time = time.time()
    while not future_goal_handle.done():
        if time.time() > (start_time + timeout):
            node.get_logger().error("Failed to obtain goal_handle. Timeout.")
            return False
        rclpy.spin_once(node, timeout_sec=0)

    client_goal_handle: ClientGoalHandle = future_goal_handle.result()
    if not client_goal_handle.accepted:
        node.get_logger().error("Goal was rejected by the action server.")
        return False

    future_result: Future = client_goal_handle.get_result_async()
    start_time = time.time()
    while not future_result.done():
        if time.time() > (start_time + timeout):
            node.get_logger().error("Failed to obtain result. Timeout.")
            return False
        rclpy.spin_once(node, timeout_sec=0)

    result: TriggerAction.Impl.GetResultService.Response = future_result.result()
    return result.result.success


def create_ready_action_client(
    node: Node, action_type: Type, action_name: str, timeout: int
) -> ActionClient:
    """Create and wait for an ActionClient to become ready.

    Args:
        node (Node): The rclpy node used to create the action client.
        action_type (Type): The action type class
        action_name (str): The fully qualified action name.
        timeout (int): Timeout in seconds to wait for the server.

    Returns:
        ActionClient: A ready ActionClient instance.

    Raises:
        RuntimeError: If the action server is not available within the timeout.
    """
    client = ActionClient(node, action_type, action_name)
    if not client.wait_for_server(timeout_sec=timeout):
        raise RuntimeError(f"Action server {action_name} not available")
    return client


def assert_for_message(message_type: type, topic: str, timeout: int) -> None:
    """Assert that a message of a specific type is received on a given topic within a timeout period.

    Args:
        message_type (type): The type of the message to wait for.
        topic (str): The topic to listen to.
        timeout (int): The maximum time in seconds to wait for the message.
    """
    wait_for_topics = WaitForTopics([(topic, message_type)], timeout)
    received = wait_for_topics.wait()
    wait_for_topics.shutdown()
    assert received, (
        f"No message received of type {message_type.__name__} on topic {topic} within {timeout} seconds."
    )


def wait_until_reached_joint(
    namespace: str,
    joint: str,
    expected_value: float,
    timeout_sec: int,
    tolerance: float = 0.025,
) -> tuple[bool, float]:
    """Wait until a joint reaches the expected value within a tolerance.

    Args:
        namespace (str): Namespace of the platform (e.g., 'franka').
        joint (str): Name of the joint to check.
        expected_value (float): Target joint value in radians.
        timeout_sec (int): Timeout duration in seconds.
        tolerance (float): Acceptable deviation from the expected value.

    Returns:
        tuple[bool, float]: (True, joint_value) if target reached; otherwise (False , joint_value).
    """
    end_time = time.monotonic() + timeout_sec
    while time.monotonic() < end_time:
        try:
            joint_value = get_joint_position(
                namespace=namespace, joint=joint, timeout=timeout_sec
            )
            if joint_value == pytest.approx(expected_value, abs=tolerance):
                time.sleep(2)
                return (True, joint_value)
        except ValueError:
            pass

        time.sleep(0.25)
    return (False, joint_value)


def call_move_to_configuration_service(
    node: Node, namespace: str, configuration: str, timeout: int
) -> bool:
    """Call the move_to_configuration service and return True if a response from the service was received.

    Args:
        node (Node): The ROS 2 node to use for the service call.
        namespace (str): The namespace of the platform.
        configuration (str): The configuration to move to.
        timeout (int): The timeout in seconds for the service call.

    Returns:
        bool: True if the service call was successful, False otherwise.
    """
    client = create_ready_service_client(
        node,
        StringSrv,
        f"/{namespace}/moveit_manager/move_to_configuration",
        timeout_sec=timeout,
    )
    request = StringSrv.Request()
    request.text = configuration
    future = client.call_async(request)
    rclpy.spin_until_future_complete(node, future=future, timeout_sec=timeout)
    return future.result() is not None


def follow_joint_trajectory_goal(
    node: Node,
    positions: list[float],
    controller: str,
    timeout: int,
    time_from_start: int = 3,
) -> None:
    """Test sending a joint trajectory goal to the arm controller.

    Args:
        node (Node): The ROS 2 node to use for the action client.
        positions (list[float]): The joint positions to move to.
        controller (str): The name of the controller to use.
        timeout (int): The timeout in seconds for the action client.
        time_from_start (int, optional): The time from start in seconds. Defaults to 3.
    """
    action_client = create_ready_action_client(
        node,
        FollowJointTrajectory,
        f"/{controller}/follow_joint_trajectory",
        timeout=timeout,
    )

    goal_msg = FollowJointTrajectory.Goal()
    goal_msg.trajectory.joint_names = [
        "fr3_joint1",
        "fr3_joint2",
        "fr3_joint3",
        "fr3_joint4",
        "fr3_joint5",
        "fr3_joint6",
        "fr3_joint7",
    ]

    point = JointTrajectoryPoint()
    point.positions = positions
    point.time_from_start = Duration(sec=time_from_start, nanosec=0)

    goal_msg.trajectory.points.append(point)

    future = action_client.send_goal_async(goal_msg)
    rclpy.spin_until_future_complete(node, future, timeout_sec=timeout)
    goal_handle: ClientGoalHandle = future.result()
    assert goal_handle.accepted

    result_future: Future = goal_handle.get_result_async()
    rclpy.spin_until_future_complete(node, result_future, timeout_sec=timeout)
