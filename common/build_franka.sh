#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARCH=$1
PACKAGE=franka
BASE_PACKAGE=core

./build.sh $ARCH $PACKAGE $BASE_PACKAGE
