cmake_minimum_required(VERSION 3.8)
project(visual_inspection)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ── Find packages ──────────────────────────────────────────────────────────────
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(moveit_msgs REQUIRED)
find_package(control_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# ── Custom message and action generation ──────────────────────────────────────
# NOTE: do NOT call ament_python_install_package() alongside rosidl_generate_interfaces
# for the same package name — rosidl registers the Python package internally.
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/InspectionResult.msg"
  "action/RunInspection.action"
  DEPENDENCIES std_msgs geometry_msgs
)

# ── C++ commander node ─────────────────────────────────────────────────────────
add_executable(inspection_commander_node
  src/inspection_commander_node.cpp
)

ament_target_dependencies(inspection_commander_node
  rclcpp
  rclcpp_action
  std_msgs
  geometry_msgs
  moveit_ros_planning_interface
  moveit_msgs
  control_msgs
)

# Link generated C++ typesupport
rosidl_get_typesupport_target(cpp_typesupport_target
  ${PROJECT_NAME} "rosidl_typesupport_cpp")
target_link_libraries(inspection_commander_node
  "${cpp_typesupport_target}"
)

install(TARGETS inspection_commander_node
  DESTINATION lib/${PROJECT_NAME}
)

# ── Python bridge node and metrics node ───────────────────────────────────────
# Installed directly (not via ament_python_install_package — see NOTE above)
install(PROGRAMS
  visual_inspection/inspection_node.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME inspection_node
)
install(PROGRAMS
  visual_inspection/inspection_metrics_node.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME inspection_metrics_node
)

# ── Install scripts, launch, config ───────────────────────────────────────────
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
