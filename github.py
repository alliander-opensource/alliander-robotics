# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import argparse
import os
import sys

import requests

import utils


def select_components(components: str) -> None:
    """Selects components to build, used in the open PR workflow.

    Args:
        components (str): the components to select, either "all" or "changed".
    """
    if components not in {"all", "changed"}:
        sys.exit("Invalid argument to select_components, expected 'all' or 'changed'.")

    ubuntu_components = set(utils.load_components("ubuntu_images").keys())
    cuda_components = set(utils.load_components("cuda_images").keys())

    changed_packages = utils.get_changed_packages()
    changed_components = {p.removeprefix("alliander_") for p in changed_packages}

    if not utils.is_core_files_changed() and components != "all":
        ubuntu_components = ubuntu_components.intersection(changed_components)
        cuda_components = cuda_components.intersection(changed_components)

    variables = [
        f"REBUILD_CORE={utils.is_core_docker_changed()}",
        f"UBUNTU_COMPONENTS={list(ubuntu_components)}",
        f"REBUILD_UBUNTU_IMAGES={bool(ubuntu_components)}",
        f"CUDA_COMPONENTS={list(cuda_components)}",
        f"REBUILD_CUDA_IMAGES={bool(cuda_components)}",
    ]

    for variable in variables:
        print(variable)
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
                print(variable, file=fh)


def remove_tags_on_docker_hub(token: str) -> None:
    """Removes tags on Docker Hub, used in the closed PR workflow.

    Args:
        token (str): the token to authenticate with the Docker Hub API.
    """
    request = requests.get("https://hub.docker.com/v2/repositories/allianderrobotics/")
    number_of_repositories = request.json()["count"]

    params = {"page_size": number_of_repositories}
    request = requests.get(
        "https://hub.docker.com/v2/repositories/allianderrobotics/", params=params
    )
    repositories = [repository["name"] for repository in request.json()["results"]]
    print(f"Repositories: {repositories}")

    successfull = True
    successfull_status_code = 204
    for repository in repositories:
        request = requests.get(
            f"https://hub.docker.com/v2/repositories/allianderrobotics/{repository}/tags/"
        )
        number_of_tags = request.json()["count"]

        params = {"page_size": number_of_tags}
        request = requests.get(
            f"https://hub.docker.com/v2/repositories/allianderrobotics/{repository}/tags/",
            params=params,
        )

        tags = [
            tag["name"]
            for tag in request.json()["results"]
            if utils.get_git_branch() in tag["name"]
        ]
        if not tags:
            continue
        print("\nRepository:", repository)
        print("Tags to remove:", tags)

        for tag in tags:
            headers = {"Accept": "application/json", "Authorization": f"JWT {token}"}
            request = requests.delete(
                f"https://hub.docker.com/v2/repositories/allianderrobotics/{repository}/tags/{tag}/",
                headers=headers,
            )
            if request.status_code == successfull_status_code:
                print(f"| Success | {request.status_code} | {tag} |")
            else:
                print(f"| Failure | {request.status_code} | {tag} |")
                successfull = False

    if not successfull:
        sys.exit("Failed to remove all tags on Docker Hub.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Builds one or multiple Docker images."
    )

    parser.add_argument(
        "--select-components",
        required=False,
        metavar="COMPONENTS",
        help="Select components for the PR workflow.",
    )

    parser.add_argument(
        "--remove-tags-on-docker-hub",
        required=False,
        metavar="TOKEN",
        help="Remmove tags on Docker Hub for the closed PR workflow.",
    )

    args = parser.parse_args()
    if args.select_components:
        select_components(args.select_components)
    elif args.remove_tags_on_docker_hub:
        remove_tags_on_docker_hub(args.remove_tags_on_docker_hub)
