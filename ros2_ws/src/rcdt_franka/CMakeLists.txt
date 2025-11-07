# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)
project(rcdt_franka)

# CMake dependencies:
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(std_srvs REQUIRED)
find_package(franka_msgs REQUIRED)
find_package(control_msgs REQUIRED)
find_package(rcdt_messages REQUIRED)

# C++ executables:
include_directories(include)
add_executable(fr3_gripper_simulation src/fr3_gripper_simulation.cpp)
ament_target_dependencies(fr3_gripper_simulation
  rclcpp
  rclcpp_action
  std_srvs
  franka_msgs
  control_msgs
)
add_executable(gripper src/gripper.cpp)
ament_target_dependencies(gripper
  rclcpp
  rclcpp_action
  std_srvs
  franka_msgs
  rcdt_messages
)

install(
  TARGETS fr3_gripper_simulation gripper
  DESTINATION lib/${PROJECT_NAME}
)

# Shared folders:
install(
  DIRECTORY launch config urdf
  DESTINATION share/${PROJECT_NAME}
)

# Default test:
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
