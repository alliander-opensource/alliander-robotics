# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import contextlib
import subprocess

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spin up the docker containers.")

    parser.add_argument(
        "configuration",
        help="Configuration name to launch.",
    )

    parser.add_argument(
        "-d",
        required=False,
        action="store_true",
        help="Run containers in detached mode.",
    )

    args = parser.parse_args()

    # Create platforms compose file:
    cmd = [f"python3 compose.py --arch amd64 -c {args.configuration} --dev"]
    subprocess.run(cmd, shell=True, check=True)

    # Create simulator compose file:
    cmd = [f"python3 compose.py --arch amd64 -c {args.configuration} --simulator --dev"]
    subprocess.run(cmd, shell=True, check=True)

    # Create tools compose file:
    cmd = [f"python3 compose.py --arch amd64 -c {args.configuration} --tools --dev"]
    subprocess.run(cmd, shell=True, check=True)

    # Spin up containers:
    cmd = "docker compose -f platforms.yml -f simulator.yml -f tools.yml up"
    if args.d:
        cmd += " -d"

    with contextlib.suppress(KeyboardInterrupt):
        subprocess.run([cmd], shell=True, check=False)
