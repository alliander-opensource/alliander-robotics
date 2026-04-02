#!/bin/bash -i

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

# Since this script is interactive, the .bashrc is sourced automatically!

set -e

colcon build --symlink-install \
  --cmake-args -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=1

# run clang-tidy checks, which will also produce warnings in /opt/ros/jazzy/src/gtest_vendor/...
echo "Running clang-tidy"
clang_tidy_output=$(run-clang-tidy -p=build/ -header-filter=src/ src/alliander_* 2>&1) || true
echo "$clang_tidy_output"

# only exit with failure code if our own code has warnings
if echo "$clang_tidy_output" | grep -qP "src/.*warning:"; then
  echo "clang-tidy found warnings, failing..."
  exit 1
fi

echo "source $(pwd)/install/setup.bash" >> /root/.bashrc
