# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)
project(alliander_seekthermal)

# CMake dependencies:
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# Other dependencies:
find_package(OpenCV REQUIRED COMPONENTS core imgproc)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)

# Debug dependency
find_package(cv_bridge REQUIRED)

# Python package:
ament_python_install_package(${PROJECT_NAME})

# C++ executables:
include_directories(include)
add_executable(thermal_detector_node src/thermal_detector.cpp src/thermal_detector_node.cpp)
ament_target_dependencies(thermal_detector_node
  cv_bridge
  rclcpp
  sensor_msgs
  std_msgs
)
target_include_directories(thermal_detector_node
  PRIVATE
  include
  ${OpenCV_INCLUDE_DIRS}
)
target_link_libraries(thermal_detector_node  
  ${OpenCV_LIBS}
)

install(
  TARGETS thermal_detector_node
  DESTINATION lib/${PROJECT_NAME}
)

# Python executables:
install(
  DIRECTORY src_py/
  DESTINATION lib/${PROJECT_NAME}
)

# Shared folders:
install(
  DIRECTORY launch 
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
