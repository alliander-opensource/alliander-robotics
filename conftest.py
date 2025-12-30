# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

"""Global pytest fixtures for ROS 2 integration testing."""

import subprocess
from typing import Iterator

import pytest
import rclpy
from _pytest.config import Config
from _pytest.fixtures import SubRequest
from rclpy.node import Node

from compose import Compose


@pytest.fixture(scope="module", autouse=True)
def start_and_stop_containers(request: SubRequest):
    output_file = "/rcdt_robotics/rcdt_tests/compose.yml"
    platforms = getattr(request.module, "PLATFORMS", {})
    compose = Compose(platforms)
    compose.compose_for_test(simulator=True, tools=False, output_file=output_file)
    process = subprocess.Popen([f"docker compose -f {output_file} up"], shell=True)
    yield
    subprocess.run(
        [f"docker compose -f {output_file} down -t 1"], check=False, shell=True
    )
    process.wait()
    subprocess.run(
        [f"docker compose -f {output_file} rm -fsv"], check=False, shell=True
    )


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
    if rclpy.ok():
        rclpy.shutdown()


@pytest.fixture(scope="module")
def timeout(pytestconfig: Config) -> int:
    """Fixture to get the timeout value from pytest config and return half of it.

    Args:
        pytestconfig (Config): The pytest configuration object.

    Returns:
        int: The timeout value in seconds.
    """
    return int(pytestconfig.getini("timeout"))


@pytest.fixture(scope="session")
def joint_movement_tolerance() -> float:
    """Tolerance of testing joint movements.

    This is the maximum allowed deviation for joint movements during tests.

    Returns:
        float: The tolerance value for joint movements.
    """
    return 0.01


@pytest.fixture(scope="session")
def finger_joint_fault_tolerance() -> float:
    """Tolerance of testing finger joint movements.

    This is the maximum allowed deviation for finger joint movements during tests.

    Returns:
        float: The tolerance value for finger joint movements.
    """
    return 0.025
