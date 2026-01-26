# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)
<<<<<<<< HEAD:rcdt_visualization/src/rcdt_visualization/CMakeLists.txt
project(rcdt_visualization)
========
project(rcdt_nav2)
>>>>>>>> main:ros2_ws/src/rcdt_nav2/CMakeLists.txt

# CMake dependencies:
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

<<<<<<<< HEAD:rcdt_visualization/src/rcdt_visualization/CMakeLists.txt
# Python package:
ament_python_install_package(${PROJECT_NAME})

========
>>>>>>>> main:ros2_ws/src/rcdt_nav2/CMakeLists.txt
# Python executables:
install(
  DIRECTORY src_py/
  DESTINATION lib/${PROJECT_NAME}
)

# Shared folders:
install(
<<<<<<<< HEAD:rcdt_visualization/src/rcdt_visualization/CMakeLists.txt
  DIRECTORY config launch rviz
========
  DIRECTORY launch config 
>>>>>>>> main:ros2_ws/src/rcdt_nav2/CMakeLists.txt
  DESTINATION share/${PROJECT_NAME}
)

# Default test:
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()