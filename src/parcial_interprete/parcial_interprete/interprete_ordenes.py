import rclpy
from rclpy.node import Node

from parcial_interfaces.srv import InterpretarOrden


class InterpreteOrdenes(Node):

    def __init__(self):
        super().__init__('interprete_ordenes')

        self.servicio = self.create_service(
            InterpretarOrden,
            '/interpretar_orden',
            self.interpretar_callback
        )

        self.get_logger().info(
            'interprete_ordenes listo'
        )

    def interpretar_callback(self, request, response):

        self.get_logger().info(
            f'Frase recibida: {request.frase}'
        )

        # RESPUESTA FIJA SOLO PARA PROBAR ROS 2
        response.accion = 'recoger'
        response.objeto = 'objeto_prueba'
        response.color = 'rojo'
        response.prioridad = 1
        response.permitido = True

        # Todavia no estamos usando LAYA
        response.degradado = True
        response.metodo = 'prueba_local'

        response.tiempo_proceso_ms = 0.0
        response.http_total_ms = -1.0
        response.inferencia_laya_ms = -1.0
        response.rtt_red_ms = -1.0

        response.detalle = (
            'Respuesta fija para comprobar el servicio ROS 2'
        )

        return response


def main(args=None):

    rclpy.init(args=args)

    nodo = InterpreteOrdenes()

    try:
        rclpy.spin(nodo)

    except KeyboardInterrupt:
        pass

    nodo.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
