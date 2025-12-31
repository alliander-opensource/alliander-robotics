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
        nargs="?",
        help="Configuration name to launch.",
    )

    parser.add_argument(
        "--pytest",
        action="store_true",
        help="Create the test container compose and start pytest inside it.",
    )

    parser.add_argument(
        "--linting",
        action="store_true",
        help="Create the test container compose and start pytest inside it.",
    )

    parser.add_argument(
        "-d",
        required=False,
        action="store_true",
        help="Run containers in detached mode.",
    )

    args = parser.parse_args()

    # Create compose file:
    if args.pytest:
        cmd = ["python3 compose.py --arch amd64 --pytest"]
    elif args.linting:
        cmd = ["python3 compose.py --arch amd64 --linting"]
    else:
        cmd = [
            f"python3 compose.py --arch amd64 -c {args.configuration} --simulator --tools --dev"
        ]
    subprocess.run(cmd, shell=True, check=True)

    # Spin up containers:
    cmd = "docker compose -f compose.yml up"
    if args.d:
        cmd += " -d"

    with contextlib.suppress(KeyboardInterrupt):
        subprocess.run([cmd], shell=True, check=False)

    # Stop containers:
    cmd = ["docker compose -f compose.yml down -t 1"]
    subprocess.run(cmd, shell=True, check=True)

    # Stop containers started for pytest:
    if args.pytest:
        cmd = ["docker compose -f rcdt_tests/compose.yml down -t 1"]
        subprocess.run(cmd, shell=True, check=True)
        cmd = ["docker compose -f rcdt_tests/compose.yml rm -fsv"]
        subprocess.run(cmd, shell=True, check=True)
