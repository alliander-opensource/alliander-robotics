# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)
project(alliander_gazebo)

# CMake dependencies:
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)

# Python executables:
install(
  DIRECTORY src_py/
  DESTINATION lib/${PROJECT_NAME}
)

# Python package:
ament_python_install_package(${PROJECT_NAME})

# Shared folders:
install(
  DIRECTORY config launch models worlds
  DESTINATION share/${PROJECT_NAME}
)

# Navsat covariance node:
add_executable(navsat_covariance_node
  src/navsat_covariance.cpp
)
ament_target_dependencies(navsat_covariance_node
  rclcpp
  sensor_msgs
)
install(TARGETS
  navsat_covariance_node
  DESTINATION lib/${PROJECT_NAME}
)

# Gazebo charging checker:
find_package(gz_transport_vendor REQUIRED)
find_package(gz-transport13 REQUIRED)
find_package(gz_msgs_vendor REQUIRED)
find_package(gz-msgs10 REQUIRED)
find_package(eigen3_cmake_module REQUIRED)
find_package(Eigen3 REQUIRED)
add_executable(gz_charging_checker
  src/gz_charging_checker.cpp
)
ament_target_dependencies(gz_charging_checker
  rclcpp
  gz-transport13
  gz-msgs10
  Eigen3
)
install(TARGETS
  gz_charging_checker
  DESTINATION lib/${PROJECT_NAME}
)

ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/env-hooks/${PROJECT_NAME}.sh.in")
ament_package()
