# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)
project(alliander_husarion)

# CMake dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# ROS 2 dependencies
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)

# Fallback velocity node
add_executable(fallback_velocity src/fallback_velocity.cpp)
ament_target_dependencies(fallback_velocity rclcpp geometry_msgs)

install(
  TARGETS fallback_velocity
  DESTINATION lib/${PROJECT_NAME}
)

# Shared folders
install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
