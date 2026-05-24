cmake_minimum_required(VERSION 3.8)
project(benchmark)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

add_executable(topic_latency_benchmark src/topic_latency_benchmark.cpp)
target_compile_features(topic_latency_benchmark PUBLIC cxx_std_17)
ament_target_dependencies(topic_latency_benchmark rclcpp std_msgs)

install(TARGETS
  topic_latency_benchmark
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()