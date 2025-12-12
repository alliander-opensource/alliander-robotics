import argparse
import os
import subprocess
import sys
from pathlib import Path

import yaml

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
    ],
}


def get_src_mounts(package: str) -> list[str]:
    cwd = Path.cwd()
    src_dir = cwd.joinpath(f"{package}", "src")
    return [
        f"./{str(p.relative_to(cwd))}:/rcdt/ros/src/{p.name}"
        for p in src_dir.iterdir()
        if p.is_dir()
    ]


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


def replace_env_var(content: dict, var: str, value: str):
    """
    Iterate through all platforms' environment variables, and replace var with var=value.
    The value has to be a string because that is how it is stored in docker-compose.yml files.
    """
    for service in content["services"]:
        environment = content["services"][service]["environment"]
        indices = [idx for idx, s in enumerate(environment) if var in s]
        if len(indices) < 1:
            print(
                f"[{service.upper()}] Could not find variable {var} in environment variables {environment}"
            )
            continue
        if len(indices) > 1:
            print(
                f"Found {len(indices)} variables named {var} in environment variables {environment}. This should be only one."
            )
            continue

        idx = indices[0]
        environment[idx] = f"{var}={value}"


def create_couplings(content: dict, platforms: list[str]) -> dict:
    """
    This function is responsible for updating environment variables based on which platforms are being launched.
    For example, if gps is part of the platforms, USE_GPS should be True. Otherwise, it should be False.
    """
    replace_env_var(
        content,
        "PLATFORMS",
        ",".join(
            [p for p in platforms if p in ["panther", "lynx", "franka", "ouster"]]
        ),
    )
    if "gps" in platforms:
        replace_env_var(content, "USE_GPS", "true")
    else:
        replace_env_var(content, "USE_GPS", "false")
    if "nav2" in platforms:
        vehicle_type = ""
        if "panther" in platforms:
            vehicle_type = "panther"
        elif "lynx" in platforms:
            vehicle_type = "lynx"
        replace_env_var(content, "NAMESPACE_VEHICLE", vehicle_type)
    return content


def compose_platforms(
    arch: str, platforms: list, dev: bool = False, output_file: str = "platforms.yml"
):
    print("----- CREATING PLATFORMS.YML COMPOSE -----")
    merged_compose = {}
    image_tag = get_image_tag()

    print(f"Image tag: {image_tag}")
    print(f"Dev mode: {dev}")

    for platform in platforms:
        if platform in ["panther", "lynx"]:
            filename = "rcdt_husarion/docker-compose.yml"
        else:
            filename = f"rcdt_{platform}/docker-compose.yml"

        if not os.path.exists(filename):
            print(f"Warning: file {filename} not found. Skipping.")
            continue

        print(f"Merging {filename}")

        with open(filename, "r") as f:
            content = yaml.safe_load(f)

            if not content:
                continue

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
            if "image" in service_config and "${IMAGE_TAG}" in service_config["image"]:
                original_image = service_config["image"]
                service_config["image"] = original_image.replace(
                    "${IMAGE_TAG}", f"{arch}-{image_tag}"
                )
            if dev:
                src_mounts = get_src_mounts(service_name)
                service_config["volumes"] = (
                    service_config["volumes"] + dev_settings["volumes"] + src_mounts
                )
    create_couplings(merged_compose, platforms)

    print(f"\nWriting final compose file to {output_file}")

    with open(output_file, "w") as f:
        yaml.safe_dump(merged_compose, f, default_flow_style=False, sort_keys=False)

    print("Done!")


def compose_simulator(
    arch: str,
    platforms: list[str],
    dev: bool = False,
    output_file: str = "simulator.yml",
):
    print("----- CREATING SIMULATOR.YML COMPOSE -----")
    filename = "rcdt_gazebo/docker-compose.yml"

    if not os.path.exists(filename):
        print(
            "Warning: did not find docker-compose.yml file in rcdt_gazebo. Exiting..."
        )
        sys.exit(1)

    with open(filename, "r") as f:
        content = yaml.safe_load(f)
        service = content["services"]["rcdt_gazebo"]

        image_tag = get_image_tag()
        print(f"Image tag: {image_tag}")

        original_image = service["image"]
        service["image"] = original_image.replace("${IMAGE_TAG}", f"{arch}-{image_tag}")

        service["environment"].append(f"PLATFORMS={','.join(platforms)}")
        service["environment"].append(
            "BRIDGE_TOPICS=/ouster/scan/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked"
        )

        if dev:
            src_mounts_gazebo = get_src_mounts("rcdt_gazebo")
            src_mounts_husarion = get_src_mounts("rcdt_husarion")
            service["volumes"] = (
                service["volumes"]
                + dev_settings["volumes"]
                + src_mounts_gazebo
                + src_mounts_husarion
            )

        create_couplings(content, platforms)

        print(f"\nWriting final compose file to {output_file}")

        with open(output_file, "w") as f:
            yaml.safe_dump(content, f, default_flow_style=False, sort_keys=False)


def compose_tools(
    arch: str, platforms: list[str], dev: bool = False, output_file: str = "tools.yml"
):
    print("----- CREATING TOOLS.YML COMPOSE -----")
    filename = "rcdt_tools/docker-compose.yml"

    if not os.path.exists(filename):
        print("Warning: did not find docker-compose.yml file in rcdt_tools. Exiting...")
        sys.exit(1)

    with open(filename, "r") as f:
        content = yaml.safe_load(f)
        service = content["services"]["rcdt_tools"]

        image_tag = get_image_tag()
        print(f"Image tag: {image_tag}")

        original_image = service["image"]
        service["image"] = original_image.replace("${IMAGE_TAG}", f"{arch}-{image_tag}")

        service["environment"].append(f"PLATFORMS={','.join(platforms)}")

        if dev:
            src_mounts = get_src_mounts("rcdt_tools")
            service["volumes"] = (
                service["volumes"] + dev_settings["volumes"] + src_mounts
            )

        create_couplings(content, platforms)

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
        required=True,
        choices=["amd64", "arm64"],
        help="Target architecture (amd64 or arm64).",
    )

    parser.add_argument(
        "--platforms",
        required=True,
        nargs="+",
        help="List of platform components to include (e.g. panther franka) in a platforms.yaml compose file.",
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

    if "husarion" in args.platforms:
        print("ERROR: instead of 'husarion', please specify 'panther' or 'lynx'.")
        sys.exit(1)

    if args.simulator:
        compose_simulator(args.arch, args.platforms, args.dev)
    if args.tools:
        compose_tools(args.arch, args.platforms, args.dev)
    if not args.simulator and not args.tools:
        compose_platforms(args.arch, args.platforms, args.dev)
