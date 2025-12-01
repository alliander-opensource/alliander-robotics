#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARCH=$1
PACKAGE=realsense
BASE_PACKAGE=cuda

./build.sh $ARCH $PACKAGE $BASE_PACKAGE
