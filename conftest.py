# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

"""Global pytest fixtures for ROS 2 integration testing."""

from typing import Iterator

import pytest
import rclpy
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from rcdt_utilities.launch_utils import reset
from rclpy.node import Node


def pytest_addoption(parser: Parser) -> None:
    """Add custom command line options for pytest.

    Args:
        parser (Parser): The pytest parser to add options to.
    """
    parser.addoption("--simulation", action="store", default="True")


@pytest.fixture(scope="module", autouse=True)
def reset_platform() -> None:
    """Fixture to automatically reset the platform configuration from a previous test module."""
    reset()


@pytest.fixture(scope="module")
def test_node() -> Iterator[Node]:
    """Fixture to create a singleton node for testing.

    This node is used to ensure that the ROS 2 context is initialized and can be used in tests.

    Yields:
        Node: The singleton node for testing.
    """
    rclpy.init()
    node = Node("test_node")
    yield node
    node.destroy_node()
    rclpy.shutdown()


@pytest.fixture(scope="module")
def timeout(pytestconfig: Config) -> int:
    """Fixture to get the timeout value from pytest config.

    Args:
        pytestconfig (Config): The pytest configuration object.

    Returns:
        int: The timeout value in seconds.
    """
    return int(pytestconfig.getini("timeout"))


@pytest.fixture(scope="session")
def finger_joint_fault_tolerance() -> float:
    """Tolerance of testing finger joint movements.

    This is the maximum allowed deviation for finger joint movements during tests.

    Returns:
        float: The tolerance value for finger joint movements.
    """
    return 0.025


@pytest.fixture(scope="session")
def joint_movement_tolerance() -> float:
    """Tolerance of testing joint movements.

    This is the maximum allowed deviation for joint movements during tests.

    Returns:
        float: The tolerance value for joint movements.
    """
    return 0.01


@pytest.fixture(scope="session")
def navigation_distance_tolerance() -> float:
    """Distance tolerance of testing navigation.

    This is the maximum allowed deviation for navigation during tests.

    Returns:
        float: The tolerance value for navigation.
    """
    return 0.2


@pytest.fixture(scope="session")
def navigation_degree_tolerance() -> float:
    """Latitude/Longitude degree tolerance of testing navigation.

    This is the maximum allowed deviation for navigation during tests.

    Returns:
        float: The tolerance value for navigation.
    """
    return 2e-6
