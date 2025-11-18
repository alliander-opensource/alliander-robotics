# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)
project(rcdt_utilities)

# CMake dependencies:
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# Other dependencies:
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(tf2_ros REQUIRED)

find_package(geometry_msgs REQUIRED)
find_package(rcdt_interfaces REQUIRED)

# Python package:
ament_python_install_package(${PROJECT_NAME})

# Python executables:
install(
  DIRECTORY src_py/
  DESTINATION lib/${PROJECT_NAME}
)

# C++ executables:
include_directories(include)

add_executable(manipulate_pose 
  src/manipulate_pose.cpp
  src/node.cpp
)
ament_target_dependencies(manipulate_pose
  geometry_msgs
  rcdt_interfaces
  rclcpp
  tf2
  tf2_geometry_msgs
  tf2_ros
)

install(
  TARGETS manipulate_pose
  DESTINATION lib/${PROJECT_NAME}
)

# Shared folders:
install(
  DIRECTORY launch rviz urdf
  DESTINATION share/${PROJECT_NAME}
)

# Default test:
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  find_package(ament_cmake_gtest REQUIRED)

  ament_lint_auto_find_test_dependencies()

  ament_add_gtest(manipulate_pose_test
    tests/test_package.cpp
    src/manipulate_pose.cpp
  )
  ament_target_dependencies(manipulate_pose_test
    geometry_msgs
    rcdt_interfaces
    rclcpp
    tf2
    tf2_geometry_msgs
    tf2_ros
  )
  install(
    TARGETS manipulate_pose_test
    DESTINATION lib/${PROJECT_NAME}
  )
endif()

ament_package()
