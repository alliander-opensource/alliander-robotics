#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
source /opt/ros/jazzy/setup.bash
source /rcdt/ros/install/setup.bash

export PYTHONPATH="/rcdt/.venv/lib/python3.12/site-packages:$PYTHONPATH"
export PATH="/rcdt/.venv/bin:$PATH"

exec "$@"
