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
find_package(nav2_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

include_directories(include)

# Shared folders:
install(
  DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

add_executable(task_planner_node src/main.cpp)
ament_target_dependencies(task_planner_node
  rclcpp
  rclcpp_action
  alliander_interfaces
  behaviortree_cpp
  behaviortree_ros2
  nav2_msgs
  sensor_msgs
)

install(TARGETS task_planner_node DESTINATION lib/${PROJECT_NAME})

ament_package()
