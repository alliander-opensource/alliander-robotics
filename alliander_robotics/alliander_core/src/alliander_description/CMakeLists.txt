# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)
project(alliander_description)

# CMake dependencies:
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# Shared folders:
install(
  DIRECTORY env-hooks urdf 
  DESTINATION share/${PROJECT_NAME}
)

ament_package(CONFIG_EXTRAS "alliander_description-extras.cmake")
