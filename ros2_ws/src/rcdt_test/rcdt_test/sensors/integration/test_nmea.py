# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


import launch_pytest
import pytest
from _pytest.fixtures import SubRequest
from launch import LaunchDescription
from rcdt_launch.platforms.gps import GPS
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path
from rcdt_utilities.test_utils import assert_for_message, wait_for_register
from sensor_msgs.msg import NavSatFix

namespace = "nmea"


@launch_pytest.fixture(scope="module")
def launch(request: SubRequest) -> LaunchDescription:
    """Fixture to create launch file for the test.

    Args:
        request (SubRequest): The pytest request object, used to access command line options

    Returns:
        LaunchDescription: The launch description for the test.
    """
    GPS(platform="nmea", position=[0, 0, 0.5], namespace=namespace)
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
def test_gps_fix_published(timeout: int) -> None:
    """Test that the gps fix messages are published.

    Args:
        timeout (int): The timeout in seconds to wait for the messages to be published.
    """
    assert_for_message(NavSatFix, f"/{namespace}/gps/fix", timeout=timeout)
