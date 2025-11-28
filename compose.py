import argparse
import os
from pathlib import Path
import subprocess
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


def compose_and_write(arch: str, platforms: list, dev: bool = False, output_file: str = "docker-compose.yml"):
    merged_compose = {}
    image_tag = get_image_tag()

    print(f"--- Using image tag {image_tag} ---")
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Creates a combined docker-compose.yml file from platform-specific composes.")

    parser.add_argument('--arch', required=True, choices=['amd64', 'arm64'], help="Target architecture (amd64 or arm64).")

    parser.add_argument('--platforms', required=True, nargs='+', help="List of platform components to include (e.g. husarion franka simulation). Names need to match with the rcdt_ directories in the repository root.")

    parser.add_argument('--dev', required=False, action='store_true', help="Add this flag to enable dev mode, where repo folders are mounted into the container.")

    args = parser.parse_args()

    compose_and_write(args.arch, args.platforms, args.dev)
