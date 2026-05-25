# Minimum CMake version for this package.
cmake_minimum_required(VERSION 3.8)

# Package name.
project(denso_remote_control)

# Enable common warnings when using GCC/Clang.
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find required build and runtime dependencies.
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(denso_interfaces)

# Optional template for additional dependencies.
# find_package(<dependency> REQUIRED)

# Legacy executable path kept as reference (disabled).
# add_executable(remote_control_server src/remote_control_server.cpp)
# ament_target_dependencies(remote_control_server rclcpp std_msgs moveit_ros_planning_interface denso_interfaces)
# target_include_directories(remote_control_server PUBLIC
#   $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
#   $<INSTALL_INTERFACE:include>)
# target_compile_features(remote_control_server PUBLIC c_std_99 cxx_std_17)
# install(TARGETS remote_control_server
#   DESTINATION lib/${PROJECT_NAME})
# install(DIRECTORY
#   launch
#   DESTINATION share/${PROJECT_NAME}
# )

# Build the composable node as a shared library.
add_library(remote_control_server SHARED
  src/remote_control_server.cpp
)

# Include paths for build and install contexts.
# tells the compiler where to look for #include header files when building remote_control_server.
# PRIVATE means these include paths are only needed to compile this target itself — 
# they won't be propagated to other targets that link against this library. The alternatives are:
target_include_directories(remote_control_server PRIVATE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)

# Link target dependencies.
ament_target_dependencies(remote_control_server
  std_msgs
  rclcpp
  rclcpp_action
  rclcpp_components
  moveit_ros_planning_interface
  denso_interfaces
)

# Register component plugin and create an "thin" executable wrapper.
rclcpp_components_register_node(remote_control_server PLUGIN "action_denso_control::RemoteControlServer" EXECUTABLE remote_control_server_executer)

# Install library/executable artifacts.
# ARCHIVE is for Static libraries (.a / .lib), DLL import libraries (.lib), and a handful of other "archive-like" objects.
# LIBRARY is for Shared libraries (.so), modules, and other dynamically loadable objects. Not Window's DLL files (.dll) or MacOS frameworks.
# RUNTIME Executables of all kinds except MacOS bundles; and Window's DLLs (.dll).
# This is just boilerplate pattern for multi-platform support. The actual files generated on Linux is only LIBRARY.
install(TARGETS
  remote_control_server
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)

install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}
)

# Optional lint/test block (disabled).
# if(BUILD_TESTING)
#   find_package(ament_lint_auto REQUIRED)
#   set(ament_cmake_copyright_FOUND TRUE)
#   set(ament_cmake_cpplint_FOUND TRUE)
#   ament_lint_auto_find_test_dependencies()
# endif()

# Finalize the ament package.
ament_package()
