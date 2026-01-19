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
        "configuration",
        nargs="?",
        help="Configuration name to launch.",
    )

    parser.add_argument(
        "--hardware",
        action="store_true",
        help="Start a configuration on the hardware.",
    )

    parser.add_argument(
        "--pytest",
        default=False,
        nargs=argparse.REMAINDER,
        help="Create the test container compose and start pytest inside it.",
    )

    parser.add_argument(
        "--pytest-no-nvidia",
        default=False,
        nargs=argparse.REMAINDER,
        help="Create the test container compose, without NVIDIA runtime, and start pytest inside it.",
    )

    parser.add_argument(
        "--linting",
        action="store_true",
        help="Create the test container compose and start pytest inside it.",
    )

    parser.add_argument(
        "--documentation",
        action="store_true",
        help="Start sphinx autobuild to serve the documentation with live reloading.",
    )

    parser.add_argument(
        "-d",
        required=False,
        action="store_true",
        help="Run containers in detached mode.",
    )

    args = parser.parse_args()

    # Create compose file:
    if isinstance(args.pytest, list):
        cmd = "python3 compose.py --pytest " + " ".join(args.pytest)
    elif isinstance(args.pytest_no_nvidia, list):
        cmd = "python3 compose.py --pytest-no-nvidia " + " ".join(args.pytest_no_nvidia)
    elif args.linting:
        cmd = "python3 compose.py --linting"
    elif args.documentation:
        cmd = "python3 compose.py --documentation"
    else:
        cmd = f"python3 compose.py -c {args.configuration} --visualization --dev"
        if not args.hardware:
            cmd += " --simulator"
    subprocess.run([cmd], shell=True, check=True)

    # Spin up containers:
    cmd = "docker compose -f compose.yml up"
    if args.d:
        cmd += " -d"
    if args.linting or args.pytest or args.pytest_no_nvidia:
        cmd += " --abort-on-container-exit"

    result = subprocess.CompletedProcess([], 0)
    with contextlib.suppress(KeyboardInterrupt):
        result = subprocess.run([cmd], shell=True, check=False)

    # Stop containers:
    cmd = ["docker compose -f compose.yml down -t 1"]
    subprocess.run(cmd, shell=True, check=True)

    # Stop containers started for pytest:
    if args.pytest or args.pytest_no_nvidia:
        cmd = ["docker compose -f compose_pytest.yml down -t 1"]
        subprocess.run(cmd, shell=True, check=True)
        cmd = ["docker compose -f compose_pytest.yml rm -fsv"]
        subprocess.run(cmd, shell=True, check=True)

    sys.exit(result.returncode)
