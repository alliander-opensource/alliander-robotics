# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)

project(rcdt_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(vision_msgs REQUIRED)

file(GLOB MSGS CONFIGURE_DEPENDS msg/*.msg*)
file(GLOB SRVS CONFIGURE_DEPENDS srv/*.srv*)
file(GLOB ACTIONS CONFIGURE_DEPENDS action/*.action*)

foreach(file IN LISTS MSGS)
  string(REPLACE "${CMAKE_CURRENT_SOURCE_DIR}/" "" file_relative ${file})
  list(APPEND MSGS_STRIPPED ${file_relative})
endforeach()

foreach(file IN LISTS SRVS)
  string(REPLACE "${CMAKE_CURRENT_SOURCE_DIR}/" "" file_relative ${file})
  list(APPEND SRVS_STRIPPED ${file_relative})
endforeach()

foreach(file IN LISTS ACTIONS)
  string(REPLACE "${CMAKE_CURRENT_SOURCE_DIR}/" "" file_relative ${file})
  list(APPEND ACTIONS_STRIPPED ${file_relative})
endforeach()

rosidl_generate_interfaces(${PROJECT_NAME}
  ${MSGS_STRIPPED}
  ${SRVS_STRIPPED}
  ${ACTIONS_STRIPPED}
  DEPENDENCIES
  std_msgs
  geometry_msgs
  sensor_msgs
  vision_msgs
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
