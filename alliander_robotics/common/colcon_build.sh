#!/bin/bash -i

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

# Since this script is interactive, the .bashrc is sourced automatically!

set -e

# Define arguments based on building internal or external packages:
COLCON_ARGS=()
CMAKE_ARGS=()
if [ "$1" = "--external" ]; then
  echo "Building external packages. Do not build tests."
  CMAKE_ARGS+=(-DBUILD_TESTING=OFF)
else
  echo "Building internal packages. Enabling symlink to support direct changes."
  COLCON_ARGS+=(--symlink-install)
fi

# Build the packages:
colcon build "${COLCON_ARGS[@]}" --cmake-args -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=1 "${CMAKE_ARGS[@]}"

# Run tests if we are building internal packages. If any test fails, print the test results:
if [ "$1" != "--external" ]; then
  colcon test --ctest-args tests --return-code-on-test-failure || colcon test-result --all --verbose
fi

# Run clang-tidy checks, which will also produce warnings in /opt/ros/jazzy/src/gtest_vendor/...
echo "Running clang-tidy"
clang_tidy_output=$(run-clang-tidy -p=build/ -header-filter=src/ src/alliander_* 2>&1) || true
echo "$clang_tidy_output"

# Only exit with failure code if our own code has warnings
if echo "$clang_tidy_output" | grep -qP "src/.*warning:"; then
  echo "clang-tidy found warnings, failing..."
  exit 1
fi

echo "source $(pwd)/install/setup.bash" >> /root/.bashrc
