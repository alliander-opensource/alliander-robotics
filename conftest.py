# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

"""Global pytest fixtures for ROS 2 integration testing."""

import subprocess
import time
from typing import Generator, Iterator

import pytest
import rclpy
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.fixtures import SubRequest
from rclpy.node import Node
from termcolor import colored

from compose import Compose

LAUNCH_TIMEOUT = 90  # seconds


def pytest_addoption(parser: Parser) -> None:
    """Add custom command line options for pytest.

    Args:
        parser (Parser): The pytest parser to add options to.
    """
    parser.addoption("--simulation", action="store", default="True")


@pytest.fixture(scope="function", autouse=True)
def print_test_info(request: SubRequest) -> Generator:
    """Print the start and end of each test.

    Args:
        request (SubRequest): The pytest request object.
    """
    print(colored(f"Starting test: {request.node.name}", "blue"))
    yield
    print("")
    print(colored(f"Finished test: {request.node.name}", "blue"))


def stop_containers(compose_file: str) -> None:
    """Stop and remove Docker containers defined in the given compose file.

    Args:
        compose_file (str): The path to the Docker compose file.
    """
    subprocess.run(
        [f"docker compose -f {compose_file} down -t 1"], check=False, shell=True
    )
    subprocess.run(
        [f"docker compose -f {compose_file} rm -fsv"], check=False, shell=True
    )


def check_containers_started(compose_file: str, number_of_services: int) -> bool:
    """Check if the expected number of Docker containers are started.

    Args:
        compose_file (str): The path to the Docker compose file.
        number_of_services (int): The expected number of running services.

    Returns:
        bool: True if all services are started.
    """
    process = subprocess.run(
        [
            f"docker inspect -f '{{{{.State.Health.Status}}}}' $(docker compose -f {compose_file} ps -q)"
        ],
        check=False,
        shell=True,
        capture_output=True,
    )
    stdout = process.stdout.decode("utf-8").rstrip()
    statuses = stdout.split()
    if len(statuses) != number_of_services:
        return False
    return all(status == "healthy" for status in statuses)


@pytest.fixture(scope="module", autouse=True)
def start_and_stop_containers(request: SubRequest) -> Generator:
    """Automatically start and stop Docker containers for each test module.

    Args:
        request (SubRequest): The pytest request object.
    """
    # Execute before starting the tests in the module:
    compose_file = "/rcdt_robotics/rcdt_tests/compose.yml"
    platforms = getattr(request.module, "PLATFORMS", {})
    world = getattr(request.module, "WORLD", "")
    compose = Compose(platforms, world=world)
    number_of_services = compose.compose_for_test(
        simulator=True, tools=False, output_file=compose_file
    )
    process = subprocess.Popen([f"docker compose -f {compose_file} up"], shell=True)

    containers_started = False
    start_time = time.time()
    while not containers_started:
        containers_started = check_containers_started(compose_file, number_of_services)
        if time.time() - start_time > LAUNCH_TIMEOUT:
            stop_containers(compose_file)
            pytest.exit("Timeout waiting for containers to start. Exiting pytest.")
    print(colored("All containers are started, start testing!", "green"))

    # Yield to run the tests in the module:
    yield

    # Execute after all tests in module are done:
    stop_containers(compose_file)
    process.wait()


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


@pytest.fixture(scope="session")
def navigation_distance_tolerance() -> float:
    """Distance tolerance of testing navigation.

    This is the maximum allowed deviation for navigation during tests.

    Returns:
        float: The tolerance value for navigation.
    """
    return 0.25
