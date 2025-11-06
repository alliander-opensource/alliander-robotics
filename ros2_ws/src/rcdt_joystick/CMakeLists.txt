# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)
project(rcdt_joystick)

# CMake dependencies:
find_package(nlohmann_json REQUIRED)
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(ament_index_cpp REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)

# C++ executables:
include_directories(include)
add_executable(joy_topic_manager 
  src/joy_topic_manager.cpp
  src/node.cpp
)
ament_target_dependencies(joy_topic_manager
  ament_index_cpp
  nlohmann_json
  rclcpp
  sensor_msgs
)

install(
  TARGETS joy_topic_manager
  DESTINATION lib/${PROJECT_NAME}
)

# Python executables:
install(
  DIRECTORY src_py/
  DESTINATION lib/${PROJECT_NAME}
)

# Shared folders:
install(
  DIRECTORY config
  DESTINATION share/${PROJECT_NAME}
)

# Default test:
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  find_package(ament_cmake_gtest REQUIRED)

  ament_lint_auto_find_test_dependencies()

  ament_add_gtest(joy_topic_manager_test
    tests/test_package.cpp
    src/joy_topic_manager.cpp
  )
  ament_target_dependencies(joy_topic_manager_test
    ament_index_cpp
    nlohmann_json
    rclcpp
    sensor_msgs
  )
  target_compile_definitions(joy_topic_manager_test 
    PRIVATE BUILD_TESTING
  )
  install(
    TARGETS joy_topic_manager_test
    DESTINATION lib/${PROJECT_NAME}
  )
endif()

ament_package()
