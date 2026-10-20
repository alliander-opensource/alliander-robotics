# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import argparse
import re
import subprocess
import sys

from termcolor import colored, cprint

from alliander_robotics import utils

DOCKER_ORGANIZATION = "allianderrobotics"
TAG_REGEX = re.compile(r"\w[\w.-]{0,127}", re.ASCII)
REPO_REGEX = re.compile(r"[a-z0-9]+(?:[._-][a-z0-9]+)*")


class ImageManager:
    """Class to pull or build Docker images.

    Attributes:
        components (dict): dictionary containing the components to pull or build, as defined in components.yml
    """

    components: dict = utils.load_components()

    def __init__(self, no_cache: bool = False) -> None:
        """Initialize class.

        Args:
            no_cache (bool): whether to use the cache when building. no_cache defaults to False.
        """
        self.no_cache = no_cache

        self.arch = subprocess.getoutput("dpkg --print-architecture")
        if self.arch not in {"amd64", "arm64"}:
            print(f"Architecture {self.arch} is not supported.")
            sys.exit(1)

        self.selected = []

    def select_repositories(self, repositories: list[str]) -> None:
        """Selects repositories to pull or build. If no repositories are provided, all repositories are selected.

        Args:
            repositories (list[str]): list of repositories to select.
        """
        if not repositories:
            self.selected = list(self.components.keys())
            return
        for repository in repositories:
            if repository not in self.components:
                print(f"Repository {repository} not found in components.yml.")
                sys.exit(1)
        self.selected = repositories

    def run(self, pull: bool, build: bool) -> None:
        """Pull or build the docker images for all selected repositories.

        Args:
            pull (bool): whether to pull the images.
            build (bool): whether to build the images.
        """

        def colored_bool(value: bool) -> str:
            return colored(str(value), "green" if value else "red")

        print(f"pull: {colored_bool(pull)}, build: {colored_bool(build)}")
        print(f"repositories: {self.selected}")

        changed_packages = utils.get_changed_packages()
        for repository in self.selected:
            package = f"alliander_{repository}"
            tag = (
                "latest"
                if set({package, "alliander_core"}).isdisjoint(changed_packages)
                else utils.get_git_branch()
            )

            tag = "latest" if tag == "main" else tag

            if pull:
                self.run_pull_subprocess(repository, tag)
            if build:
                self.run_build_subprocess(repository, tag)

    @staticmethod
    def run_pull_subprocess(repository: str, tag: str = "latest") -> None:
        """Runs a docker pull command to pull a specific image.

        Args:
            repository (str): repository of the docker image to build.
            tag (str): tag of the docker image to pull.

        Raises:
            ValueError: If repository or tag name contains illegal characters.
        """
        cprint(
            f"\n\n\n---------- Pulling {DOCKER_ORGANIZATION}/{repository}:{tag} ----------",
            "blue",
        )

        if not TAG_REGEX.fullmatch(repository) or not TAG_REGEX.fullmatch(tag):
            raise ValueError("Invalid repository or tag")
        subprocess.run(
            ["docker", "pull", f"{DOCKER_ORGANIZATION}/{repository}:{tag}"], check=True
        )

    def run_build_subprocess(self, repository: str, tag: str = "latest") -> None:
        """Runs a docker build command to build a specific image.

        Args:
            repository (str): repository of the docker image to build.
            tag (str): tag of the docker image to build.

        Raises:
            ValueError: If repository or tag name contains illegal characters.
        """
        cprint(
            f"\n\n\n---------- Building {DOCKER_ORGANIZATION}/{repository}:{tag} ----------",
            "blue",
        )

        cache_args = []
        if self.no_cache:
            cache_args = ["--no-cache"]

        base_image_tag = (
            "latest" if not utils.is_core_docker_changed() else utils.get_git_branch()
        )
        base_image_tag = "latest" if repository in {"base", "cuda"} else base_image_tag
        base_image_tag = "latest" if base_image_tag == "main" else base_image_tag

        component = self.components[repository]
        cmd = [
            "docker",
            "build",
            "-f",
            component["dockerfile"],
            "--build-arg",
            f"SRC_DIRECTORY={component['src_directory']}",
            "--build-arg",
            f"BASE_IMAGE={component['base_image']}:{base_image_tag}",
            "--platform",
            f"linux/{self.arch}",
            "-t",
            f"{DOCKER_ORGANIZATION}/{repository}:{tag}",
            *cache_args,
            ".",
        ]
        if not TAG_REGEX.fullmatch(repository) or not TAG_REGEX.fullmatch(tag):
            raise ValueError("Invalid repository or tag")
        subprocess.run(cmd, check=True)


class Parser(argparse.ArgumentParser):
    """Parser for the manager.py script."""

    def __init__(self) -> None:
        """Initialize the parser."""
        super().__init__()
        self.description = "Builds or pulls one or multiple Docker images."

        self.add_argument(
            "--pull",
            required=False,
            action="store_true",
            help="Add this flag if you want to pull Docker images.",
        )

        self.add_argument(
            "--build",
            required=False,
            action="store_true",
            help="Add this flag if you want to build Docker images.",
        )

        self.add_argument(
            "--no-cache",
            required=False,
            action="store_true",
            help="Add this flag if you want to build Docker images without using the cache.",
        )

        self.add_argument(
            "-c",
            "--components",
            required=False,
            default=[],
            nargs="+",
            help="List of components to pull or build. Use the repository names as defined in components.yml.",
        )

    def run(self) -> None:
        """Run the parser."""
        args = self.parse_args()
        image_manager = ImageManager(args.no_cache)
        image_manager.select_repositories(args.components)
        image_manager.run(args.pull, args.build)
