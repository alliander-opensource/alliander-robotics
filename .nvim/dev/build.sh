#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
set -e

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
echo $SCRIPT_DIR

docker build \
  --platform linux/amd64 \
  -f $SCRIPT_DIR../../../.devcontainer/dev/Dockerfile \
  -t allianderrobotics/dev \
  $SCRIPT_DIR/../../
