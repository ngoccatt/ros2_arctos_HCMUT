cmake_minimum_required(VERSION 3.5)
project(denso_hardware_interface)

# Compiler options
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(can_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(realtime_tools REQUIRED)
find_package(trajectory_msgs REQUIRED)
find_package(denso_motor_driver REQUIRED)
find_package(pluginlib REQUIRED)
find_package(std_srvs REQUIRED)
find_package(std_msgs REQUIRED)

# ===================================== Add library for hardware interface  ===================================== 
add_library(denso_interface SHARED
  src/denso_interface.cpp
  src/denso_hand_interface.cpp
)

# Link the hardware interface libraries and dependencies
target_link_libraries(denso_interface
  ${rclcpp_LIBRARIES}
  ${hardware_interface_LIBRARIES} 
)

# Include directories
target_include_directories(denso_interface
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# Specify dependencies
ament_target_dependencies(denso_interface
  rclcpp
  can_msgs
  sensor_msgs
  denso_motor_driver  
  hardware_interface
  trajectory_msgs
  realtime_tools
  std_srvs
  std_msgs
)

# Export the plugin description file
pluginlib_export_plugin_description_file(hardware_interface "denso_hardware_interface.xml")

# Install targets
install(TARGETS 
  denso_interface
  EXPORT export_denso_interface
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  RUNTIME DESTINATION bin
  INCLUDES DESTINATION include
)

# Install header files
install(DIRECTORY include/
  DESTINATION include
)

# install(DIRECTORY config 
#   DESTINATION share/${PROJECT_NAME}
# )

# install(DIRECTORY ros2_control
#   DESTINATION share/${PROJECT_NAME}/ros2_control
# )

# Install launch files
install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

install(FILES denso_hardware_interface.xml
  DESTINATION share/${PROJECT_NAME}
)

# Export package
ament_export_targets(export_denso_interface HAS_LIBRARY_TARGET)
ament_export_dependencies(
  rclcpp 
  can_msgs 
  sensor_msgs 
  hardware_interface 
  std_srvs
  std_msgs
)

ament_package()