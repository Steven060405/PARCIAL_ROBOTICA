cmake_minimum_required(VERSION 3.8)
project(arm_broker_interfaces)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(action_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(trajectory_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "action/MoveArm.action"
  "action/OrdenBrazo.action"
  "srv/LocalizarObjeto.srv"
  "srv/PlanificarPose.srv"
  "msg/QueueState.msg"
  DEPENDENCIES action_msgs builtin_interfaces trajectory_msgs
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
