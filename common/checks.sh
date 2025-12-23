#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARCH=$1

# Check the platform
if [ "$ARCH" != "amd64" ] && [ "$ARCH" != "arm64" ] ; then
  echo "Invalid architecture $ARCH. Please choose either 'amd64' or 'arm64'."
  exit 1
else
  echo "Running for architecture $ARCH."
fi

# Set platform and start QEMU if needed
if [ "$ARCH" == "amd64" ] ; then
  PLATFORM="linux/amd64"
  if [ "$(uname -p)" != "x86_64" ] ; then
    echo "ERROR: Running amd64 build on $(uname -p) device, exiting."
    exit 1
  fi
else 
  PLATFORM="linux/arm64/v8"
  if [ "$(uname -p)" == "x86_64" ] ; then
    echo "***** Setting up QEMU environment... *****"
    docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
  fi
fi
