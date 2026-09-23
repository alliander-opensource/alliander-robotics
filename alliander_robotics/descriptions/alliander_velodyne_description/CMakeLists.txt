# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)
project(alliander_velodyne_description)


# CMake dependencies:
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(alliander_description REQUIRED)

# Shared folders:
install(
  DIRECTORY urdf 
  DESTINATION share/${PROJECT_NAME}
)

ament_environment_hooks(
  "${alliander_description_GZ_SIM_RESOURCE_PATH_HOOK}"
)
ament_package()
