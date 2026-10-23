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
find_package(geographic_msgs REQUIRED)
find_package(diagnostic_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(robot_localization REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(GEOGRAPHICLIB REQUIRED IMPORTED_TARGET geographiclib)

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

# bt_is_system_healthy_node
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

# georeferencing_node
add_executable(georeferencing_node src/georeferencing.cpp)
ament_target_dependencies(georeferencing_node
  rclcpp
  geographic_msgs
  sensor_msgs
  geometry_msgs
  nav_msgs
  robot_localization
  tf2
  tf2_geometry_msgs
  tf2_ros
  std_srvs)
target_link_libraries(georeferencing_node PkgConfig::GEOGRAPHICLIB)
install(TARGETS georeferencing_node DESTINATION lib/${PROJECT_NAME})

ament_package()
