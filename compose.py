import argparse
import os
import subprocess
import sys
from pathlib import Path

import yaml

from predefined_configurations import PredefinedConfigurations
from rcdt_core.src.rcdt_utilities.rcdt_utilities.config_objects import (
    EnvironmentConfiguration,
    Platform,
    SimulatorConfig,
    ToolsConfig,
)

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
        "./rcdt_core/src/rcdt_utilities:/rcdt/ros/src/rcdt_utilities"
    ],
}


class Compose:
    def __init__(
        self,
        platforms: list[Platform],
        arch: str = "amd64",
        dev: bool = False,
        simulator: bool = False,
        tools: bool = False,
    ) -> None:
        self.platforms = platforms
        self.arch = arch
        self.dev = dev

        if simulator:
            self.compose_simulator()
        if tools:
            self.compose_tools()
        if not simulator and not tools:
            self.compose_platforms()

    @staticmethod
    def get_src_mounts(package: str) -> list[str]:
        cwd = Path.cwd()
        src_dir = cwd.joinpath(f"{package}", "src")
        return [
            f"./{str(p.relative_to(cwd))}:/rcdt/ros/src/{p.name}"
            for p in src_dir.iterdir()
            if p.is_dir()
        ]

    @staticmethod
    def get_image_tag():
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

    def compose_platforms(self, output_file: str = "platforms.yml"):
        print("----- CREATING PLATFORMS.YML COMPOSE -----")
        merged_compose = {}
        image_tag = self.get_image_tag()

        print(f"Image tag: {image_tag}")
        print(f"Dev mode: {self.dev}")

        for platform in self.platforms.values():
            if platform.name in {"panther", "lynx"}:
                service_name = "rcdt_husarion"
            else:
                service_name = f"rcdt_{platform.name}"

            filename = f"{service_name}/docker-compose.yml"
            if not os.path.exists(filename):
                print(f"Warning: file {filename} not found. Skipping.")
                continue

            print(f"Merging {filename}")

            with open(filename, "r") as f:
                content = yaml.safe_load(f)

                if not content:
                    continue

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

        if not merged_compose:
            print("Error: no compose files were merged. Aborting.")
            return

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

        with open(output_file, "w") as f:
            yaml.safe_dump(merged_compose, f, default_flow_style=False, sort_keys=False)

        print("Done!")

    def compose_simulator(self, output_file: str = "simulator.yml"):
        print("----- CREATING SIMULATOR.YML COMPOSE -----")
        filename = "rcdt_gazebo/docker-compose.yml"

        simulator_config = SimulatorConfig()
        simulator_config.load_ui = True
        simulator_config.platforms = list(self.platforms.values())

        if not os.path.exists(filename):
            print(
                "Warning: did not find docker-compose.yml file in rcdt_gazebo. Exiting..."
            )
            sys.exit(1)

        with open(filename, "r") as f:
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

            with open(output_file, "w") as f:
                yaml.safe_dump(content, f, default_flow_style=False, sort_keys=False)

    def compose_tools(self, output_file: str = "tools.yml"):
        print("----- CREATING TOOLS.YML COMPOSE -----")
        filename = "rcdt_tools/docker-compose.yml"

        tools_config = ToolsConfig()
        tools_config.rviz = True
        tools_config.vizanti = False
        tools_config.platforms = list(self.platforms.values())

        if not os.path.exists(filename):
            print(
                "Warning: did not find docker-compose.yml file in rcdt_tools. Exiting..."
            )
            sys.exit(1)

        with open(filename, "r") as f:
            content = yaml.safe_load(f)
            service = content["services"]["rcdt_tools"]

            image_tag = self.get_image_tag()
            print(f"Image tag: {image_tag}")

            original_image = service["image"]
            service["image"] = original_image.replace(
                "${IMAGE_TAG}", f"{self.arch}-{image_tag}"
            )

            service["command"][-1] += f" config:='{tools_config.to_str()}'"

            if self.dev:
                src_mounts = self.get_src_mounts("rcdt_tools")
                service["volumes"] = (
                    service["volumes"] + dev_settings["volumes"] + src_mounts
                )

            print(f"\nWriting final compose file to {output_file}")

            with open(output_file, "w") as f:
                yaml.safe_dump(content, f, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    """
    Currently there are three separate compose calls: platforms, simulator, and tools.
    In rcdt_husarion, in platforms, SIMULATION=true/false is needed. The way it is currently structured,
    the compose does not know if we want to add a simulator when calling compose_platforms().
    Maybe a fix is to put everything in one command (compose.py --platforms panther nav2 simulator), that
    then generates platforms.yml, simulator.yml, tools.yml.
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
        "--tools",
        required=False,
        action="store_true",
        help="Add this flag to build a tools.yml compose file, indicating which platforms are present in Rviz / Vizanti with the '--platforms' tag.",
    )

    parser.add_argument(
        "--dev",
        required=False,
        action="store_true",
        help="Add this flag to enable dev mode, where repo folders are mounted into the container.",
    )

    args = parser.parse_args()

    if args.configuration:
        PredefinedConfigurations.apply_configuration(args.configuration)
        platforms = EnvironmentConfiguration.platforms

    compose = Compose(platforms, args.arch, args.dev, args.simulator, args.tools)
