# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import contextlib
import subprocess
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spin up the docker containers.")

    parser.add_argument(
        "platforms",
        nargs="+",
        help="List of platform components to include (e.g. panther franka) in a platforms.yaml compose file.",
    )

    parser.add_argument(
        "-d",
        required=False,
        action="store_true",
        help="Run containers in detached mode.",
    )

    args = parser.parse_args()

    if len(args.platforms) != 1:
        print("Error: Exactly one platform must be specified.")
        sys.exit(1)
    platform = args.platforms[0]

    # Create platforms compose file:
    cmd = [f"python3 compose.py --arch amd64 --platforms {platform} --dev"]
    subprocess.run(cmd, shell=True, check=True)

    # Create simulator compose file:
    cmd = [f"python3 compose.py --arch amd64 --platforms {platform} --simulator --dev"]
    subprocess.run(cmd, shell=True, check=True)

    # Spin up containers:
    cmd = "docker compose -f platforms.yml -f simulator.yml up"
    if args.d:
        cmd += " -d"

    with contextlib.suppress(KeyboardInterrupt):
        subprocess.run([cmd], shell=True, check=False)
