# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import argparse
import os
import sys
import typing
from pathlib import Path

import yaml

from predefined_configurations import PredefinedConfigurations
from rcdt_core.src.rcdt_utilities.rcdt_utilities.config_objects import (
    EnvironmentConfiguration,
    Platform,
    SimulatorConfig,
    VisualizationConfig,
)

SERVICE = typing.Literal[
    "platform",
    "simulator",
    "moveit",
    "nav2",
    "visualization",
    "pytest",
    "pytest-no-nvidia",
    "linting",
]
MODE = typing.Literal["configuration", "test", "pytest", "pytest-no-nvidia", "linting"]

predefined_configurations = PredefinedConfigurations.get_names()

dev_settings = {
    "volumes": [
        "${HOME}/.vscode-server:/root/.vscode-server",
        "./.personal.bashrc:/root/.personal.bashrc",
        "${HOME}/.nix-profile/bin/nvim:/usr/bin/nvim",
        "/nix/store:/nix/store",
        "./pyproject.toml:/rcdt/pyproject.toml",
        "./.config:/rcdt/.config",
        "./clangd:/rcdt/clangd",
        "./rcdt_core/src/rcdt_utilities:/rcdt/ros/src/rcdt_utilities",
    ],
}


class Compose:
    """Class to create docker-compose files."""

    def __init__(self) -> None:
        """Initialize."""
        self.platforms: dict[str, Platform] = {}
        self.simulator = True
        self.visualization = True
        self.arch = "amd64"
        self.dev = False
        self.world = ""

    @staticmethod
    def get_src_mounts(package: str) -> list[str]:
        """Get the src mounts for a given package.

        Args:
            package (str): The package name.

        Returns:
            list[str]: A list of volume mount strings.
        """
        cwd = Path.cwd()
        src_dir = cwd.joinpath(f"{package}", "src")
        return [
            f"./{str(p.relative_to(cwd))}:/rcdt/ros/src/{p.name}"
            for p in src_dir.iterdir()
            if p.is_dir()
        ]

    @staticmethod
    def load_compose(filename: str) -> dict:
        """Load a compose file.

        Args:
            filename (str): The compose file name.

        Returns:
            dict: The content of the compose file.
        """
        if not os.path.exists(filename):
            print(f"Warning: did not find {filename}. Exiting...")
            sys.exit(1)

        with open(filename, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @staticmethod
    def write_compose(filename: str, content: dict) -> None:
        """Write a compose file.

        Args:
            filename (str): The compose file name.
            content (dict): The content of the compose file.
        """
        with open(filename, "w", encoding="utf-8") as f:
            yaml.safe_dump(content, f, default_flow_style=False, sort_keys=False)

    def add_service(
        self,
        content: dict,
        mode: SERVICE,
        platform: Platform | None = None,
        arguments: str = "",
    ) -> None:
        """Create a service for a docker compose file.

        Args:
            content (dict): The existing compose content to update.
            mode (MODE): The type of compose to create.
            platform (Platform | None): The platform object (required for 'platform' mode).
            arguments (str): Additional arguments that can be appended to the command.

        Raises:
            ValueError: If platform mode is selected but no platform is provided.
        """
        match mode:
            case "platform" | "moveit" | "nav2":
                if platform is None:
                    raise ValueError(f"Platform must be provided when mode is '{mode}'")
                package = platform.package() if mode == "platform" else f"rcdt_{mode}"
                command = f" config:='{platform.to_str()}'"
            case "simulator":
                package = "rcdt_gazebo"
                simulator_config = SimulatorConfig()
                simulator_config.load_ui = EnvironmentConfiguration.gazebo_ui
                simulator_config.world = (
                    EnvironmentConfiguration.world if not self.world else self.world
                )
                simulator_config.platforms = list(self.platforms.values())
                command = f" config:='{simulator_config.to_str()}'"
            case "visualization":
                package = "rcdt_visualization"
                visualization_config = VisualizationConfig()
                visualization_config.rviz = EnvironmentConfiguration.rviz
                visualization_config.vizanti = EnvironmentConfiguration.vizanti
                visualization_config.gui = EnvironmentConfiguration.rcdt_gui
                visualization_config.platforms = list(self.platforms.values())
                command = f" config:='{visualization_config.to_str()}'"
            case "linting":
                package = "rcdt_tests"
                command = " && pre-commit run --all-files"
            case "pytest" | "pytest-no-nvidia":
                package = "rcdt_tests"
                command = " && pytest --ignore=ros2_ws -s -rsxf" + arguments

        # General:
        filename = f"{package}/docker-compose.yml"
        service = self.load_compose(filename)["services"][package]
        original_image: str = service["image"]
        service["image"] = original_image.replace("${IMAGE_TAG}", f"{self.arch}")
        service["command"][-1] += command

        # Dependencies:
        if mode in {"moveit", "nav2"}:
            if platform is None:
                raise ValueError(f"Platform must be provided when mode is '{mode}'")
            service["depends_on"] = {}
            service["depends_on"][platform.package()] = {"condition": "service_healthy"}

        # Dev settings:
        if self.dev:
            src_mounts = self.get_src_mounts(package)
            service["volumes"] = (
                service["volumes"] + dev_settings["volumes"] + src_mounts
            )

        # Remove runtime: nvidia if pytest-no-nvidia
        if mode in {"linting", "pytest-no-nvidia"} and "runtime" in service:
            del service["runtime"]
        content["services"][package] = service

    def create_compose(
        self,
        mode: MODE,
        output_file: str = "compose.yml",
        arguments: str = "",
    ) -> int:
        """Create a combined compose file.

        Args:
            mode: MODE: The use case for the compose file.
            output_file (str): The output compose file name.
            arguments (str): Additional arguments that can be passed to a service command.

        Returns:
            dict: The compose content if output_file is not provided.
        """
        content = {"services": {}}
        services = content["services"]

        match mode:
            case "pytest" | "pytest-no-nvidia":
                self.add_service(content, mode, arguments=arguments)
            case "linting":
                self.add_service(content, "linting")
            case "configuration" | "test":
                for platform in self.platforms.values():
                    self.add_service(content, "platform", platform)
                    if getattr(platform, "moveit", False):
                        self.add_service(content, "moveit", platform)
                    if getattr(platform, "nav2", False):
                        self.add_service(content, "nav2", platform)
                if self.simulator:
                    self.add_service(content, "simulator")
                if self.visualization:
                    self.add_service(content, "visualization")
                    services["rcdt_visualization"]["depends_on"] = {}

        # Add healthchecks to all services:
        for name, service in services.items():
            service["healthcheck"] = {
                "test": ["CMD-SHELL", "[ -f /tmp/startup_complete ]"],
                "interval": "1s",
                "retries": 1000,
            }
            # Make visualization depenend on all other services:
            if "rcdt_visualization" in services and name != "rcdt_visualization":
                services["rcdt_visualization"]["depends_on"][name] = {
                    "condition": "service_healthy"
                }
            if mode == "test":
                for test_service in services.values():
                    test_service["volumes"] = ["/dev:/dev"]

        self.write_compose(output_file, content)
        return len(services)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Creates a combined docker-compose.yml file from platform-specific composes."
    )

    parser.add_argument(
        "--arch",
        required=False,
        choices=["amd64", "arm64"],
        default="amd64",
        help="Target architecture (amd64 or arm64).",
    )

    parser.add_argument(
        "-p",
        "--platforms",
        required=False,
        nargs="+",
        help="List of platform components to include (e.g. panther franka) in a platforms.yaml compose file.",
    )

    parser.add_argument(
        "-c",
        "--configuration",
        required=False,
        help="Select a predefined configuration.",
    )

    parser.add_argument(
        "--simulator",
        required=False,
        action="store_true",
        help="Add this flag to build a simulator.yml compose file, indicating which platforms are present in the simulation with the '--platforms' tag.",
    )

    parser.add_argument(
        "--visualization",
        required=False,
        action="store_true",
        help="Add this flag to build a visualization.yml compose file, indicating which platforms are present in Rviz / Vizanti with the '--platforms' tag.",
    )

    parser.add_argument(
        "--dev",
        required=False,
        action="store_true",
        help="Add this flag to enable dev mode, where repo folders are mounted into the container.",
    )

    parser.add_argument(
        "--pytest",
        default=False,
        nargs=argparse.REMAINDER,
        help="Add this flag to start the test container and run pytest inside it.",
    )

    parser.add_argument(
        "--pytest-no-nvidia",
        default=False,
        nargs=argparse.REMAINDER,
        help="Add this flag to start the test container, without the NVIDIA runtime, and run pytest inside it.",
    )

    parser.add_argument(
        "--linting",
        required=False,
        action="store_true",
        help="Add this flag to start the test container and run linting checks inside it.",
    )

    args = parser.parse_args()

    compose = Compose()
    if args.configuration:
        PredefinedConfigurations.apply_configuration(args.configuration)
        compose.simulator = args.simulator
        compose.visualization = args.visualization
        compose.arch = args.arch
        compose.dev = args.dev
        compose.platforms = EnvironmentConfiguration.platforms
        compose.create_compose("configuration")
    elif isinstance(args.pytest, list):
        arguments = " " + " ".join(args.pytest)
        compose.create_compose("pytest", arguments=arguments)
    elif isinstance(args.pytest_no_nvidia, list):
        arguments = " " + " ".join(args.pytest_no_nvidia)
        compose.create_compose("pytest-no-nvidia", arguments=arguments)
    elif args.linting:
        compose.create_compose("linting")
