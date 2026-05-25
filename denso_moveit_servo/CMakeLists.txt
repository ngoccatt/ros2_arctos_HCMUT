cmake_minimum_required(VERSION 3.8)
project(denso_moveit_servo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(moveit_servo REQUIRED)
find_package(trajectory_msgs REQUIRED)
find_package(control_msgs REQUIRED)
find_package(std_srvs REQUIRED)

# Create component library
add_library(denso_moveit_servo_node SHARED src/denso_moveit_servo_node.cpp)

ament_target_dependencies(denso_moveit_servo_node 
  rclcpp 
  rclcpp_components 
  moveit_servo 
  trajectory_msgs 
  control_msgs 
  std_srvs
)

# Register the component
rclcpp_components_register_node(denso_moveit_servo_node
  PLUGIN "denso_moveit_servo::DensoMoveItServoNode"
  EXECUTABLE denso_moveit_servo_node_exec
)

# then install the second file (as executable)
add_executable(servo_keyboard_input src/servo_keyboard_input.cpp)

ament_target_dependencies(servo_keyboard_input rclcpp moveit_servo trajectory_msgs control_msgs std_srvs)

target_include_directories(denso_moveit_servo_node PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)

target_include_directories(servo_keyboard_input PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)

target_compile_features(denso_moveit_servo_node PUBLIC c_std_99 cxx_std_17)

target_compile_features(servo_keyboard_input PUBLIC c_std_99 cxx_std_17)

install(
  TARGETS denso_moveit_servo_node
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(
  TARGETS servo_keyboard_input
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

# if(BUILD_TESTING)
#   find_package(ament_lint_auto REQUIRED)
#   # the following line skips the linter which checks for copyrights
#   # comment the line when a copyright and license is added to all source files
#   set(ament_cmake_copyright_FOUND TRUE)
#   # the following line skips cpplint (only works in a git repo)
#   # comment the line when this package is in a git repo and when
#   # a copyright and license is added to all source files
#   set(ament_cmake_cpplint_FOUND TRUE)
#   ament_lint_auto_find_test_dependencies()
# endif()

ament_package()
