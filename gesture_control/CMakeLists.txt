cmake_minimum_required(VERSION 3.8)
project(gesture_control)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ── Find packages ─────────────────────────────────────────────────────────────
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(moveit_msgs REQUIRED)
find_package(control_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# ── Custom message generation ─────────────────────────────────────────────────
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/GestureDetection.msg"
  DEPENDENCIES std_msgs
)

# ── C++ commander node ────────────────────────────────────────────────────────
add_executable(gesture_commander_node
  src/gesture_commander_node.cpp
)

ament_target_dependencies(gesture_commander_node
  rclcpp
  rclcpp_action
  std_msgs
  sensor_msgs
  moveit_ros_planning_interface
  moveit_msgs
  control_msgs
  std_srvs
)

# Link generated C++ message typesupport to the executable
rosidl_get_typesupport_target(cpp_typesupport_target
  ${PROJECT_NAME} "rosidl_typesupport_cpp")
target_link_libraries(gesture_commander_node
  "${cpp_typesupport_target}"
)

install(TARGETS gesture_commander_node
  DESTINATION lib/${PROJECT_NAME}
)

# ── Python recognition node ───────────────────────────────────────────────────
# Note: ament_python_install_package is NOT called here because
# rosidl_generate_interfaces already registers the gesture_control Python package
# (for the generated message bindings). Calling it again would create duplicate targets.
# The node script is installed directly as an executable.
install(PROGRAMS
  gesture_control/gesture_recognition_node.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME gesture_recognition_node
)

# ── Python metrics node ───────────────────────────────────────────────────────
install(PROGRAMS
  gesture_control/gesture_metrics_node.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME gesture_metrics_node
)

# ── Install scripts, launch, config ──────────────────────────────────────────
install(DIRECTORY scripts/
  DESTINATION share/${PROJECT_NAME}/scripts
)
install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)
install(DIRECTORY config/
  DESTINATION share/${PROJECT_NAME}/config
)

ament_package()
