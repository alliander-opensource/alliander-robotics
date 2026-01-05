# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import subprocess
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

TOOLS = typing.Literal["moveit", "nav2"]

predefined_configurations = PredefinedConfigurations.get_names()

dev_settings = {
    "volumes": [
        "${HOME}/.vscode-server:/root/.vscode-server",
        "./.personal.bashrc:/root/.personal.bashrc",
        "${HOME}/.nix-profile/bin/nvim:/usr/bin/nvim",
        "/nix/store:/nix/store",
        "./.env:/rcdt/.env",
        "./pyproject.toml:/rcdt/pyproject.toml",
        "./.config:/rcdt/.config",
        "./clangd:/rcdt/clangd",
        "./rcdt_core/src/rcdt_utilities:/rcdt/ros/src/rcdt_utilities",
    ],
}


class Compose:
    """Class to create docker-compose files based on the selected configuration or flags."""

    def __init__(
        self,
        platforms: dict[str, Platform],
        arch: str = "amd64",
        dev: bool = False,
        world: str = "",
    ) -> None:
        """Initialize."""
        self.platforms = platforms
        self.arch = arch
        self.dev = dev
        self.world = world

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
    def get_image_tag() -> str:
        """Get the image tag based on the current Git branch.

        Returns:
            str: The image tag.
        """
        # Set image_tag harcoded for now:
        return "latest"
        try:
            branch_name = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                universal_newlines=True,
                stderr=subprocess.PIPE,
            ).strip()
        except subprocess.CalledProcessError:
            print("Warning: not in a Git repository. Defaulting to 'latest'.")
            return "latest"
        except FileNotFoundError:
            print("Warning: 'git' command not found. Defaulting to 'latest'.")
            return "latest"

        if branch_name == "main":
            return "latest"
        return branch_name

    def compose_for_linting(self, output_file: str = "") -> dict:
        """Create a compose file for linting checks.

        Args:
            output_file (str): The output file of the compose.

        Returns:
            dict: The compose content.
        """
        filename = "rcdt_tests/docker-compose.yml"

        if not os.path.exists(filename):
            print(
                "Warning: did not find docker-compose.yml file in rcdt_tests. Exiting..."
            )
            sys.exit(1)

        with open(filename, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)

        service = content["services"]["rcdt_tests"]

        image_tag = self.get_image_tag()
        print(f"Image tag: {image_tag}")

        original_image = service["image"]
        service["image"] = original_image.replace(
            "${IMAGE_TAG}", f"{self.arch}-{image_tag}"
        )

        service["command"][-1] = "cd /rcdt_robotics && pre-commit run --all-files"

        print(f"\nWriting final compose file to {output_file}")

        with open(output_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(content, f, default_flow_style=False, sort_keys=False)

        return content

    def compose_for_test_container(self, output_file: str = "") -> dict:
        """Create a compose file for running the test container.

        Args:
            output_file (str): The output file of the compose.

        Returns:
            dict: The compose content.
        """
        filename = "rcdt_tests/docker-compose.yml"

        if not os.path.exists(filename):
            print(
                "Warning: did not find docker-compose.yml file in rcdt_tests. Exiting..."
            )
            sys.exit(1)

        with open(filename, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)

        service = content["services"]["rcdt_tests"]

        image_tag = self.get_image_tag()
        print(f"Image tag: {image_tag}")

        original_image = service["image"]
        service["image"] = original_image.replace(
            "${IMAGE_TAG}", f"{self.arch}-{image_tag}"
        )

        print(f"\nWriting final compose file to {output_file}")

        with open(output_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(content, f, default_flow_style=False, sort_keys=False)

        return content

    def compose_for_test(
        self, simulator: bool, visualization: bool, output_file: str
    ) -> int:
        """Create a compose file with the containers required to run the pytest.

        Args:
            simulator (bool): Whether to use simulation.
            visualization (bool): Whether to use visualization tools.
            output_file (str): The output file of the compose.

        Returns:
            int: The number of services in the compose.
        """
        compose: dict = self.compose_combined("", simulator, visualization)

        number_of_services = 0
        for service in compose["services"]:
            del compose["services"][service]["env_file"]
            compose["services"][service]["volumes"] = ["/dev:/dev"]
            number_of_services += 1

        with open(output_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(compose, f, default_flow_style=False, sort_keys=False)

        return number_of_services

    def compose_tool(self, platform: Platform, tool: TOOLS) -> dict:
        """Define the content of the platform related tools.

        Args:
            platform (Platform): The platform object.
            tool (TOOLS): The related tool.

        Returns:
            dict: The compose content.

        Raises:
            ValueError: If the tool is unknown.
        """
        if tool not in typing.get_args(TOOLS):
            raise ValueError(f"Unknown tool '{tool}'. Available: {TOOLS}")

        service_name = f"rcdt_{tool}"

        if platform.name in {"panther", "lynx"}:
            platform_service_name = "rcdt_husarion"
        else:
            platform_service_name = f"rcdt_{platform.name}"

        filename = f"{service_name}/docker-compose.yml"

        if not os.path.exists(filename):
            print(
                f"Warning: did not find docker-compose.yml file in {filename}. Exiting..."
            )
            sys.exit(1)

        with open(filename, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)

        service = content["services"][service_name]

        # Start tool when platfrorm is ready:
        service["depends_on"] = {}
        service["depends_on"][platform_service_name] = {"condition": "service_healthy"}

        image_tag = self.get_image_tag()
        print(f"Image tag: {image_tag}")

        original_image = service["image"]
        service["image"] = original_image.replace(
            "${IMAGE_TAG}", f"{self.arch}-{image_tag}"
        )

        if self.dev:
            src_mounts = self.get_src_mounts(service_name)
            service["volumes"] = (
                service["volumes"] + dev_settings["volumes"] + src_mounts
            )

        service["command"][-1] += f" config:='{platform.to_str()}'"

        return content

    def compose_combined(
        self,
        output_file: str = "",
        simulator: bool = False,
        visualization: bool = False,
    ) -> dict:
        """Create a combined compose file.

        Args:
            output_file (str): The output file of the compose.
            simulator (bool): Whether to use simulation.
            visualization (bool): Whether to include the visualization tools.

        Returns:
            dict: The compose content if output_file is not provided.
        """
        compose = self.compose_platforms()
        if simulator:
            compose["services"].update(self.compose_simulator()["services"])
        if visualization:
            compose["services"].update(self.compose_visualization()["services"])

        # Add Moveit or Nav2 for Arms or Vehicles:
        for platform in self.platforms.values():
            if (
                platform.platform_type == "Arm"
                and hasattr(platform, "moveit")
                and platform.moveit
            ):
                compose["services"].update(
                    self.compose_tool(platform, "moveit")["services"]
                )
            if (
                platform.platform_type == "Vehicle"
                and hasattr(platform, "nav2")
                and platform.nav2
            ):
                compose["services"].update(
                    self.compose_tool(platform, "nav2")["services"]
                )

        # Add healthchecks to all services:
        for service in compose["services"]:
            compose["services"][service]["healthcheck"] = {
                "test": ["CMD-SHELL", "[ -f /tmp/startup_complete ]"],
                "interval": "1s",
                "retries": 1000,
            }

        # Make visualization depenend on all other services:
        if visualization:
            compose["services"]["rcdt_visualization"]["depends_on"] = {}
            for service in compose["services"]:
                if service != "rcdt_visualization":
                    compose["services"]["rcdt_visualization"]["depends_on"][service] = {
                        "condition": "service_healthy"
                    }

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(compose, f, default_flow_style=False, sort_keys=False)

        return compose

    def compose_platforms(self, output_file: str = "platforms.yml") -> dict:
        """Create a compose file for the selected platforms.

        Args:
            output_file (str): The output file of the compose.

        Returns:
            dict: The compose content.
        """
        print("----- CREATING PLATFORMS.YML COMPOSE -----")
        merged_compose = {}
        image_tag = self.get_image_tag()

        print(f"Image tag: {image_tag}")
        print(f"Dev mode: {self.dev}")

        for platform in self.platforms.values():
            if platform.name in {"panther", "lynx"}:
                service_name = "rcdt_husarion"
            elif platform.name == "nmea_gps":
                service_name = "rcdt_gps"
            else:
                service_name = f"rcdt_{platform.name}"

            filename = f"{service_name}/docker-compose.yml"
            if not os.path.exists(filename):
                print(f"Warning: file {filename} not found. Skipping.")
                continue

            print(f"Merging {filename}")

            with open(filename, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)

            content["services"][service_name]["command"][-1] += (
                f" config:='{platform.to_str()}'"
            )

            if "services" in content:
                if "services" not in merged_compose:
                    merged_compose["services"] = {}
                merged_compose["services"].update(content["services"])

            for key, value in content.items():
                if key != "services" and key not in merged_compose:
                    merged_compose[key] = value

        # Replace image tag
        if "services" in merged_compose:
            for service_name, service_config in merged_compose["services"].items():
                if (
                    "image" in service_config
                    and "${IMAGE_TAG}" in service_config["image"]
                ):
                    original_image = service_config["image"]
                    service_config["image"] = original_image.replace(
                        "${IMAGE_TAG}", f"{self.arch}-{image_tag}"
                    )
                if self.dev:
                    src_mounts = self.get_src_mounts(service_name)
                    service_config["volumes"] = (
                        service_config["volumes"] + dev_settings["volumes"] + src_mounts
                    )

        print(f"\nWriting final compose file to {output_file}")

        with open(output_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(merged_compose, f, default_flow_style=False, sort_keys=False)

        print("Done!")
        return merged_compose

    def compose_simulator(self, output_file: str = "simulator.yml") -> dict:
        """Create a compose file for the simulator.

        Args:
            output_file (str): The output file of the compose.

        Returns:
            dict: The compose content.
        """
        print("----- CREATING SIMULATOR.YML COMPOSE -----")
        filename = "rcdt_gazebo/docker-compose.yml"

        simulator_config = SimulatorConfig()
        simulator_config.load_ui = True
        simulator_config.world = (
            EnvironmentConfiguration.world if not self.world else self.world
        )
        simulator_config.platforms = list(self.platforms.values())

        if not os.path.exists(filename):
            print(
                "Warning: did not find docker-compose.yml file in rcdt_gazebo. Exiting..."
            )
            sys.exit(1)

        with open(filename, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)

        service = content["services"]["rcdt_gazebo"]

        image_tag = self.get_image_tag()
        print(f"Image tag: {image_tag}")

        original_image = service["image"]
        service["image"] = original_image.replace(
            "${IMAGE_TAG}", f"{self.arch}-{image_tag}"
        )

        service["command"][-1] += f" config:='{simulator_config.to_str()}'"

        if self.dev:
            src_mounts_gazebo = self.get_src_mounts("rcdt_gazebo")
            src_mounts_husarion = self.get_src_mounts("rcdt_husarion")
            service["volumes"] = (
                service["volumes"]
                + dev_settings["volumes"]
                + src_mounts_gazebo
                + src_mounts_husarion
            )

        print(f"\nWriting final compose file to {output_file}")

        with open(output_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(content, f, default_flow_style=False, sort_keys=False)

        return content

    def compose_visualization(self, output_file: str = "visualization.yml") -> dict:
        """Create a compose file for the visualization visualization.

        Args:
            output_file (str): The output file of the compose.

        Returns:
            dict: The compose content.
        """
        print("----- CREATING TOOLS.YML COMPOSE -----")
        filename = "rcdt_visualization/docker-compose.yml"

        visualization_config = VisualizationConfig()
        visualization_config.rviz = True
        visualization_config.vizanti = False
        visualization_config.platforms = list(self.platforms.values())

        if not os.path.exists(filename):
            print(
                "Warning: did not find docker-compose.yml file in rcdt_visualization. Exiting..."
            )
            sys.exit(1)

        with open(filename, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)

        service = content["services"]["rcdt_visualization"]

        image_tag = self.get_image_tag()
        print(f"Image tag: {image_tag}")

        original_image = service["image"]
        service["image"] = original_image.replace(
            "${IMAGE_TAG}", f"{self.arch}-{image_tag}"
        )

        service["command"][-1] += f" config:='{visualization_config.to_str()}'"

        if self.dev:
            src_mounts = self.get_src_mounts("rcdt_visualization")
            service["volumes"] = (
                service["volumes"] + dev_settings["volumes"] + src_mounts
            )

        print(f"\nWriting final compose file to {output_file}")

        with open(output_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(content, f, default_flow_style=False, sort_keys=False)

        return content


if __name__ == "__main__":
    """
    Currently there are three separate compose calls: platforms, simulator, and visualization.
    In rcdt_husarion, in platforms, SIMULATION=true/false is needed. The way it is currently structured,
    the compose does not know if we want to add a simulator when calling compose_platforms().
    Maybe a fix is to put everything in one command (compose.py --platforms panther nav2 simulator), that
    then generates platforms.yml, simulator.yml, visualization.yml.
    """
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
        required=False,
        action="store_true",
        help="Add this flag to start the test container and run pytest inside it.",
    )

    parser.add_argument(
        "--linting",
        required=False,
        action="store_true",
        help="Add this flag to start the test container and run linting checks inside it.",
    )

    args = parser.parse_args()

    if args.configuration:
        PredefinedConfigurations.apply_configuration(args.configuration)
        platforms = EnvironmentConfiguration.platforms
        compose = Compose(platforms, args.arch, args.dev)
        compose.compose_combined("compose.yml", args.simulator, args.visualization)
    elif args.pytest:
        compose = Compose({}, args.arch, args.dev)
        compose.compose_for_test_container("compose.yml")
    elif args.linting:
        compose = Compose({}, args.arch, args.dev)
        compose.compose_for_linting("compose.yml")
