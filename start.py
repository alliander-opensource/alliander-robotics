# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import argparse
import contextlib
import os
import subprocess
import sys
import typing
from pathlib import Path

import yaml

import utils
from alliander_core.src.alliander_utilities.alliander_utilities.config_objects import (
    Platform,
)
from predefined_configurations import PredefinedConfigurations

SERVICE = typing.Literal[
    "platform",
    "simulator",
    "moveit",
    "nav2",
    "visualization",
    "pytest",
    "pytest-no-nvidia",
    "linting",
    "documentation",
    "joystick",
    "diagnostics",
]
MODE = typing.Literal[
    "configuration",
    "configuration-no-nvidia",
    "pytest",
    "pytest-no-nvidia",
    "linting",
    "documentation",
]


class Compose:
    """Class to create docker-compose files.

    Attributes:
        dev_settings (dict): dictionary of additional settings to include if self.dev is set to True.
        host_cwd (str): current working directory on host machine, needed to propagate mounts inside test containers.
        home_dir (str): home directory on host machine, needed to propagate mounts inside test containers.
    """

    dev_settings: dict = {
        "volumes": [
            "${HOME}/.nix-profile/bin/nvim:/usr/bin/nvim",
            "/nix/store:/nix/store",
            "./pyproject.toml:/alliander/pyproject.toml",
            "./alliander_core/src/alliander_utilities:/alliander/ros/src/alliander_utilities",
        ],
    }
    host_cwd: str = os.path.abspath(os.getcwd())
    home_dir: str = os.path.expanduser("~")

    def __init__(self) -> None:
        """Initialize."""
        self.mode: MODE | None = None
        self.remove_nvidia = False
        self.predefined_configuration = PredefinedConfigurations()
        self.simulator = True
        self.visualization = True
        self.dev = False
        self.gazebo_ui = False
        self.joystick = False

        self.changed_packages = utils.get_changed_packages()

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
            f"./{str(p.relative_to(cwd))}:/alliander/ros/src/{p.name}"
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

    def get_service_config(
        self, service_type: SERVICE, platform: Platform | None, arguments: str
    ) -> tuple[str, str, dict]:
        """Gets the relevant package, the command, and additional config for a given service type.

        Args:
            service_type (SERVICE): service type to get config for.
            platform (Platform | None): platform to get config for, or None if not a platform.
            arguments (str): additional arguments for pytest.

        Returns:
            tuple[str, str, dict]: tuple consisting of the package, the config for compose, and additional config.

        Raises:
            ValueError: if platform is not provided while a platform is needed.
        """
        needs_platform = service_type in {"platform", "moveit", "nav2"}
        if needs_platform and platform is None:
            raise ValueError(f"Platform required for '{service_type}'")

        if platform and needs_platform:
            platform.simulation = self.simulator

        base_configs = {
            "simulator": (
                "alliander_gazebo",
                (
                    f" platform_list:='{self.predefined_configuration.plat_conf.to_str()}'"
                    f" sim_config:='{self.predefined_configuration.sim_conf.to_str()}'"
                ),
                {},
            ),
            "visualization": (
                "alliander_visualization",
                (
                    f" platform_list:='{self.predefined_configuration.plat_conf.to_str()}'"
                    f" vis_config:='{self.predefined_configuration.viz_conf.to_str()}'"
                ),
                {},
            ),
            "joystick": (
                "alliander_joystick",
                f" platform_list:='{self.predefined_configuration.plat_conf.to_str()}'",
                {},
            ),
            "diagnostics": (
                "alliander_diagnostics",
                (
                    f" platform_list:='{self.predefined_configuration.plat_conf.to_str()}'"
                    f" use_sim_time:='{self.simulator}'"
                ),
                {},
            ),
            "linting": (
                "alliander_tests",
                " && pre-commit run --all-files",
                {},
            ),
            "documentation": (
                "alliander_tests",
                " && sphinx-autobuild --port 0 docs docs/build/html",
                {},
            ),
            "pytest": (
                "alliander_tests",
                " && pytest -s -rsxf" + arguments,
                {},
            ),
            "pytest-no-nvidia": (
                "alliander_tests",
                " && pytest -s -rsxf" + arguments,
                {},
            ),
        }

        if platform is not None:
            platform_configs = {
                "platform": (
                    platform.package(),
                    f" platform_config:='{platform.to_str()}'",
                    {"needs_dependency": False},
                ),
                "moveit": (
                    "alliander_moveit",
                    f" platform_config:='{platform.to_str()}'",
                    {"needs_dependency": True},
                ),
                "nav2": (
                    "alliander_nav2",
                    f" platform_config:='{platform.to_str()}'",
                    {"needs_dependency": True},
                ),
            }
            configs = {**base_configs, **platform_configs}
        else:
            configs = base_configs

        return configs[service_type]

    def load_service_base(self, package: str, command: str) -> dict:
        """Loads the base compose file for a certain package and adds a command.

        Args:
            package (str): package to get docker-compose.yml file from.
            command (str): command to put in command field in docker-compose.yml file.

        Returns:
            dict: dictionary containing YAML data from docker-compose.yml, with added command.
        """
        print(f"{package}")
        service = self.load_compose(f"{package}/docker-compose.yml")["services"][
            package
        ]

        # Use the branch tag if the package has changes:
        name_branch = subprocess.getoutput("git rev-parse --abbrev-ref HEAD")
        if package in self.changed_packages:
            service["image"] += f":{name_branch}"

        if self.mode == "configuration-no-nvidia":
            service["init"] = True
            service["command"][-1] = f"xvfb-run -a {service['command'][-1]}"
        service["command"][-1] += command
        return service

    @staticmethod
    def apply_dependencies(
        service: dict, config: dict, platform: Platform | None
    ) -> None:
        """Adds a depends_on to wait on the platform container being healthy before starting.

        Args:
            service (dict): dictionary containing Docker container's YAML config.
            config (dict): additional config, in this case to specify if a depends_on is needed.
            platform (Platform | None): platform that depends_on waits for, or None if not applicable.
        """
        if config.get("needs_dependency") and platform:
            service["depends_on"] = {
                platform.package(): {"condition": "service_healthy"}
            }

    def apply_dev_settings(self, service: dict, package: str) -> None:
        """Adds dev mounts to a specific service, if applicable.

        Args:
            service (dict): dictionary containing Docker container's YAML config.
            package (str): package to mount in container, such that live code updates are possible.
        """
        if self.dev:
            src_mounts = self.get_src_mounts(package)
            all_mounts = (
                service["volumes"] + Compose.dev_settings["volumes"] + src_mounts
            )

            # abslute host path so mounts persist in pytest containers
            all_mounts = [m.replace("./", f"{Compose.host_cwd}/") for m in all_mounts]
            all_mounts = [
                m.replace("${HOME}", f"{Compose.home_dir}") for m in all_mounts
            ]
            service["volumes"] = all_mounts

    def apply_runtime_settings(self, service: dict) -> None:
        """Removes NVIDIA runtime if necessary.

        Args:
            service (dict): dictionary containing Docker container's YAML config.
        """
        if self.remove_nvidia and "runtime" in service:
            del service["runtime"]

    def apply_env_settings(self, service: dict, service_type: SERVICE) -> None:
        """Applies environment variables to the pytest container, so that they can being propagated to the containers started inside the pytest container.

        Args:
            service (dict): dictionary containing Docker container's YAML config.
            service_type (SERVICE): type of service being created.
        """
        if service_type not in {"pytest", "pytest-no-nvidia"}:
            return

        env_vars = service.get("environment", [])
        if self.predefined_configuration.sim_conf.load_ui:
            env_vars.append("GAZEBO_UI=true")
        if self.dev:
            env_vars.append("DEV_MOUNTS=true")
            env_vars.append(f"HOST_CWD={Compose.host_cwd}")
            env_vars.append(f"HOME_DIR={Compose.home_dir}")
        if service_type == "pytest-no-nvidia":
            env_vars.append("NO_NVIDIA=true")
        service["environment"] = env_vars

    def add_service(
        self,
        content: dict,
        service_type: SERVICE,
        platform: Platform | None = None,
        arguments: str = "",
    ) -> None:
        """Create a service for a docker compose file.

        Args:
            content (dict): The existing compose content to update.
            service_type (SERVICE): Type of service to add to the compose.
            platform (Platform | None): The platform object (required for 'platform' mode).
            arguments (str): Additional arguments that can be appended to the command.
        """
        package, command, config = self.get_service_config(
            service_type, platform, arguments
        )

        service = self.load_service_base(package, command)
        self.apply_dependencies(service, config, platform)
        self.apply_dev_settings(service, package)
        self.apply_runtime_settings(service)
        self.apply_env_settings(service, service_type)

        content["services"][package] = service

    def create_compose(  # noqa: PLR0912
        self,
        output_file: str = "compose.yml",
        arguments: str = "",
    ) -> list:
        """Create a combined compose file.

        Args:
            output_file (str): The output compose file name.
            arguments (str): Additional arguments that can be passed to a service command.

        Returns:
            list: The names of the services in the compose file.
        """
        content = {"services": {}}
        services = content["services"]

        # Remove NVIDIA runtime for linting or no-nvidia runs:
        if self.mode in {"linting", "configuration-no-nvidia", "pytest-no-nvidia"}:
            self.remove_nvidia = True

        match self.mode:
            case "pytest" | "pytest-no-nvidia":
                self.add_service(content, self.mode, arguments=arguments)
            case "linting":
                self.add_service(content, "linting")
            case "documentation":
                self.add_service(content, "documentation")
            case "configuration" | "configuration-no-nvidia":
                self.add_service(content, "diagnostics")
                for platform in self.predefined_configuration.plat_conf.platforms:
                    self.add_service(content, "platform", platform)
                    if getattr(platform, "moveit", False):
                        self.add_service(content, "moveit", platform)
                    if getattr(platform, "nav2", False):
                        self.add_service(content, "nav2", platform)
                if self.simulator:
                    self.add_service(content, "simulator")
                if self.visualization:
                    self.add_service(content, "visualization")
                    services["alliander_visualization"]["depends_on"] = {}
                if self.joystick:
                    self.add_service(content, "joystick")

        # Add healthchecks to all services:
        for name, service in services.items():
            service["healthcheck"] = {
                "test": ["CMD-SHELL", "[ -f /tmp/startup_complete ]"],
                "interval": "1s",
                "retries": 1000,
            }
            # Make visualization depenend on all other services:
            if (
                "alliander_visualization" in services
                and name != "alliander_visualization"
            ):
                services["alliander_visualization"]["depends_on"][name] = {
                    "condition": "service_healthy"
                }

        self.write_compose(output_file, content)
        return list(services.keys())

    def run_compose(self) -> int:
        """Runs generated compose.yml file.

        Returns:
            int: return code from docker compose run.
        """
        cmd = "docker compose -f compose.yml up"
        if self.mode in {"linting", "pytest", "pytest-no-nvidia"}:
            cmd += " --abort-on-container-exit"
        if self.mode == "pytest-no-nvidia":
            cmd += " --quiet-pull"

        result = subprocess.CompletedProcess([], 0)
        with contextlib.suppress(KeyboardInterrupt):
            result = subprocess.run([cmd], shell=True, check=False)

        # Stop containers:
        cmd = ["docker compose -f compose.yml down -t 1"]
        subprocess.run(cmd, shell=True, check=True)

        # Stop containers started for pytest:
        if self.mode in {"pytest", "pytest-no-nvidia"}:
            cmd = ["docker compose -f compose_pytest.yml down -t 1"]
            subprocess.run(cmd, shell=True, check=True)
            cmd = ["docker compose -f compose_pytest.yml rm -fsv"]
            subprocess.run(cmd, shell=True, check=True)

        return result.returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Creates and runs a combined docker-compose.yml file from platform-specific composes."
    )

    # RUNNABLES
    parser.add_argument(
        "configuration",
        nargs="?",
        help="Select a predefined configuration.",
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

    parser.add_argument(
        "--documentation",
        required=False,
        action="store_true",
        help="Add this flag to start a container serving the documentation with live reloading.",
    )

    # FLAGS
    parser.add_argument(
        "-w",
        "--hardware",
        required=False,
        action="store_true",
        help="Add this flag to indicate the configuration should run on hardware (as opposed to with Gazebo).",
    )

    parser.add_argument(
        "-v",
        "--visualization",
        required=False,
        action="store_true",
        help="Add this flag to include visualization tools (Rviz, Vizanti) in the configuration.",
    )

    parser.add_argument(
        "-d",
        "--dev",
        required=False,
        action="store_true",
        help="Add this flag to enable dev mode, where repo folders are mounted into the container.",
    )

    parser.add_argument(
        "-u",
        "--ui",
        required=False,
        action="store_true",
        help="Add this flag to enable the Gazebo UI in containers.",
    )

    parser.add_argument(
        "-j",
        "--joystick",
        required=False,
        action="store_true",
        help="Add this flag to enable joystick control for arm and/or vehicle platforms.",
    )

    # Parse arguments:
    args = parser.parse_args()
    compose = Compose()
    arguments = ""

    config_setup = PredefinedConfigurations()
    config_setup.sim_conf.load_ui = args.ui
    compose.dev = args.dev
    if args.configuration:
        config_setup.apply_configuration(args.configuration)
        compose.simulator = not args.hardware
        compose.visualization = args.visualization
        compose.joystick = args.joystick
        compose.mode = "configuration"
    elif isinstance(args.pytest, list):
        arguments = " " + " ".join(args.pytest)
        compose.gazebo_ui = args.ui
        compose.mode = "pytest"
    elif isinstance(args.pytest_no_nvidia, list):
        arguments = " " + " ".join(args.pytest_no_nvidia)
        compose.mode = "pytest-no-nvidia"
    elif args.linting:
        compose.mode = "linting"
    elif args.documentation:
        compose.mode = "documentation"
    else:
        print(
            "Invalid configuration. Please check your arguments. Run with --help to see your options."
        )
        sys.exit(1)
    compose.predefined_configuration = config_setup

    # Create compose file:
    compose.create_compose(arguments=arguments)

    # Spin up containers:
    ret = compose.run_compose()
    sys.exit(ret)
