cmake_minimum_required(VERSION 3.8)
project(denso_bringup)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(denso_description REQUIRED)
find_package(denso_hardware_interface REQUIRED)
find_package(denso_moveit_config REQUIRED)
find_package(gz_ros2_control REQUIRED)
find_package(rosbridge_server REQUIRED)
# https://docs.ros.org/en/humble/p/v4l2_camera/#
find_package(v4l2_camera REQUIRED)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
