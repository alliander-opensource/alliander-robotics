# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


import launch_pytest
import pytest
from _pytest.fixtures import SubRequest
from launch import LaunchDescription
from rcdt_launch.robot import Camera
from rcdt_utilities.launch_utils import assert_for_message, get_file_path
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.test_utils import wait_for_register
from sensor_msgs.msg import CameraInfo, Image

namespace = "realsense"


@launch_pytest.fixture(scope="module")
def launch(request: SubRequest) -> LaunchDescription:
    """Fixture to create launch file for the realsense test.

    Args:
        request (SubRequest): The pytest request object, used to access command line options

    Returns:
        LaunchDescription: The launch description for the realsense test.
    """
    Camera(platform="realsense", position=[0, 0, 0.5], namespace=namespace)
    launch = RegisteredLaunchDescription(
        get_file_path("rcdt_launch", ["launch"], "robots.launch.py"),
        launch_arguments={
            "rviz": "False",
            "simulation": request.config.getoption("simulation"),
        },
    )
    return Register.connect_context([launch])


@pytest.mark.launch(fixture=launch)
def test_wait_for_register(timeout: int) -> None:
    """Test that the robot is registered in the system to start the tests.

    Args:
        timeout (int): The timeout in seconds before stopping the test.
    """
    wait_for_register(timeout=timeout)


@pytest.mark.launch(fixture=launch)
def test_color_image_published(timeout: int) -> None:
    """Test that color images are published.

    Args:
        timeout (int): The timeout in seconds to wait for the joint states to be published.
    """
    assert_for_message(Image, f"/{namespace}/color/image_raw", timeout=timeout)


@pytest.mark.launch(fixture=launch)
def test_color_camera_info_published(timeout: int) -> None:
    """Test that color camera info is published.

    Args:
        timeout (int): The timeout in seconds to wait for the joint states to be published.
    """
    assert_for_message(CameraInfo, f"/{namespace}/color/camera_info", timeout=timeout)


@pytest.mark.launch(fixture=launch)
def test_depth_image_published(timeout: int) -> None:
    """Test that depth images are published.

    Args:
        timeout (int): The timeout in seconds to wait for the joint states to be published.
    """
    assert_for_message(Image, f"/{namespace}/depth/image_rect_raw", timeout=timeout)


@pytest.mark.launch(fixture=launch)
def test_depth_camera_info_published(timeout: int) -> None:
    """Test that color camera info is published.

    Args:
        timeout (int): The timeout in seconds to wait for the joint states to be published.
    """
    assert_for_message(CameraInfo, f"/{namespace}/depth/camera_info", timeout=timeout)
