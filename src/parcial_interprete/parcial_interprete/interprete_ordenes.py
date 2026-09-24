import time

import rclpy
from rclpy.node import Node

from parcial_interfaces.srv import InterpretarOrden
from .clasificador import clasificar_local


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

        self.get_logger().info(
            'Modo actual: clasificador local por palabras clave'
        )


    def interpretar_callback(self, request, response):

        inicio = time.perf_counter()

        frase = request.frase.strip()

        self.get_logger().info(
            f'Frase recibida: {frase}'
        )

        # Si llega una frase vacia, rechazamos
        if not frase:

            response.accion = 'desconocida'
            response.objeto = 'desconocido'
            response.color = 'desconocido'
            response.prioridad = 0
            response.permitido = False

            response.degradado = True
            response.metodo = 'keywords'

            response.http_total_ms = -1.0
            response.inferencia_laya_ms = -1.0
            response.rtt_red_ms = -1.0

            response.detalle = 'Frase vacia'

            response.tiempo_proceso_ms = (
                time.perf_counter() - inicio
            ) * 1000.0

            return response


        # Clasificacion local
        resultado = clasificar_local(frase)

        response.accion = resultado['accion']
        response.objeto = resultado['objeto']
        response.color = resultado['color']
        response.prioridad = int(
            resultado['prioridad']
        )
        response.permitido = bool(
            resultado['permitido']
        )

        # En este momento estamos usando solamente
        # el clasificador local.
        response.degradado = True
        response.metodo = 'keywords'

        # Aun no usamos LAYA
        response.http_total_ms = -1.0
        response.inferencia_laya_ms = -1.0
        response.rtt_red_ms = -1.0

        response.detalle = (
            'Clasificacion local por palabras clave'
        )

        response.tiempo_proceso_ms = (
            time.perf_counter() - inicio
        ) * 1000.0


        self.get_logger().info(
            'Resultado -> '
            f'accion={response.accion}, '
            f'objeto={response.objeto}, '
            f'color={response.color}, '
            f'prioridad={response.prioridad}, '
            f'permitido={response.permitido}'
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
