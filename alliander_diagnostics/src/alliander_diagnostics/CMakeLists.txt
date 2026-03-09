# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)
project(alliander_diagnostics)

# CMake dependencies:
find_package(ament_cmake REQUIRED)

# Other dependencies:
find_package(rclcpp REQUIRED)
find_package(diagnostic_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

# C++ executables:
include_directories(include)
add_executable(diagnostics
  src/diagnostics_node.cpp
  src/gps_diagnostics.cpp
)
target_include_directories(diagnostics PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
ament_target_dependencies(diagnostics
  diagnostic_msgs
  rclcpp
  sensor_msgs
)

install(
  TARGETS diagnostics
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
