import re
import time

import requests
import rclpy
from rclpy.node import Node

from parcial_interfaces.srv import InterpretarOrden
from .clasificador import clasificar_local


class InterpreteOrdenes(Node):

    def __init__(self):
        super().__init__('interprete_ordenes')

        # ==========================
        # PARAMETROS
        # ==========================
        self.declare_parameter(
            'laya_url',
            'http://127.0.0.1:8000'
        )

        self.declare_parameter(
            'laya_preset',
            'manual_prueba'
        )

        self.declare_parameter(
            'laya_model',
            'typed-decisions'
        )

        self.declare_parameter(
            'timeout_s',
            5.0
        )

        self.laya_url = str(
            self.get_parameter('laya_url').value
        ).rstrip('/')

        self.laya_preset = str(
            self.get_parameter('laya_preset').value
        )

        self.laya_model = str(
            self.get_parameter('laya_model').value
        )

        self.timeout_s = float(
            self.get_parameter('timeout_s').value
        )

        # Session HTTP.
        # Evitamos que proxies del sistema interfieran
        # con la conexion local al servidor LAYA.
        self.http = requests.Session()
        self.http.trust_env = False

        self.servicio = self.create_service(
            InterpretarOrden,
            '/interpretar_orden',
            self.interpretar_callback
        )

        self.get_logger().info(
            'interprete_ordenes listo'
        )

        self.get_logger().info(
            f'LAYA URL: {self.laya_url}'
        )

        self.get_logger().info(
            f'LAYA preset/identificador: {self.laya_preset}'
        )

        self.get_logger().info(
            f'LAYA modelo: {self.laya_model}'
        )

        self.get_logger().info(
            f'Timeout: {self.timeout_s:.2f} s'
        )


    def construir_preguntas(self):

        return {
            'accion': {
                'type': 'choice',
                'instructions': (
                    'Selecciona exactamente que accion ordena '
                    'realizar la persona al robot.'
                ),
                'criteria': {
                    'recoger': (
                        'La persona ordena recoger, tomar, '
                        'agarrar o coger un objeto.'
                    ),
                    'depositar': (
                        'La persona ordena colocar, poner, '
                        'llevar o depositar un objeto.'
                    ),
                    'detener': (
                        'La persona ordena detener, parar '
                        'o cancelar el movimiento.'
                    ),
                },
            },

            'objeto': {
                'type': 'choice',
                'instructions': (
                    'Selecciona exactamente el objeto '
                    'mencionado en la orden.'
                ),
                'criteria': {
                    'cubo': (
                        'El objeto mencionado es un cubo.'
                    ),
                    'bloque': (
                        'El objeto mencionado es un bloque.'
                    ),
                    'botella': (
                        'El objeto mencionado es una botella.'
                    ),
                    'pelota': (
                        'El objeto mencionado es una pelota.'
                    ),
                },
            },

            'color': {
                'type': 'choice',
                'instructions': (
                    'Selecciona exactamente el color '
                    'mencionado en la orden.'
                ),
                'criteria': {
                    'rojo': (
                        'El color mencionado es rojo o roja.'
                    ),
                    'verde': (
                        'El color mencionado es verde.'
                    ),
                    'azul': (
                        'El color mencionado es azul.'
                    ),
                    'amarillo': (
                        'El color mencionado es amarillo '
                        'o amarilla.'
                    ),
                },
            },

            'prioridad': {
                'type': 'choice',
                'instructions': (
                    'Clasifica exclusivamente el nivel '
                    'de prioridad expresado en la orden.'
                ),
                'criteria': {
                    'baja': (
                        'La persona indica que puede hacerse '
                        'cuando sea posible, sin apuro, '
                        'despacio o con prioridad baja.'
                    ),
                    'normal': (
                        'La persona da una orden normal '
                        'y no expresa urgencia ni tampoco '
                        'que pueda esperar.'
                    ),
                    'alta': (
                        'La persona indica que debe hacerse '
                        'rapido, que es importante o que '
                        'tiene prioridad alta.'
                    ),
                    'urgente': (
                        'La persona indica emergencia, '
                        'urgente, inmediatamente '
                        'o ahora mismo.'
                    ),
                },
            },

            'permitido': {
                'type': 'choice',
                'instructions': (
                    'Clasifica exclusivamente si la orden '
                    'es segura para un brazo robotico.'
                ),
                'criteria': {
                    'permitido': (
                        'La orden pide recoger, colocar, '
                        'mover o detener objetos de forma '
                        'segura y sin causar daño.'
                    ),
                    'no_permitido': (
                        'La orden pide golpear, atacar, '
                        'lastimar o causar daño.'
                    ),
                },
            },
        }


    def obtener_inferencia_ms(self, respuesta_http):

        # LAYA moderno publica este encabezado.
        valor = respuesta_http.headers.get(
            'X-Inference-Time-Ms'
        )

        if valor is not None:
            try:
                return float(valor)
            except (TypeError, ValueError):
                pass

        # Alternativa estandar Server-Timing:
        # inference;dur=12.34
        server_timing = respuesta_http.headers.get(
            'Server-Timing',
            ''
        )

        coincidencia = re.search(
            r'inference\s*;\s*dur=([0-9.]+)',
            server_timing
        )

        if coincidencia:
            try:
                return float(coincidencia.group(1))
            except ValueError:
                pass

        return -1.0


    def consultar_laya(self, frase):

        url = (
            self.laya_url
            + '/v1/systemone'
        )

        payload = {
            'state': frase,
            'lang': 'es',
            'model': self.laya_model,
            'questions': self.construir_preguntas(),
        }

        inicio_http = time.perf_counter()

        respuesta_http = self.http.post(
            url,
            json=payload,
            timeout=self.timeout_s
        )

        http_total_ms = (
            time.perf_counter() - inicio_http
        ) * 1000.0

        respuesta_http.raise_for_status()

        datos = respuesta_http.json()

        respuestas = datos.get(
            'answers',
            {}
        )

        accion = respuestas.get(
            'accion',
            {}
        ).get(
            'choice',
            'desconocida'
        )

        objeto = respuestas.get(
            'objeto',
            {}
        ).get(
            'choice',
            'desconocido'
        )

        color = respuestas.get(
            'color',
            {}
        ).get(
            'choice',
            'desconocido'
        )

        prioridad_texto = respuestas.get(
            'prioridad',
            {}
        ).get(
            'choice',
            'normal'
        )

        permitido_texto = respuestas.get(
            'permitido',
            {}
        ).get(
            'choice',
            'no_permitido'
        )

        mapa_prioridad = {
            'baja': 0,
            'normal': 1,
            'alta': 2,
            'urgente': 3,
        }

        prioridad = mapa_prioridad.get(
            prioridad_texto,
            1
        )

        permitido = (
            permitido_texto == 'permitido'
        )

        inferencia_laya_ms = (
            self.obtener_inferencia_ms(
                respuesta_http
            )
        )

        if inferencia_laya_ms >= 0.0:
            rtt_red_ms = max(
                0.0,
                http_total_ms - inferencia_laya_ms
            )
        else:
            rtt_red_ms = -1.0

        return {
            'accion': str(accion),
            'objeto': str(objeto),
            'color': str(color),
            'prioridad': int(prioridad),
            'permitido': bool(permitido),

            'http_total_ms': float(
                http_total_ms
            ),

            'inferencia_laya_ms': float(
                inferencia_laya_ms
            ),

            'rtt_red_ms': float(
                rtt_red_ms
            ),

            'modelo_respuesta': str(
                datos.get(
                    'model',
                    self.laya_model
                )
            ),
        }


    def aplicar_keywords(
        self,
        frase,
        response,
        inicio,
        detalle,
        http_total_ms=-1.0
    ):

        resultado = clasificar_local(
            frase
        )

        response.accion = resultado[
            'accion'
        ]

        response.objeto = resultado[
            'objeto'
        ]

        response.color = resultado[
            'color'
        ]

        response.prioridad = int(
            resultado['prioridad']
        )

        response.permitido = bool(
            resultado['permitido']
        )

        response.degradado = True
        response.metodo = 'keywords'

        response.http_total_ms = float(
            http_total_ms
        )

        response.inferencia_laya_ms = -1.0
        response.rtt_red_ms = -1.0

        response.detalle = detalle

        response.tiempo_proceso_ms = (
            time.perf_counter() - inicio
        ) * 1000.0

        return response


    def interpretar_callback(
        self,
        request,
        response
    ):

        inicio = time.perf_counter()

        frase = request.frase.strip()

        self.get_logger().info(
            f'Frase recibida: {frase}'
        )

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

        # Clasificacion local se calcula siempre.
        # Ademas del fallback, se usa como veto de
        # seguridad ante palabras explicitamente peligrosas.
        resultado_local = clasificar_local(
            frase
        )

        inicio_http = time.perf_counter()

        try:

            resultado_laya = self.consultar_laya(
                frase
            )

            # ==========================
            # SALIDAS CRUDAS DE LAYA
            # ==========================
            prioridad_laya = int(
                resultado_laya['prioridad']
            )

            permitido_laya = bool(
                resultado_laya['permitido']
            )

            # ==========================
            # NORMALIZACION LOCAL
            # ==========================
            prioridad_local = int(
                resultado_local['prioridad']
            )

            permitido_local = bool(
                resultado_local['permitido']
            )

            # Accion, objeto y color:
            # siempre vienen de LAYA cuando LAYA responde.
            response.accion = resultado_laya[
                'accion'
            ]

            response.objeto = resultado_laya[
                'objeto'
            ]

            response.color = resultado_laya[
                'color'
            ]

            # Prioridad:
            # conservamos la salida cruda de LAYA
            # para las metricas, pero la salida final
            # se normaliza mediante reglas deterministas.
            response.prioridad = prioridad_local

            # Seguridad:
            # LAYA propone y keywords puede vetar.
            permitido_final = (
                permitido_laya
                and permitido_local
            )

            veto_local = (
                permitido_laya
                and not permitido_local
            )

            response.permitido = permitido_final

            # LAYA respondio correctamente:
            # no estamos en modo degradado.
            response.degradado = False

            if veto_local:
                response.metodo = (
                    'laya+normalizacion_prioridad+veto_local'
                )
            else:
                response.metodo = (
                    'laya+normalizacion_prioridad'
                )

            response.http_total_ms = float(
                resultado_laya[
                    'http_total_ms'
                ]
            )

            response.inferencia_laya_ms = float(
                resultado_laya[
                    'inferencia_laya_ms'
                ]
            )

            response.rtt_red_ms = float(
                resultado_laya[
                    'rtt_red_ms'
                ]
            )

            response.detalle = (
                'LAYA OK; '
                f'modelo='
                f'{resultado_laya["modelo_respuesta"]}; '
                f'preset={self.laya_preset}; '
                f'prioridad_laya={prioridad_laya}; '
                f'prioridad_local={prioridad_local}; '
                f'permitido_laya={permitido_laya}; '
                f'permitido_local={permitido_local}; '
                f'veto_local={veto_local}'
            )

        except requests.exceptions.Timeout:

            http_fallido_ms = (
                time.perf_counter()
                - inicio_http
            ) * 1000.0

            self.get_logger().warning(
                'Timeout de LAYA. '
                'Activando fallback keywords.'
            )

            return self.aplicar_keywords(
                frase,
                response,
                inicio,
                (
                    'Fallback por timeout de LAYA; '
                    f'preset={self.laya_preset}'
                ),
                http_total_ms=http_fallido_ms
            )

        except Exception as error:

            http_fallido_ms = (
                time.perf_counter()
                - inicio_http
            ) * 1000.0

            self.get_logger().warning(
                'Fallo de LAYA. '
                'Activando fallback keywords. '
                f'Error={type(error).__name__}'
            )

            return self.aplicar_keywords(
                frase,
                response,
                inicio,
                (
                    'Fallback por fallo de LAYA: '
                    f'{type(error).__name__}; '
                    f'preset={self.laya_preset}'
                ),
                http_total_ms=http_fallido_ms
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
            f'permitido={response.permitido}, '
            f'degradado={response.degradado}, '
            f'metodo={response.metodo}'
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
