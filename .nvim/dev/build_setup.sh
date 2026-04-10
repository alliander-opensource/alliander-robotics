#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
set +u

source /opt/ros/jazzy/setup.bash
source /alliander/ros/install/setup.bash
export PYTHONPATH="/alliander/.venv/lib/python3.12/site-packages:$PYTHONPATH"
export PATH="/alliander/.venv/bin:$PATH"

set -u
