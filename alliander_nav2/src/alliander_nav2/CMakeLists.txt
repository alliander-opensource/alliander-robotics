# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)
project(alliander_nav2)

# CMake dependencies:
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(nav2_behavior_tree REQUIRED)
find_package(diagnostic_msgs REQUIRED)

add_library(bt_is_gps_healthy_node SHARED
  src/gps_health_check.cpp
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

ament_target_dependencies(bt_is_gps_healthy_node
  rclcpp
  nav2_behavior_tree
  diagnostic_msgs
)

target_compile_definitions(bt_is_gps_healthy_node PRIVATE BT_PLUGIN_EXPORT)

install(TARGETS bt_is_gps_healthy_node
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

# Default test:
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
