# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

"""Global pytest fixtures for ROS 2 integration testing."""

import json
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
from alliander_utilities.config_objects import PlatformList, SimulatorConfig
from rclpy.node import Node
from termcolor import cprint

import utils
from predefined_configurations import PredefinedConfigurations
from start import Compose

LAUNCH_TIMEOUT = 90  # seconds
COMPOSE_FILE = "/alliander_robotics/compose_pytest.yml"
HOST_COMPOSE_FILE = "/alliander_robotics/compose.yml"


class Configurations:
    """Configurations used for pytest.

    Attributes:
        mode (str): The mode of testing.
        changed_packages (set[str]): The set of packages that have changed.
        ros_domain_id (int): ...
    """

    mode: str
    changed_packages: set[str]
    ros_domain_id: int = 0


def pytest_addoption(parser: Parser) -> None:
    """Add custom command line options for pytest.

    Args:
        parser (Parser): The pytest parser to add options to.
    """
    parser.addoption("--simulation", action="store", default="True")
    parser.addoption("--mode", action="store", default="changed")


@pytest.hookimpl()
def pytest_sessionstart() -> None:
    """Run before the pytest session starts."""
    Configurations.changed_packages = utils.get_changed_packages(verbose=True)
    print(f"\nChanged packages: {Configurations.changed_packages}\n")


@pytest.fixture(scope="session", autouse=True)
def control_session(pytestconfig: Config) -> Generator:
    """Controls setup and teardown of the pytest session.

    Args:
        pytestconfig (Config): The pytest configuration object.

    Yields:
        Generator: Yields signal control to the test session.
    """
    mode = pytestconfig.getoption("mode")
    mode_options = ["changed", "all"]
    if mode not in mode_options:
        pytest.exit(
            f"Invalid mode '{mode}' specified. Please choose from {mode_options}."
        )
    Configurations.mode = mode

    orig = signal.signal(signal.SIGTERM, signal.getsignal(signal.SIGINT))

    yield

    print("\n")
    cprint("All tests finished, stopping Docker containers...", "yellow")
    stop_containers(COMPOSE_FILE)
    signal.signal(signal.SIGTERM, orig)


@pytest.fixture(scope="class", autouse=True)
def control_class(request: SubRequest) -> Generator:
    """Controls the setup and teardown of a pytest class.

    Args:
        request (SubRequest): The pytest request object.

    Yields:
        Generator: Starts and stops Docker containers for each module.
    """
    Configurations.ros_domain_id += 1
    os.environ["ROS_DOMAIN_ID"] = f"{Configurations.ros_domain_id}"
    print("")
    cprint(f"[{request.cls.__name__}]: started", "blue")
    services = create_compose_file(request)
    if Configurations.mode != "all":
        skip_if_no_changes(services)
    pull_missing_images()
    wait_for_removal_nodes()

    process = start_containers(services)

    yield

    stop_containers(COMPOSE_FILE)
    process.wait()
    cprint(f"[{request.cls.__name__}]: finished", "blue")


@pytest.fixture(scope="function", autouse=True)
def control_function(request: SubRequest) -> Generator:
    """Control the setup and teardown of an individual test function.

    Args:
        request (SubRequest): The pytest request object.

    Yields:
        Generator: Yields start and end of each test function.
    """
    cprint(f"Starting test: {request.node.name}", "blue")

    yield

    print("")
    cprint(f"Finished test: {request.node.name}", "blue")


def create_compose_file(request: SubRequest) -> list:
    """Create a compose file for the group of tests.

    Args:
        request (SubRequest): The pytest request object.

    Returns:
        list: The list of services defined in the compose file.
    """
    compose = Compose(Configurations.ros_domain_id)
    if os.getenv("NO_NVIDIA", default="false").lower() == "true":
        compose.mode = "configuration-no-nvidia"
    else:
        compose.mode = "configuration"
    compose.predefined_configuration = PredefinedConfigurations()
    compose.visualization = False

    platform_list = PlatformList()
    platform_list.platforms = request.cls.platforms.values()
    compose.predefined_configuration.plat_conf = platform_list

    load_ui = os.getenv("GAZEBO_UI", default="false").lower() == "true"
    world = getattr(request.cls, "world", "empty.sdf")
    sim_config = SimulatorConfig(load_ui=load_ui, world=world)
    compose.predefined_configuration.sim_conf = sim_config

    # Propagate dev mounts
    dev_mounts = os.getenv("DEV_MOUNTS", default="false") == "true"
    if dev_mounts:
        compose.dev = True
        host_cwd = os.getenv("HOST_CWD", default="/alliander")
        home_dir = os.getenv("HOME_DIR", default="/root")
        Compose.host_cwd = host_cwd
        Compose.home_dir = home_dir

    services = compose.create_compose(COMPOSE_FILE)
    return services


def skip_if_no_changes(services: list) -> None:
    """Skip the test if no relevant packages have changed.

    Args:
        services (list): The list of services required for the test.
    """
    required_packages = set(services)
    required_packages.add("alliander_core")
    if required_packages.isdisjoint(Configurations.changed_packages):
        pytest.skip(reason="No relevant packages have changed.")
    else:
        print("\n")
        print("Running test since the following relevant packages have changed:")
        print(required_packages.intersection(Configurations.changed_packages))
        print("\n")


def pull_missing_images() -> None:
    """Pull the missing Docker images required for the test."""
    compose = json.loads(
        subprocess.check_output(
            f"docker compose -f {COMPOSE_FILE} config --format json".split(),
        )
    )
    services = []
    images = []
    for service_name, service in compose["services"].items():
        services.append(service_name)
        images.append(service["image"])

    # Create list of services of which the image needs to be pulled:
    services_to_pull = []
    for image, service in zip(images, services, strict=False):
        try:
            subprocess.check_output(
                f"docker image inspect {image}".split(),
                stdin=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            cprint(f"Image {image} is already available locally.", "green")
        except subprocess.CalledProcessError:
            cprint(f"Image {image} is not available locally.", "yellow")
            services_to_pull.append(service)

    # Pull the missing images:
    cmd = f"docker compose -f {COMPOSE_FILE} pull {' '.join(services_to_pull)}"
    if os.getenv("NO_NVIDIA", default="false").lower() == "true":
        cmd += " --quiet"
    if services_to_pull:
        cprint(f"Pulling missing images: {services_to_pull}", "yellow")
        subprocess.run(cmd, timeout=3600, shell=True, check=True)


def wait_for_removal_nodes() -> None:
    """Wait for all active nodes to be stopped before moving on."""
    cprint("Checking ros2 node list before starting containers.", "blue")

    while active_nodes := subprocess.check_output(
        ["ros2", "node", "list"],
        stdin=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ):
        cprint(
            f"Waiting for the following nodes to exit: {active_nodes.decode('utf-8').strip()}",
            "red",
        )
        time.sleep(1)

    cprint("No more nodes active, moving on.", "blue")


def start_containers(services: list) -> subprocess.Popen:
    """Start the Docker containers for all services.

    Args:
        services (list): The list of services to start.

    Returns:
        subprocess.Popen: The process running the Docker containers.
    """
    process = subprocess.Popen([f"docker compose -f {COMPOSE_FILE} up"], shell=True)

    containers_started = False
    start_time = time.time()
    while not containers_started:
        containers_started = check_containers_started(COMPOSE_FILE, services)
        if time.time() - start_time > LAUNCH_TIMEOUT:
            stop_containers(COMPOSE_FILE)
            pytest.exit("Timeout waiting for containers to start. Exiting pytest.")
    cprint("All containers are started, start testing!", "green")

    return process


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
        try:
            name, status = line.strip("/").split()
        except ValueError:
            continue
        if name in services:
            statuses[name] = status == "healthy"
    if len(statuses) < len(services):
        return False
    return all(statuses.values())


@pytest.fixture(scope="class")
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


@pytest.fixture(scope="session")
def timeout(pytestconfig: Config) -> int:
    """Fixture to get the timeout value from pytest config return it.

    Args:
        pytestconfig (Config): The pytest configuration object.

    Returns:
        int: The timeout value in seconds.
    """
    return int(int(pytestconfig.getini("timeout")) / 2)


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
