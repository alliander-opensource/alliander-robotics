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
        "-p",
        required=False,
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

    if isinstance(args.p, list):
        if len(args.p) > 1:
            print("Error: Only one platform can be specified.")
            sys.exit(1)
        platform = args.p[0]

        # Create platforms compose file:
        cmd = [f"python3 compose.py --arch amd64 --platforms {platform} --dev"]
        subprocess.run(cmd, shell=True, check=True)

        # Create simulator compose file:
        cmd = [
            f"python3 compose.py --arch amd64 --platforms {platform} --simulator --dev"
        ]
        subprocess.run(cmd, shell=True, check=True)

        # Create tools compose file:
        cmd = [f"python3 compose.py --arch amd64 --platforms {platform} --tools --dev"]
        subprocess.run(cmd, shell=True, check=True)

    # Spin up containers:
    cmd = "docker compose -f platforms.yml -f simulator.yml -f tools.yml up"
    if args.d:
        cmd += " -d"

    with contextlib.suppress(KeyboardInterrupt):
        subprocess.run([cmd], shell=True, check=False)
