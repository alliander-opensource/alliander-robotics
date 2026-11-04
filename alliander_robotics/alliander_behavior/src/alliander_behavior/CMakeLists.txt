# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)
project(alliander_behavior)

# CMake dependencies:
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)

find_package(alliander_interfaces REQUIRED)
find_package(behaviortree_cpp REQUIRED)
find_package(behaviortree_ros2 REQUIRED)
find_package(geographic_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav2_msgs REQUIRED)
find_package(robot_localization REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_srvs REQUIRED)

include_directories(include)

# Shared folders:
install(
  DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

add_executable(autonomous_navigation_node src/autonomous_navigation.cpp)
ament_target_dependencies(autonomous_navigation_node
  rclcpp
  rclcpp_action
  alliander_interfaces
  behaviortree_cpp
  behaviortree_ros2
  geographic_msgs
  geometry_msgs
  nav2_msgs
  robot_localization
  sensor_msgs
  std_srvs
)

install(TARGETS autonomous_navigation_node DESTINATION lib/${PROJECT_NAME})

ament_package()
