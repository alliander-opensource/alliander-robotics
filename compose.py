import argparse
import os
from pathlib import Path
import subprocess
import sys
import yaml


dev_settings = {
    'volumes': [
        '${HOME}/.vscode-server:/root/.vscode-server',
        './.personal.bashrc:/root/.personal.bashrc',
        '${HOME}/.nix-profile/bin/nvim:/usr/bin/nvim',
        '/nix/store:/nix/store',
        './.env:/rcdt/.env',
        './pyproject.toml:/rcdt/pyproject.toml',
        './.config:/rcdt/.config',
        './clangd:/rcdt/clangd',
    ],
}


def get_src_mounts(package: str) -> list[str]:
    cwd = Path.cwd()
    src_dir = cwd.joinpath(f"{package}", 'src')
    return [f"./{str(p.relative_to(cwd))}:/rcdt/ros/src/{p.name}" for p in src_dir.iterdir() if p.is_dir()] 


def get_image_tag():
    try:
        branch_name = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            universal_newlines=True,
            stderr=subprocess.PIPE
        ).strip()
    except subprocess.CalledProcessError:
        print("Warning: not in a Git repository. Defaulting to 'latest'.")
        return "latest"
    except FileNotFoundError:
        print("Warning: 'git' command not found. Defaulting to 'latest'.")
        return "latest"
    
    if branch_name == 'main':
        return 'latest'
    return branch_name


def compose_and_write(arch: str, platforms: list, dev: bool = False, output_file: str = "platforms.yml"):
    print("----- CREATING PLATFORMS.YML COMPOSE -----")
    merged_compose = {}
    image_tag = get_image_tag()

    print(f"Image tag: {image_tag}")
    print(f"Dev mode: {dev}")

    for platform in platforms:
        filename = f"rcdt_{platform}/docker-compose.yml"

        if not os.path.exists(filename):
            print(f"Warning: file {filename} not found. Skipping.")
            continue

        print(f"Merging {filename}")

        with open(filename, 'r') as f:
            content = yaml.safe_load(f)

            if not content:
                continue

            if 'services' in content:
                if 'services' not in merged_compose:
                    merged_compose['services'] = {}
                merged_compose['services'].update(content['services'])

            for key, value in content.items():
                if key != 'services' and key not in merged_compose:
                    merged_compose[key] = value

    if not merged_compose:
        print("Error: no compose files were merged. Aborting.")
        return
    
    # Replace image tag
    if 'services' in merged_compose:
        for service_name, service_config in merged_compose['services'].items():
            if 'image' in service_config and '${IMAGE_TAG}' in service_config['image']:
                original_image = service_config['image']
                service_config['image'] = original_image.replace('${IMAGE_TAG}', f"{arch}-{image_tag}")
            if dev:
                src_mounts = get_src_mounts(service_name)
                service_config['volumes'] = service_config['volumes'] + dev_settings['volumes'] + src_mounts


    print(f"\nWriting final compose file to {output_file}")

    with open(output_file, 'w') as f:
        yaml.safe_dump(merged_compose, f, default_flow_style=False, sort_keys=False)

    print("Done!")


def compose_simulator(arch: str, platforms: list[str], dev: bool = False, output_file: str = "simulator.yml"):
    print("----- CREATING SIMULATOR.YML COMPOSE -----")
    filename = "rcdt_gazebo/docker-compose.yml"

    if not os.path.exists(filename):
        print("Warning: did not find docker-compose.yml file in rcdt_gazebo. Exiting...")
        sys.exit(1)

    with open(filename, 'r') as f:
        content = yaml.safe_load(f)
        service = content['services']['rcdt_gazebo']

        image_tag = get_image_tag()
        print(f"Image tag: {image_tag}")
        
        original_image = service['image']
        service['image'] = original_image.replace('${IMAGE_TAG}', f"{arch}-{image_tag}")

        service['environment'].append(f"PLATFORMS={",".join(platforms)}")

        if dev:
            src_mounts = get_src_mounts('rcdt_gazebo')
            service['volumes'] = service['volumes'] + dev_settings['volumes'] + src_mounts

        print(f"\nWriting final compose file to {output_file}")

        with open(output_file, 'w') as f:
            yaml.safe_dump(content, f, default_flow_style=False, sort_keys=False)


def compose_tools(arch: str, platforms: list[str], dev: bool = False, output_file: str = "tools.yml"):
    print("----- CREATING TOOLS.YML COMPOSE -----")
    filename = "rcdt_tools/docker-compose.yml"

    if not os.path.exists(filename):
        print("Warning: did not find docker-compose.yml file in rcdt_tools. Exiting...")
        sys.exit(1)

    with open(filename, 'r') as f:
        content = yaml.safe_load(f)
        service = content['services']['rcdt_tools']

        image_tag = get_image_tag()
        print(f"Image tag: {image_tag}")

        original_image = service['image']
        service['image'] = original_image.replace('${IMAGE_TAG}', f"{arch}-{image_tag}")

        service['environment'].append(f"PLATFORMS={",".join(platforms)}")

        if dev:
            src_mounts = get_src_mounts('rcdt_tools')
            service['volumes'] = service['volumes'] + dev_settings['volumes'] + src_mounts

        print(f"\nWriting final compose file to {output_file}")

        with open(output_file, 'w') as f:
            yaml.safe_dump(content, f, default_flow_style=False, sort_keys=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Creates a combined docker-compose.yml file from platform-specific composes.")

    parser.add_argument('--arch', required=True, choices=['amd64', 'arm64'], help="Target architecture (amd64 or arm64).")

    parser.add_argument('--platforms', required=True, nargs='+', help="List of platform components to include (e.g. panther franka) in a platforms.yaml compose file.")

    parser.add_argument('--simulator', required=False, action='store_true', help="Add this flag to build a simulator.yml compose file, indicating which platforms are present in the simulation with the '--platforms' tag.") 

    parser.add_argument('--tools', required=False, action='store_true', help="Add this flag to build a tools.yml compose file, indicating which platforms are present in Rviz / Vizanti with the '--platforms' tag.") 

    parser.add_argument('--dev', required=False, action='store_true', help="Add this flag to enable dev mode, where repo folders are mounted into the container.")

    args = parser.parse_args()

    if args.simulator:
        compose_simulator(args.arch, args.platforms, args.dev)
    if args.tools:
        compose_tools(args.arch, args.platforms, args.dev)
    if not args.simulator and not args.tools:
        compose_and_write(args.arch, args.platforms, args.dev)
