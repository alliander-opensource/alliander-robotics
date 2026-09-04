# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)
project(alliander_isaac)

# CMake dependencies:
find_package(ament_cmake REQUIRED)

# Other dependencies:
find_package(rclcpp REQUIRED)
find_package(isaac_ros_apriltag_interfaces REQUIRED)

# Shared folders:
install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

# Apriltag Manager:
add_executable(apriltag_manager
  src/apriltag_manager.cpp)
ament_target_dependencies(apriltag_manager
  rclcpp
  isaac_ros_apriltag_interfaces
)

install(
  TARGETS apriltag_manager
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
