# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


import launch_pytest
import pytest
from _pytest.fixtures import SubRequest
from launch import LaunchDescription
from rcdt_launch.platforms.arm import Arm
from rcdt_test.franka.end_to_end.base_franka import get_tests
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path
from rcdt_utilities.test_utils import add_tests_to_class

namespace = "franka"


@launch_pytest.fixture(scope="class")
def franka(request: SubRequest) -> LaunchDescription:
    """Fixture to create a launch description for the Franka robot.

    This fixture sets up the Franka robot with the necessary configurations and
    launches the required nodes for testing.

    Args:
        request (SubRequest): The pytest request object, used to access command line options

    Returns:
        LaunchDescription: The launch description containing the Franka robot setup.

    """
    Arm(
        platform="franka",
        position=[0, 0, 0],
        namespace=namespace,
        gripper=True,
        moveit=True,
    )
    franka_launch = RegisteredLaunchDescription(
        get_file_path("rcdt_launch", ["launch"], "bringup.launch.py"),
        launch_arguments={
            "rviz": "False",
            "simulation": request.config.getoption("simulation"),
        },
    )
    return Register.connect_context([franka_launch])


@pytest.mark.launch(fixture=franka)
class TestCoreLaunch:
    """Run all the FrankaLaunchTests under franka.launch.py."""


add_tests_to_class(TestCoreLaunch, get_tests(namespace))
