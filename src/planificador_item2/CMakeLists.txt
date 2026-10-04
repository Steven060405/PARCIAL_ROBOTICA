cmake_minimum_required(VERSION 3.8)
project(planificador_item2)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(arm_broker_interfaces REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(trajectory_msgs REQUIRED)

add_executable(
  planificador_moveit
  src/planificador_moveit.cpp
)

ament_target_dependencies(
  planificador_moveit
  rclcpp
  moveit_ros_planning_interface
  arm_broker_interfaces
  geometry_msgs
  trajectory_msgs
)

install(
  TARGETS planificador_moveit
  DESTINATION lib/${PROJECT_NAME}
)


install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
