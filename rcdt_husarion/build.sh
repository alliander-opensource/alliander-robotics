#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARCH=$1
PACKAGE=husarion
BASE_PACKAGE=core

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
cd $SCRIPT_DIR/../common/ && ./build.sh $ARCH $PACKAGE $BASE_PACKAGE && cd $SCRIPT_DIR
