# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.5)
project(rcdt_gazebo)

# CMake dependencies:
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

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

# Default test:
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/env-hooks/${PROJECT_NAME}.sh.in")
ament_package()
