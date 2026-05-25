cmake_minimum_required(VERSION 3.5)
project(denso_description)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY urdf meshes rviz launch
  DESTINATION share/${PROJECT_NAME}
)

# these line is to set environment variables for Gazebo to find the model and meshes
# https://gazebosim.org/docs/fortress/ros_gz_project_template_guide/#accessing-simulation-assets
ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/hooks/${PROJECT_NAME}.dsv.in")
ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/hooks/${PROJECT_NAME}.sh.in")

ament_package()
