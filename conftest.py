# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

"""Global pytest fixtures for ROS 2 integration testing."""

import time
from typing import Iterator

import pytest
import rclpy
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from rcdt_utilities.launch_utils import reset
from rclpy.node import Node
from ros2node.api import NodeName, get_node_names


def pytest_addoption(parser: Parser) -> None:
    """Add custom command line options for pytest.

    Args:
        parser (Parser): The pytest parser to add options to.
    """
    parser.addoption("--simulation", action="store", default="True")


@pytest.fixture(scope="module", autouse=True)
def wait_for_nodes_to_stop(test_node: Node) -> None:
    """Fixture to wait for all nodes to stop before starting with the tests.

    Args:
        test_node (Node): The test node used to check for active nodes.
    """
    test_node_name = test_node.get_fully_qualified_name()
    node_names: list[NodeName] = [
        NodeName(name="dummy", full_name="dummy", namespace="dummy")
    ]
    while len(node_names) > 0:
        node_names: list[NodeName] = get_node_names(node=test_node)
        node_names = [
            node_name
            for node_name in node_names
            if node_name.full_name != test_node_name
        ]
        msg = "\nWaiting for the following nodes to stop:\n"
        for node_name in node_names:
            msg += f"{node_name.full_name}\n"
        if len(node_names) > 0:
            test_node.get_logger().info(msg)
        time.sleep(1)


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
    """Fixture to get the timeout value from pytest config and return half of it.

    Args:
        pytestconfig (Config): The pytest configuration object.

    Returns:
        int: The timeout value in seconds.
    """
    return int(int(pytestconfig.getini("timeout")) / 2)


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
    return 0.25


@pytest.fixture(scope="session")
def navigation_degree_tolerance() -> float:
    """Latitude/Longitude degree tolerance of testing navigation.

    This is the maximum allowed deviation for navigation during tests.

    Returns:
        float: The tolerance value for navigation.
    """
    return 2.5e-6  # ~0.25 meters
