# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


import time
from typing import Any, Callable, Type

import pytest
import rclpy
from geometry_msgs.msg import Pose, PoseStamped
from launch_testing_ros.wait_for_topics import WaitForTopics
from rcdt_messages.action import Trigger as TriggerAction
from rcdt_messages.srv import ExpressPoseInOtherFrame
from rclpy.action import ActionClient
from rclpy.action.client import ClientGoalHandle
from rclpy.client import Client
from rclpy.logging import get_logger
from rclpy.node import Node
from rclpy.publisher import Publisher
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSProfile
from rclpy.task import Future
from sensor_msgs.msg import JointState, Joy
from std_msgs.msg import String
from std_srvs.srv import Trigger
from termcolor import colored

from rcdt_utilities.register import Register

logger = get_logger("test_utils")


def add_tests_to_class(cls: type, tests: dict[str, Callable]) -> None:
    """Add the defined tests to the given class.

    Use of the pytest mark.launch decorator adapts the class functions, which makes it impossible to reuse tests with different fixtures.
    However, by using this method in combination with a function that generates the test functions (tests), reuse is possible.

    Args:
        cls (type): The class to which the tests should be added.
        tests (dict[str, Callable]): The test functions to add to the class.
    """
    for name, method in tests.items():
        setattr(cls, name, method)


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

    """
    start_time = time.monotonic()
    while pub.get_subscription_count() == 0 and time.monotonic() - start_time < timeout:
        time.sleep(0.1)


def get_joint_position(namespace: str, joint: str, timeout: int) -> float:
    """Get the position of a joint from the joint states topic.

    Args:
        namespace (str): The name space of the robot.
        joint (str): The name of the joint.
        timeout (int): Timeout in seconds to wait for the joint states topic.

    Returns:
        float: The position of the joint.
    """
    topic_list = [(f"{namespace}/joint_states", JointState)]
    wait_for_topics = WaitForTopics(topic_list, timeout=timeout)
    assert wait_for_topics.wait()
    msg: JointState = wait_for_topics.received_messages(f"{namespace}/joint_states")[0]
    idx = msg.name.index(joint)
    position = msg.position[idx]
    wait_for_topics.shutdown()
    return position


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
    if not client.wait_for_service(timeout_sec=timeout_sec):
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


def call_express_pose_in_other_frame(
    node: Node, pose: PoseStamped, target_frame: str, timeout: int
) -> ExpressPoseInOtherFrame.Response:
    """Calls the /pose_manipulator/express_pose_in_other_frame service.

    Args:
        node (Node): An active rclpy Node.
        pose (PoseStamped): The pose to transform.
        target_frame (str): The frame to express the pose in.
        timeout (int): Timeout for waiting on service and result.

    Raises:
        RuntimeError: If the service call fails or times out.

    Returns:
        ExpressPoseInOtherFrame.Response: The response containing the transformed pose.
    """
    client = create_ready_service_client(
        node,
        ExpressPoseInOtherFrame,
        "/pose_manipulator/express_pose_in_other_frame",
        timeout_sec=timeout,
    )

    request = ExpressPoseInOtherFrame.Request()
    request.pose = pose
    request.target_frame = target_frame

    future: Future = client.call_async(request)
    rclpy.spin_until_future_complete(node, future, timeout_sec=timeout)

    response = future.result()
    if response is None:
        raise RuntimeError("Service call failed or timed out")

    return response


def assert_joy_topic_switch(
    node: Node,
    expected_topic: str,
    button_config: list[int],
    timeout: int,
    state_topic: str = "/joy_topic_manager/state",
) -> None:
    """Publishes a Joy message and asserts that the expected topic is published on state_topic.

    Args:
        node (Node): rclpy test node.
        expected_topic (str): Expected topic that should be published by the JoyTopicManager.
        button_config (list[int]): Joy message buttons to trigger the topic change.
        timeout (int): Max time to wait for the result.
        state_topic (str): Topic to listen for state updates from joy_topic_manager.
    """
    logger.info("Starting to assert joy topic switch")
    qos = QoSProfile(
        depth=1,
        durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        history=QoSHistoryPolicy.KEEP_LAST,
    )

    result = {}

    def callback_function(msg: String) -> None:
        """Callback function to handle messages from the state topic.

        Args:
            msg (String): The message received from the state topic.
        """
        result["state"] = msg.data

    node.create_subscription(
        msg_type=String,
        topic=state_topic,
        callback=callback_function,
        qos_profile=qos,
    )

    pub = node.create_publisher(Joy, "/joy", 10)
    wait_for_subscriber(pub, timeout)

    msg = Joy()
    msg.buttons = button_config
    publish_for_duration(
        node=node, publisher=pub, msg=msg, publish_duration=1, rate_sec=0.1
    )

    start_time = time.monotonic()
    while (
        result.get("state") != expected_topic
        and time.monotonic() - start_time < timeout
    ):
        rclpy.spin_once(node, timeout_sec=1)
        time.sleep(0.1)

    assert result.get("state") == expected_topic, (
        f"Expected state '{expected_topic}', but got '{result.get('state')}'"
    )


def assert_movements_with_joy(  # noqa: PLR0913
    node: Node,
    joy_axes: list[float],
    compare_fn: Callable[[Pose, Pose], float],
    threshold: float,
    description: str,
    frame_base: str,
    frame_target: str,
    timeout: int,
) -> None:
    """Publishes a joystick message and asserts that movement occurs above a threshold.

    Args:
        node (Node): rclpy test node.
        joy_axes (list[float]): Axes values to publish in the Joy message.
        compare_fn (Callable[[Pose, Pose], float]): Function to compare poses.
        threshold (float): Minimum change in pose to assert movement.
        description (str): Description of the pose change being tested.
        frame_base (str): Base frame of the robot.
        frame_target (str): Target frame to express the pose in.
        timeout (int): Max time to wait for the result.
    """
    pose = PoseStamped()
    pose.header.frame_id = frame_base
    first_pose = call_express_pose_in_other_frame(
        node=node, pose=pose, target_frame=frame_target, timeout=timeout
    ).pose.pose

    pub = node.create_publisher(Joy, "/joy", 10)
    wait_for_subscriber(pub, timeout)

    msg = Joy()
    msg.axes = joy_axes
    publish_for_duration(
        node=node, publisher=pub, msg=msg, publish_duration=1, rate_sec=0.1
    )

    pose = PoseStamped()
    pose.header.frame_id = frame_base
    moved_pose = call_express_pose_in_other_frame(
        node=node, pose=pose, target_frame=frame_target, timeout=timeout
    ).pose.pose
    delta = compare_fn(first_pose, moved_pose)

    assert abs(delta) > threshold, (
        f"{description} did not change after input. Δ = {delta}"
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
        namespace (str): Namespace of the robot (e.g., 'franka').
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


def wait_for_register(timeout: int) -> None:
    """Waits till all registerd actions are started.

    This function should be called in every first test of a test file.
    This ensures that all other tests are started after all actions are launched correctly.
    If not all actions start correctly, pytest-timeout will cancel the test, but this does not stop the while loop.
    Therefore, the while loop has it's own timeout which also uses the defined pytest-timeout variable.

    Args:
        timeout (int): The maximum time in seconds to wait for the register to be ready.

    """
    logger = get_logger("wait_for_register")
    start = time.monotonic()
    while not Register.all_started and time.monotonic() - start < timeout:
        time.sleep(1)
    if Register.all_started:
        logger.info(colored("Register is ready, start testing!", "green"))
    assert Register.all_started
