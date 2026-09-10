# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)
project(alliander_nav2)

# CMake dependencies:
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(nav2_behavior_tree REQUIRED)
find_package(nav2_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(diagnostic_msgs REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(robot_localization REQUIRED)

add_library(bt_is_system_healthy_node SHARED
  src/diagnostics_health_check.cpp
)

# Python executables:
install(
  DIRECTORY src_py/
  DESTINATION lib/${PROJECT_NAME}
)

# Shared folders:
install(
  DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

# Docking plugin:
include_directories(include)
find_package(nav2_util REQUIRED)
find_package(opennav_docking_core REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(pluginlib REQUIRED)
add_library(simple_charging_dock SHARED
  src/dock_plugin.cpp
)
ament_target_dependencies(simple_charging_dock
  nav2_util
  opennav_docking_core
  sensor_msgs
  geometry_msgs
  pluginlib
)

pluginlib_export_plugin_description_file(opennav_docking_core plugins.xml)

install(TARGETS simple_charging_dock
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

ament_target_dependencies(bt_is_system_healthy_node
  rclcpp
  nav2_behavior_tree
  diagnostic_msgs
)

target_compile_definitions(bt_is_system_healthy_node PRIVATE BT_PLUGIN_EXPORT)

install(TARGETS bt_is_system_healthy_node
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

add_executable(initialize_odometry_node src/initialize_global_odometry.cpp)
ament_target_dependencies(initialize_odometry_node rclcpp sensor_msgs robot_localization std_srvs)

install(TARGETS initialize_odometry_node DESTINATION lib/${PROJECT_NAME})

ament_package()
