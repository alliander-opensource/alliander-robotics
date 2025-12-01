#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARCH=$1
TYPE=$2

if [ "$TYPE" == "base" ] ; then
  PACKAGE=base
  BASE_IMAGE=ubuntu:noble
  IMAGE_BASE_TAG=rcdt/robotics:base
elif [ "$TYPE" == "cuda" ] ; then
  PACKAGE=cuda
  BASE_IMAGE=nvidia/cuda:12.9.1-cudnn-devel-ubuntu24.04
  IMAGE_BASE_TAG=rcdt/robotics:cuda
else 
  echo "Invalid build type '$TYPE'. Please choose either 'base' or 'cuda."
  exit 1
fi

export DOCKER_BUILDKIT=1

# Set Docker image tag
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
GIT_BRANCH=$(git branch --show-current)
if [ "$GIT_BRANCH" != "main" ] ; then
  IMAGE_TAG=$IMAGE_BASE_TAG-$ARCH-$GIT_BRANCH
else
  IMAGE_TAG=$IMAGE_BASE_TAG-$ARCH
fi

source $SCRIPT_DIR/../common/checks.sh $ARCH

# Build the Docker image
BASE_IMAGE=$BASE_IMAGE-$ARCH
(
  cd $SCRIPT_DIR/.. && \
  docker build -f rcdt_core/rcdt_core.Dockerfile \
  --build-arg BASE_IMAGE=$BASE_IMAGE \
  --platform $PLATFORM \
  -t $IMAGE_TAG \
  .
  )
