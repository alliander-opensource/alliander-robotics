#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

./rcdt_core/build.sh amd64 base
./rcdt_core/build.sh amd64 cuda

./rcdt_franka/build.sh amd64
./rcdt_gazebo/build.sh amd64
./rcdt_husarion/build.sh amd64
./rcdt_moveit/build.sh amd64
./rcdt_nav2/build.sh amd64
./rcdt_gps/build.sh amd64
./rcdt_ouster/build.sh amd64
./rcdt_realsense/build.sh amd64
./rcdt_tests/build.sh amd64
./rcdt_visualization/build.sh amd64
./rcdt_velodyne/build.sh amd64
./rcdt_zed/build.sh amd64
