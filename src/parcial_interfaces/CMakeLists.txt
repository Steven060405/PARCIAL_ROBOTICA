cmake_minimum_required(VERSION 3.8)
project(parcial_interfaces)

# Herramientas basicas de compilacion de ROS 2
find_package(ament_cmake REQUIRED)

# Generador de interfaces ROS 2 (.msg, .srv, .action)
find_package(rosidl_default_generators REQUIRED)

# Generar nuestro servicio personalizado
rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/InterpretarOrden.srv"
)

# Permitir que otros paquetes usen las interfaces generadas
ament_export_dependencies(rosidl_default_runtime)

ament_package()
