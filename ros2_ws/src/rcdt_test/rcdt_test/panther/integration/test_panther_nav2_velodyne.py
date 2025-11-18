# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


import launch_pytest
import numpy as np
import pytest
import rclpy
from _pytest.fixtures import SubRequest
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from launch import LaunchDescription
from nav2_msgs.action import NavigateToPose
from rcdt_launch.platforms.lidar import Lidar
from rcdt_launch.platforms.vehicle import Vehicle
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path
from rcdt_utilities.test_utils import (
    assert_for_message,
    call_trigger_service,
    create_ready_action_client,
    wait_for_register,
)
from rclpy.action.client import ClientGoalHandle
from rclpy.node import Node
from rclpy.task import Future
from sensor_msgs.msg import JointState
from tf_transformations import quaternion_from_euler

namespace_vehicle = "panther"
namespace_lidar = "velodyne"


@launch_pytest.fixture(scope="module")
def panther_launch(request: SubRequest) -> LaunchDescription:
    """Fixture to create launch file for panther robot.

    Args:
        request (SubRequest): The pytest request object, used to access command line options

    Returns:
        LaunchDescription: The launch description for the panther robot.
    """
    vehicle = Vehicle(
        platform="panther",
        position=[0, 0, 0.2],
        namespace=namespace_vehicle,
        navigation=True,
    )
    Lidar("velodyne", [0.13, -0.13, 0.35], parent=vehicle, namespace=namespace_lidar)
    launch = RegisteredLaunchDescription(
        get_file_path("rcdt_launch", ["launch"], "bringup.launch.py"),
        launch_arguments={
            "rviz": "False",
            "simulation": request.config.getoption("simulation"),
        },
    )
    return Register.connect_context([launch])


@pytest.mark.timeout(150)
@pytest.mark.launch(fixture=panther_launch)
def test_wait_for_register(timeout: int) -> None:
    """Test that the panther core is registered in the RCDT.

    Args:
        timeout (int): The timeout in seconds to wait for the panther core to register.
    """
    wait_for_register(timeout=timeout)


@pytest.mark.launch(fixture=panther_launch)
def test_joint_states_published(timeout: int) -> None:
    """Test that the joint states are published.

    Args:
        timeout (int): The timeout in seconds to wait for the joint states to be published.
    """
    assert_for_message(
        JointState, f"/{namespace_vehicle}/joint_states", timeout=timeout
    )


@pytest.mark.launch(fixture=panther_launch)
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
            service_name=f"/{namespace_vehicle}/hardware/e_stop_reset",
            timeout=timeout,
        )
        is True
    )


@pytest.mark.launch(fixture=panther_launch)
def test_nav2_goal(test_node: Node, timeout: int) -> None:
    """Test that the Panther can receive and process a navigation goal.

    Args:
        test_node (Node): The ROS 2 node to use for the test.
        timeout (int): The timeout in seconds to wait for the goal to be processed.
    """
    action_client = create_ready_action_client(
        node=test_node,
        action_type=NavigateToPose,
        action_name=f"{namespace_vehicle}/navigate_to_pose",
        timeout=timeout,
    )

    goal_msg = NavigateToPose.Goal()

    pose_stamped = PoseStamped()

    pose_stamped.header.stamp = test_node.get_clock().now().to_msg()
    pose_stamped.header.frame_id = "map"

    # 2) Position:
    pose_stamped.pose.position.x = 0.3
    pose_stamped.pose.position.y = 0.0
    pose_stamped.pose.position.z = 0.0

    # 3) Orientation with 30 degrees (quaternion):
    yaw = 30.0 * (np.pi / 180.0)
    qx, qy, qz, qw = quaternion_from_euler(0.0, 0.0, yaw)
    pose_stamped.pose.orientation.x = qx
    pose_stamped.pose.orientation.y = qy
    pose_stamped.pose.orientation.z = qz
    pose_stamped.pose.orientation.w = qw

    goal_msg.pose = pose_stamped

    future = action_client.send_goal_async(goal_msg)
    rclpy.spin_until_future_complete(test_node, future, timeout_sec=timeout)
    goal_handle: ClientGoalHandle = future.result()

    assert goal_handle.accepted

    result_future: Future = goal_handle.get_result_async()
    rclpy.spin_until_future_complete(test_node, result_future, timeout_sec=timeout)

    result: NavigateToPose.Impl.GetResultService.Response = result_future.result()
    assert result.status == GoalStatus.STATUS_SUCCEEDED, (
        f"Navigation failed with status: {result.status}"
    )
