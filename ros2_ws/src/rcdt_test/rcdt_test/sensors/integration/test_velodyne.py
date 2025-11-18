# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


import launch_pytest
import pytest
from _pytest.fixtures import SubRequest
from launch import LaunchDescription
from rcdt_launch.platforms.lidar import Lidar
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path
from rcdt_utilities.test_utils import assert_for_message, wait_for_register
from sensor_msgs.msg import PointCloud2

namespace = "velodyne"


@launch_pytest.fixture(scope="module")
def launch(request: SubRequest) -> LaunchDescription:
    """Fixture to create launch file for the velodyne test.

    Args:
        request (SubRequest): The pytest request object, used to access command line options

    Returns:
        LaunchDescription: The launch description for the velodyne test.
    """
    Lidar(platform="velodyne", position=[0, 0, 0.5], namespace=namespace)
    launch = RegisteredLaunchDescription(
        get_file_path("rcdt_launch", ["launch"], "bringup.launch.py"),
        launch_arguments={
            "rviz": "False",
            "simulation": request.config.getoption("simulation"),
        },
    )
    return Register.connect_context([launch])


@pytest.mark.launch(fixture=launch)
def test_wait_for_register(timeout: int) -> None:
    """Test that the platform is registered in the system to start the tests.

    Args:
        timeout (int): The timeout in seconds before stopping the test.
    """
    wait_for_register(timeout=timeout)


@pytest.mark.launch(fixture=launch)
def test_points_published(timeout: int) -> None:
    """Test that the pointcloud is published.

    Args:
        timeout (int): The timeout in seconds to wait for the points to be published.
    """
    assert_for_message(PointCloud2, f"/{namespace}/scan/points", timeout=timeout)
