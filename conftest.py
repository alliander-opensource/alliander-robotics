# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

"""Global pytest fixtures for ROS 2 integration testing."""

import os
import signal
import subprocess
import time
from typing import Generator, Iterator

import pytest
import rclpy
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.fixtures import SubRequest
from rcdt_utilities.config_objects import PlatformList, SimulatorConfig
from rclpy.node import Node
from termcolor import cprint

from predefined_configurations import PredefinedConfigurations
from start import Compose

LAUNCH_TIMEOUT = 90  # seconds
COMPOSE_FILE = "/rcdt_robotics/compose_pytest.yml"
HOST_COMPOSE_FILE = "/rcdt_robotics/compose.yml"


def pytest_addoption(parser: Parser) -> None:
    """Add custom command line options for pytest.

    Args:
        parser (Parser): The pytest parser to add options to.
    """
    parser.addoption("--simulation", action="store", default="True")


@pytest.fixture(scope="session", autouse=True)
def signal_handler() -> Generator:
    """Fixture to ensure that Docker containers are stopped when Pytest is interrupted.

    Yields:
        Generator: Yields signal control to the test session.
    """
    orig = signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGINT))
    yield
    cprint("Interrupt received, stopping Docker containers...", "yellow")
    stop_containers(COMPOSE_FILE)
    signal.signal(signal.SIGTERM, orig)


@pytest.fixture(scope="function", autouse=True)
def print_test_info(request: SubRequest) -> Generator:
    """Print the start and end of each test.

    Args:
        request (SubRequest): The pytest request object.

    Yields:
        Generator: Yields start and end of each test function.
    """
    cprint(f"Starting test: {request.node.name}", "blue")
    yield
    print("")
    cprint(f"Finished test: {request.node.name}", "blue")


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


def check_containers_started(compose_file: str, services: list) -> bool:
    """Check if the expected number of Docker containers are started.

    Args:
        compose_file (str): The path to the Docker compose file.
        services (list): The list of expected running services.

    Returns:
        bool: True if all services are started.
    """
    process = subprocess.run(
        [
            f"docker inspect -f='{{{{.Name}}}} {{{{.State.Health.Status}}}}' $(docker compose -f {compose_file} ps -q)"
        ],
        check=False,
        shell=True,
        capture_output=True,
    )
    stdout = process.stdout.decode("utf-8").rstrip()
    lines = stdout.split("\n")
    statuses = {}
    for line in lines:
        name, status = line.strip("/").split()
        if name in services:
            statuses[name] = status == "healthy"
    if len(statuses) < len(services):
        return False
    return all(statuses.values())


@pytest.fixture(scope="module", autouse=True)
def start_and_stop_containers(request: SubRequest) -> Generator:
    """Automatically start and stop Docker containers for each test module.

    Args:
        request (SubRequest): The pytest request object.

    Yields:
        Generator: Starts and stops Docker containers for each module.
    """
    # Execute before starting the tests in the module:
    compose = Compose()
    compose.mode = "configuration"
    compose.predefined_configuration = PredefinedConfigurations()
    compose.visualization = False

    platform_list = PlatformList()
    platform_list.platforms = getattr(request.module, "PLATFORMS", [])
    compose.predefined_configuration.plat_conf = platform_list

    world = getattr(request.module, "WORLD", "empty.sdf")
    load_ui = os.getenv("GAZEBO_UI", default="false").lower() == "true"

    # Propagate dev mounts
    dev_mounts = os.getenv("DEV_MOUNTS", default="false") == "true"
    if dev_mounts:
        compose.dev = True
        host_cwd = os.getenv("HOST_CWD", default="/rcdt")
        home_dir = os.getenv("HOME_DIR", default="/root")
        Compose.host_cwd = host_cwd
        Compose.home_dir = home_dir
    sim_config = SimulatorConfig(load_ui=load_ui, world=world)
    compose.predefined_configuration.sim_conf = sim_config

    services = compose.create_compose(COMPOSE_FILE)

    subprocess.run(
        f"docker compose -f {COMPOSE_FILE} pull --policy missing",
        timeout=3600,
        shell=True,
        check=True,
    )

    process = subprocess.Popen([f"docker compose -f {COMPOSE_FILE} up"], shell=True)

    containers_started = False
    start_time = time.time()
    while not containers_started:
        containers_started = check_containers_started(COMPOSE_FILE, services)
        if time.time() - start_time > LAUNCH_TIMEOUT:
            stop_containers(COMPOSE_FILE)
            pytest.exit("Timeout waiting for containers to start. Exiting pytest.")
    cprint("All containers are started, start testing!", "green")

    # Yield to run the tests in the module:
    yield

    # Execute after all tests in module are done:
    stop_containers(COMPOSE_FILE)
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
    """Fixture to get the timeout value from pytest config return it.

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


@pytest.fixture(scope="session")
def navigation_degree_tolerance() -> float:
    """Latitude/Longitude degree tolerance of testing navigation.

    This is the maximum allowed deviation for navigation during tests.

    Returns:
        float: The tolerance value for navigation.
    """
    return 2.5e-6  # ~0.25 meters
