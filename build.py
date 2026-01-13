# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import argparse
import subprocess
import sys

import yaml


class Builder:
    """Class to build Docker images."""

    def __init__(self, arch: str, no_cache: bool = False) -> None:
        """Initializes Builder class.

        Args:
            arch (str): architecture for which to build [amd64/arm64].
            no_cache (bool): whether to use the cache when building. no_cache defaults to False.
        """
        self.arch = arch
        self.no_cache = no_cache

    @staticmethod
    def load_yaml() -> dict:
        """Loads components.yml file into a dictionary.

        Returns:
            dictionary containing all available components, or an empty dictionary if a YAMLError is raised.
        """
        with open("components.yml", encoding="utf-8") as stream:
            try:
                data = yaml.safe_load(stream)
                return data
            except yaml.YAMLError as e:
                print(e)
                return {}

    def run_build_subprocess(self, base_image: str, tag: str, dockerfile: str) -> None:
        """Runs a docker build command to build a specific rcdt/robotics image.

        Args:
            base_image (str): docker image to use as base image for this build.
            tag (str): tag to give to resulting image.
            dockerfile (str): location of Dockerfile, relative to rcdt_robotics repo root.
        """
        print(f"\n\n\n---------- Building rcdt/robotics:{tag} ----------")

        cache_str = ""
        if self.no_cache:
            cache_str = "--no-cache"

        cmd = f"docker build \
            -f {dockerfile} \
            --build-arg BASE_IMAGE={base_image}-{self.arch} \
            --platform linux/{self.arch} \
            -t rcdt/robotics:{tag}-{self.arch} {cache_str} \
            ."
        subprocess.run(cmd, shell=True, check=True)

    def build_component(self, name: str, components: dict) -> None:
        """Builds a Docker image for a single component.

        Args:
            name (str): name of component, corresponding to a key in components.yml, to build.
            components (dict): key-value store of all components that can be built.
        """
        components = components["base"] | components["cuda"]
        if name not in components:
            print(f"Component {name} not found in components.yml.")
            sys.exit(1)
        else:
            self.run_build_subprocess(
                components[name]["base_image"],
                components[name]["tag"],
                components[name]["dockerfile"],
            )

    def build_multiple(self, components: list[str]) -> None:
        """Builds multiple Docker images, based on a list of components.

        Args:
            components (list): list of components, corresponding to keys in components.yml, to build.
        """
        all_components = self.load_yaml()
        for c in components:
            self.build_component(c, all_components)

    def build_all(self) -> None:
        """Builds all components in components.yml."""
        all_components = self.load_yaml()
        for c in all_components:
            self.build_component(c, all_components)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Builds one or multiple Docker images."
    )

    parser.add_argument(
        "--arch",
        required=True,
        choices=["amd64", "arm64"],
        default="amd64",
        help="Target architecture (amd64 or arm64).",
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
        nargs="+",
        help="List of components to build. Components should have the same name as defined in components.yml or the rcdt_* subdirectories in the repository's root.",
    )

    parser.add_argument(
        "--all",
        required=False,
        action="store_true",
        help="Add this flag to build all components listed in components.yml",
    )

    args = parser.parse_args()

    builder = Builder(args.arch, args.no_cache)
    if args.all:
        builder.build_all()
    elif args.components:
        builder.build_multiple(args.components)
    else:
        print(
            "No components selected. Please provide either components with the -c/--components flag, or specify to build all images with the --all flag."
        )
