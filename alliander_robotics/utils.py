# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import subprocess
import sys

import yaml


def get_git_branch() -> str:
    """Get the current git branch.

    Returns:
        str: The name of the current git branch.
    """
    return subprocess.getoutput("git rev-parse --abbrev-ref HEAD")


def get_files_changed(verbose: bool = False) -> list[str]:
    """Get the list of files changed in the current branch compared to main.

    Args:
        verbose (bool, optional): Whether to print detailed information. Defaults to False.

    Returns:
        list[str]: A list of file paths that have changed.
    """
    files = []
    files.extend(subprocess.getoutput("git diff origin/main --name-only").split())
    files.extend(
        subprocess.getoutput("git ls-files --others --exclude-standard").split()
    )

    if verbose:
        print("\nChecking for changed files:")
        print(f"{len(files)} files changed compared to the latest commit on main:")
        print(subprocess.getoutput("git log -n 1 origin/main --pretty=oneline"))
        print("\n")

    return files


def load_components(group: str = "") -> dict:
    """Loads components.yml file into a dictionary.

    Args:
        group (str, optional): The group of components to load.

    Returns:
        dict: A dictionary containing the components defined in components.yml.
    """
    with open("components.yml", encoding="utf-8") as stream:
        try:
            components: dict[str, dict] = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            print(e)
            sys.exit(1)

    match group:
        case "ubuntu_images":
            return {
                k: v
                for k, v in components.items()
                if v["base_image"] == "allianderrobotics/base"
            }
        case "cuda_images":
            return {
                k: v
                for k, v in components.items()
                if v["base_image"] == "allianderrobotics/cuda"
            }
        case _:
            return components


def get_changed_packages(verbose: bool = False) -> set[str]:
    """Get the set of changed packages in the repository.

    Args:
        verbose (bool, optional): Whether to print detailed information. Defaults to False.

    Returns:
        set[str]: A set of package names that have changed.
    """
    files = get_files_changed(verbose=verbose)
    return {file.split("/")[1] for file in files if file.startswith("alliander_robotics/alliander_")}


def is_core_docker_changed() -> bool:
    """Check if the ubuntu docker image is changed.

    Returns:
        bool: True if the core docker image is changed, False otherwise.
    """
    return "alliander_robotics/alliander_core/alliander_core.Dockerfile" in get_files_changed()


def is_core_files_changed() -> bool:
    """Check if files in the core package are changed.

    Returns:
        bool: True if files in the core package are changed, False otherwise.
    """
    return any(file.startswith("alliander_robotics/alliander_core/") for file in get_files_changed())
