# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.16)
project(alliander_behavior)

# CMake dependencies:
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(behaviortree_cpp REQUIRED)
find_package(behaviortree_ros2 REQUIRED)
find_package(btcpp_ros2_interfaces REQUIRED)

find_package(alliander_interfaces REQUIRED)
find_package(geographic_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav2_msgs REQUIRED)
find_package(robot_localization REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(std_srvs REQUIRED)

# Define dependencies per behavior type
set(COMMON_DEPS behaviortree_ros2 alliander_interfaces std_msgs std_srvs)
set(NAVIGATION_DEPS behaviortree_ros2 geographic_msgs geometry_msgs nav2_msgs robot_localization)
set(POWER_DEPS behaviortree_ros2 sensor_msgs)

# Install each behavior type as a library
foreach(domain common navigation power)
  string(TOUPPER ${domain} DOMAIN)
  set(target ${PROJECT_NAME}_${domain}_nodes)
  add_library(${target} INTERFACE)
  target_include_directories(${target} INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>)
  ament_target_dependencies(${target} INTERFACE ${${DOMAIN}_DEPS})
  list(APPEND NODE_TARGETS ${target})

  set(plugin ${PROJECT_NAME}_${domain}_plugin)
  add_library(${plugin} SHARED src/plugins/${domain}.cpp)
  target_compile_definitions(${plugin} PRIVATE BT_PLUGIN_EXPORT)
  target_link_libraries(${plugin} PRIVATE ${target})
  install(TARGETS ${plugin}
    LIBRARY DESTINATION share/${PROJECT_NAME}/bt_plugins/${domain})
endforeach()

add_library(${PROJECT_NAME}_executor STATIC src/behavior_executor.cpp)
target_include_directories(${PROJECT_NAME}_executor PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
ament_target_dependencies(${PROJECT_NAME}_executor PUBLIC
  rclcpp rclcpp_action behaviortree_cpp behaviortree_ros2 btcpp_ros2_interfaces)

add_executable(behavior_executor src/behavior_executor_main.cpp)
target_link_libraries(behavior_executor PRIVATE ${PROJECT_NAME}_executor)

install(DIRECTORY include/ DESTINATION include)

install(
  TARGETS ${NODE_TARGETS} ${PROJECT_NAME}_executor
  EXPORT export_${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)

install(TARGETS behavior_executor DESTINATION lib/${PROJECT_NAME})

install(
  DIRECTORY behavior_trees config launch
  DESTINATION share/${PROJECT_NAME})

ament_export_targets(export_${PROJECT_NAME} HAS_LIBRARY_TARGET)
ament_export_dependencies(
  rclcpp rclcpp_action behaviortree_cpp behaviortree_ros2 btcpp_ros2_interfaces
  alliander_interfaces geographic_msgs geometry_msgs nav2_msgs
  robot_localization sensor_msgs std_msgs std_srvs)

ament_package()
