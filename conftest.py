# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

"""Global pytest fixtures for ROS 2 integration testing."""

import subprocess

import pytest
from _pytest.fixtures import SubRequest

from compose import Compose


@pytest.fixture(scope="module", autouse=True)
def start_and_stop_containers(request: SubRequest):
    output_file = "/tmp/compose.yml"
    platforms = getattr(request.module, "PLATFORMS", {})
    compose = Compose(platforms)
    compose.compose_for_test(simulator=True, tools=False, output_file=output_file)
    process = subprocess.Popen([f"docker compose -f {output_file} up"], shell=True)
    yield
    subprocess.run([f"docker compose -f {output_file} down -t 1"], shell=True)
    process.wait()
    subprocess.run([f"docker compose -f {output_file} rm -fsv"], shell=True)
