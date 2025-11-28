#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARCH=$1

BASE_IMAGE=nvidia/cuda:12.9.1-cudnn-devel-ubuntu24.04

if [ "$ARCH" != "amd64" ] && [ "$ARCH" != "arm64" ] ; then
  echo "Invalid architecture $ARCH. Please choose either 'amd64' or 'arm64'."
  exit 1
fi

docker pull --platform linux/$ARCH $BASE_IMAGE
docker tag $BASE_IMAGE $BASE_IMAGE-$ARCH
echo "Pulled and tagged image $BASE_IMAGE-$ARCH."
