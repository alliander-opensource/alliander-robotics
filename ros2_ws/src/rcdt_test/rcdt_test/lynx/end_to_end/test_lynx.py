# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


import launch_pytest
import pytest
from _pytest.fixtures import SubRequest
from launch import LaunchDescription
from rcdt_launch.platforms.vehicle import Vehicle
from rcdt_test.panther.end_to_end.base_panther import get_tests
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path
from rcdt_utilities.test_utils import add_tests_to_class

namespace = "lynx"


@launch_pytest.fixture(scope="module")
def lynx_launch(request: SubRequest) -> LaunchDescription:
    """Fixture to create launch file for lynx robot.

    Args:
        request (SubRequest): The pytest request object, used to access command line options

    Returns:
        LaunchDescription: The launch description for the lynx robot.
    """
    Vehicle(platform="lynx", position=[0, 0, 0.13], namespace=namespace)
    launch = RegisteredLaunchDescription(
        get_file_path("rcdt_launch", ["launch"], "bringup.launch.py"),
        launch_arguments={
            "rviz": "False",
            "simulation": request.config.getoption("simulation"),
        },
    )
    return Register.connect_context([launch])


@pytest.mark.launch(fixture=lynx_launch)
class TestLynxFullSuite:
    """Re-run all tests from LynxFullTests using lynx.launch.py."""


add_tests_to_class(TestLynxFullSuite, get_tests(namespace))
