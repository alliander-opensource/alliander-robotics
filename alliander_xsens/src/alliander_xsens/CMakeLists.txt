# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)
project(alliander_xsens)

# CMake dependencies:
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)

# C++ executables:
include_directories(include)
add_executable(imu_bridge_node 
  src/main.cpp
  src/imu_bridge.cpp
)
ament_target_dependencies(imu_bridge_node
  rclcpp
  geometry_msgs
  sensor_msgs
)
install(
  TARGETS imu_bridge_node
  DESTINATION lib/${PROJECT_NAME}
)

# Shared folders:
install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

# Default test:
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
