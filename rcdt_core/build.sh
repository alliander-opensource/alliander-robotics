#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARCH=$1
PACKAGE=core

export DOCKER_BUILDKIT=1

# Set Docker image tag
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
GIT_BRANCH=$(git branch --show-current)
if [ "$GIT_BRANCH" != "main" ] ; then
  IMAGE_TAG=rcdt/robotics:$PACKAGE-$ARCH-$GIT_BRANCH
else
  IMAGE_TAG=rcdt/robotics:$PACKAGE-$ARCH
fi

source $SCRIPT_DIR/../common/checks.sh $ARCH

# Build the Docker image
BASE_IMAGE=nvidia/cuda:12.9.1-cudnn-devel-ubuntu24.04-$ARCH
(
  cd $SCRIPT_DIR/.. && \
  docker build -f rcdt_$PACKAGE/rcdt_$PACKAGE.Dockerfile \
  --build-arg BASE_IMAGE=$BASE_IMAGE \
  --platform $PLATFORM \
  -t $IMAGE_TAG \
  .
  )
