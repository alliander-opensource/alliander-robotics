# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import argparse
import subprocess
import sys

import yaml
from termcolor import colored, cprint

DOCKER_ORGANIZATION = "allianderrobotics"


class ImageManager:
    """Class to pull or build Docker images."""

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

        self.components = {}
        self.load_components()
        self.selected = []

    def load_components(self) -> None:
        """Loads components.yml file into a dictionary."""
        with open("components.yml", encoding="utf-8") as stream:
            try:
                components: dict[str, dict] = yaml.safe_load(stream)
            except yaml.YAMLError as e:
                print(e)
                sys.exit(1)

        # Create flat directory combining all components with repository as key:
        for group in components.values():
            for component in group.values():
                self.components[component["repository"]] = component

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

        for repository in self.selected:
            if pull:
                self.run_pull_subprocess(repository)
            if build:
                self.run_build_subprocess(repository)

    @staticmethod
    def run_pull_subprocess(repository: str, tag: str = "latest") -> None:
        """Runs a docker pull command to pull a specific image.

        Args:
            repository (str): repository of the docker image to build.
            tag (str): tag of the docker image to pull.
        """
        cprint(
            f"\n\n\n---------- Pulling {DOCKER_ORGANIZATION}/{repository}:{tag} ----------",
            "blue",
        )

        cmd = f"docker pull {DOCKER_ORGANIZATION}/{repository}:{tag}"
        subprocess.run(cmd, shell=True, check=True)

    def run_build_subprocess(self, repository: str, tag: str = "latest") -> None:
        """Runs a docker build command to build a specific image.

        Args:
            repository (str): repository of the docker image to build.
            tag (str): tag of the docker image to build.
        """
        cprint(
            f"\n\n\n---------- Building {DOCKER_ORGANIZATION}/{repository}:{tag} ----------",
            "blue",
        )

        cache_str = ""
        if self.no_cache:
            cache_str = "--no-cache"

        cmd = f"docker build \
            -f {self.components[repository]['dockerfile']} \
            --build-arg BASE_IMAGE={self.components[repository]['base_image']} \
            --platform linux/{self.arch} \
            -t {DOCKER_ORGANIZATION}/{repository}:{tag} {cache_str} \
            ."
        subprocess.run(cmd, shell=True, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Builds one or multiple Docker images."
    )

    parser.add_argument(
        "--pull",
        required=False,
        action="store_true",
        help="Add this flag if you want to pull Docker images.",
    )

    parser.add_argument(
        "--build",
        required=False,
        action="store_true",
        help="Add this flag if you want to build Docker images.",
    )

    parser.add_argument(
        "--no-cache",
        required=False,
        action="store_true",
        help="Add this flag if you want to build Docker images without using the cache.",
    )

    parser.add_argument(
        "-c",
        "--components",
        required=False,
        default=[],
        nargs="+",
        help="List of components to pull or build. Use the repository names as defined in components.yml.",
    )

    args = parser.parse_args()

    image_manager = ImageManager(args.no_cache)
    image_manager.select_repositories(args.components)
    image_manager.run(args.pull, args.build)
