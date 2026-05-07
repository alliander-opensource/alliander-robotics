# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import sys

from alliander_robotics.compose import Compose
from alliander_robotics.predefined_configurations import PredefinedConfigurations


class Parser(argparse.ArgumentParser):
    """Parser for the start.py script."""

    def __init__(self) -> None:
        """Initialize the parser."""
        super().__init__()
        self.description = "Creates and runs a combined docker-compose.yml file from platform-specific composes."

        # RUNNABLES
        self.add_argument(
            "configuration",
            nargs="?",
            help="Select a predefined configuration.",
        )

        self.add_argument(
            "--pytest",
            default=False,
            nargs=argparse.REMAINDER,
            help="Add this flag to start the test container and run pytest inside it.",
        )

        self.add_argument(
            "--pytest-no-nvidia",
            default=False,
            nargs=argparse.REMAINDER,
            help="Add this flag to start the test container, without the NVIDIA runtime, and run pytest inside it.",
        )

        self.add_argument(
            "--linting",
            required=False,
            action="store_true",
            help="Add this flag to start the test container and run linting checks inside it.",
        )

        self.add_argument(
            "--documentation",
            required=False,
            action="store_true",
            help="Add this flag to start a container serving the documentation with live reloading.",
        )

        # FLAGS
        self.add_argument(
            "-w",
            "--hardware",
            required=False,
            action="store_true",
            help="Add this flag to indicate the configuration should run on hardware (as opposed to with Gazebo).",
        )

        self.add_argument(
            "-v",
            "--visualization",
            required=False,
            action="store_true",
            help="Add this flag to include visualization tools (Rviz, Vizanti) in the configuration.",
        )

        self.add_argument(
            "-d",
            "--dev",
            required=False,
            action="store_true",
            help="Add this flag to enable dev mode, where repo folders are mounted into the container.",
        )

        self.add_argument(
            "-u",
            "--ui",
            required=False,
            action="store_true",
            help="Add this flag to enable the Gazebo UI in containers.",
        )

        self.add_argument(
            "-j",
            "--joystick",
            required=False,
            action="store_true",
            help="Add this flag to enable joystick control for arm and/or vehicle platforms.",
        )

        self.add_argument(
            "-m",
            "--meta",
            required=False,
            action="store_true",
            help="Add this flag to enable Meta Quest control for arm platforms.",
        )

        self.add_argument(
            "--rviz",
            required=False,
            action="store_true",
            help="Add this flag to create an additional Rviz config in rviz.yml. You still need to specify platforms.",
        )

        self.add_argument(
            "--no-run",
            required=False,
            action="store_true",
            help="Add this flag if you only want to create the YML files, but not run them.",
        )

    def run(self) -> None:
        """Run the parser."""
        args = self.parse_args()
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
            compose.meta = args.meta
            compose.rviz_yaml = args.rviz
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
        if not args.no_run:
            ret = compose.run_compose()
            sys.exit(ret)
