# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)
project(rcdt_moveit)

# CMake dependencies:
find_package(ament_cmake REQUIRED)

# Other dependencies:
find_package(rclcpp REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(moveit_visual_tools REQUIRED)
find_package(rcdt_interfaces REQUIRED)

# C++ executables:
include_directories(include)
add_executable(moveit_manager src/moveit_manager.cpp)
ament_target_dependencies(moveit_manager
  rclcpp
  moveit_ros_planning_interface
  moveit_visual_tools
  rcdt_interfaces
)

install(
  TARGETS moveit_manager
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
