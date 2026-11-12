# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.16)
project(alliander_behavior)

# Core package dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(behaviortree_cpp REQUIRED)
find_package(behaviortree_ros2 REQUIRED)
find_package(btcpp_ros2_interfaces REQUIRED)

# Behavior domain-specific dependencies
find_package(alliander_interfaces REQUIRED)
find_package(geographic_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav2_msgs REQUIRED)
find_package(robot_localization REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(std_srvs REQUIRED)

# Define behaviors per domain.
# This ensures that a BTree that doesn't need navigation
# doesn't depend on navigation deps.
set(COMMON_DEPS behaviortree_ros2 alliander_interfaces std_msgs std_srvs)
set(NAVIGATION_DEPS behaviortree_ros2 geographic_msgs geometry_msgs nav2_msgs robot_localization)
set(POWER_DEPS behaviortree_ros2 sensor_msgs)

# Build one BehaviorTree.CPP plugin library per domain
foreach(domain common navigation power)
  string(TOUPPER ${domain} DOMAIN)

  # Interface target, header-only
  set(target ${PROJECT_NAME}_${domain}_nodes)
  add_library(${target} INTERFACE)
  target_include_directories(${target} INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>)

  # Propagate the domain-specific dependencies
  ament_target_dependencies(${target} INTERFACE ${${DOMAIN}_DEPS})
  list(APPEND NODE_TARGETS ${target})

  # Build plugin as a shared library so BehaviorTree.CPP can
  # register them at runtime.
  set(plugin ${PROJECT_NAME}_${domain}_plugin)
  add_library(${plugin} SHARED src/plugins/${domain}.cpp)
  target_compile_definitions(${plugin} PRIVATE BT_PLUGIN_EXPORT)
  target_link_libraries(${plugin} PRIVATE ${target})

  # Keep plugins grouped by domain so they can be loaded independently
  install(TARGETS ${plugin}
    LIBRARY DESTINATION share/${PROJECT_NAME}/bt_plugins/${domain})
endforeach()

# Reusable generic BTree executor.
# Anything behavior-specific remain in the plugin libraries
add_library(${PROJECT_NAME}_executor STATIC src/behavior_executor.cpp)
target_include_directories(${PROJECT_NAME}_executor PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
ament_target_dependencies(${PROJECT_NAME}_executor PUBLIC
  rclcpp rclcpp_action behaviortree_cpp behaviortree_ros2 btcpp_ros2_interfaces)

# Executable main, using library above
add_executable(behavior_executor src/behavior_executor_main.cpp)
target_link_libraries(behavior_executor PRIVATE ${PROJECT_NAME}_executor)

# Install public headers and library targets
install(DIRECTORY include/ DESTINATION include)
install(
  TARGETS ${NODE_TARGETS} ${PROJECT_NAME}_executor
  EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)

# ROS2 executable installed in lib/
install(TARGETS behavior_executor DESTINATION lib/${PROJECT_NAME})

# Share directories for BT XMLs, YAML config per BT, and launch
install(
  DIRECTORY behavior_trees config launch
  DESTINATION share/${PROJECT_NAME})

# This allows another package to use find(alliander_behavior REQUIRED)
ament_export_targets(export_${PROJECT_NAME} HAS_LIBRARY_TARGET)

# This tells another package what other dependencies are needed
ament_export_dependencies(
  rclcpp rclcpp_action behaviortree_cpp behaviortree_ros2 btcpp_ros2_interfaces
  alliander_interfaces geographic_msgs geometry_msgs nav2_msgs
  robot_localization sensor_msgs std_msgs std_srvs)

ament_package()
