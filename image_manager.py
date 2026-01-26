# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import argparse
import subprocess
import sys

import yaml
from termcolor import colored, cprint


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
                components = yaml.safe_load(stream)
            except yaml.YAMLError as e:
                print(e)
                sys.exit(1)

        # Create flat directory combining base and cuda components with tag as key:
        for key in components:
            for component in components[key].values():
                self.components[component["tag"]] = component

    def select_tags(self, tags: list[str]) -> None:
        """Selects tags to pull or build. If no tags are provided, all tags are selected.

        Args:
            tags (list[str]): list of tags to select.
        """
        if not tags:
            self.selected = list(self.components.keys())
            return
        for tag in tags:
            if tag not in self.components:
                print(f"Tag {tag} not found in components.yml.")
                sys.exit(1)
        self.selected = tags

    def run(self, pull: bool, build: bool) -> None:
        """Pull or build the docker images for all selected tags.

        Args:
            pull (bool): whether to pull the images.
            build (bool): whether to build the images.
        """

        def colored_bool(value: bool) -> str:
            return colored(str(value), "green" if value else "red")

        print(f"pull: {colored_bool(pull)}, build: {colored_bool(build)}")
        print(f"tags: {self.selected}")

        for tag in self.selected:
            if pull:
                self.run_pull_subprocess(tag)
            if build:
                self.run_build_subprocess(tag)

    @staticmethod
    def run_pull_subprocess(tag: str) -> None:
        """Runs a docker pull command to pull a specific rcdt/robotics tag.

        Args:
            tag (str): tag of the docker image to pull.
        """
        cprint(f"\n\n\n---------- Pulling rcdt/robotics:{tag} ----------", "blue")

        cmd = f"docker pull rcdt/robotics:{tag}"
        subprocess.run(cmd, shell=True, check=True)

    def run_build_subprocess(self, tag: str) -> None:
        """Runs a docker build command to build a specific rcdt/robotics image.

        Args:
            tag (str): tag of the docker image to build.
        """
        cprint(f"\n\n\n---------- Building rcdt/robotics:{tag} ----------", "blue")

        cache_str = ""
        if self.no_cache:
            cache_str = "--no-cache"

        cmd = f"docker build \
            -f {self.components[tag]['dockerfile']} \
            --build-arg BASE_IMAGE={self.components[tag]['base_image']} \
            --platform linux/{self.arch} \
            -t rcdt/robotics:{tag} {cache_str} \
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
        help="List of components to pull or build. Use the tags as defined in components.yml.",
    )

    args = parser.parse_args()

    image_manager = ImageManager(args.no_cache)
    image_manager.select_tags(args.components)
    image_manager.run(args.pull, args.build)
