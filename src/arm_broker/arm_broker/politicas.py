"""Políticas de cola para el broker del JetCobot."""

import threading
import time


class Pedido:
    """Pedido generico administrado por la cola del broker.

    tipo='joint':
        movimiento articular tradicional de RB-2.

    tipo='orden':
        orden semantica de la Pregunta 2. La percepcion,
        IK y planificacion se realizan solamente cuando
        el worker la desencola.
    """

    def __init__(
        self,
        goal_handle,
        client_id,
        priority,
        joint_positions=None,
        tipo='joint',
        accion='',
        objeto='',
        color='',
        zona_destino=''
    ):
        self.goal_handle = goal_handle

        self.goal_id = bytes(
            goal_handle.goal_id.uuid
        ).hex()[:12]

        self.client_id = str(client_id)
        self.priority = int(priority)

        self.tipo = str(tipo)

        # Pedido RB-2 tradicional.
        self.joint_positions = (
            list(joint_positions)
            if joint_positions is not None
            else []
        )

        # Pedido semantico de Pregunta 2.
        self.accion = str(accion)
        self.objeto = str(objeto)
        self.color = str(color)
        self.zona_destino = str(zona_destino)

        self.t_llegada = time.time()
        self.t_inicio_ejec = None

        self.fin = threading.Event()
        self.resultado = None

    @property
    def espera_s(self):
        fin = (
            self.t_inicio_ejec
            if self.t_inicio_ejec
            else time.time()
        )

        return fin - self.t_llegada

    def __repr__(self):
        return (
            f'<{self.tipo} '
            f'{self.client_id} '
            f'p{self.priority} '
            f'{self.goal_id}>'
        )


class Politica:
    nombre = 'base'

    def siguiente(self, pendientes):
        raise NotImplementedError

    def atendido(self, pedido):
        pass


class FIFO(Politica):
    """
    First In First Out.

    Atiende el pedido que llegó primero.
    """

    nombre = 'fifo'

    def siguiente(self, pendientes):

        if not pendientes:
            return None

        indice = min(
            range(len(pendientes)),
            key=lambda i: pendientes[i].t_llegada
        )

        return indice


class SegundaPolitica(Politica):
    """
    Prioridad con envejecimiento.

    Mayor priority = más urgente.

    A medida que un pedido espera,
    incrementa su prioridad efectiva para
    reducir el riesgo de inanición.
    """

    nombre = 'prioridad'

    def __init__(self, tau_envejecimiento_s=8.0):

        self.tau = max(
            0.001,
            float(tau_envejecimiento_s)
        )

    def prioridad_efectiva(self, pedido):

        envejecimiento = (
            pedido.espera_s / self.tau
        )

        return (
            float(pedido.priority)
            + envejecimiento
        )

    def siguiente(self, pendientes):

        if not pendientes:
            return None

        # Mayor prioridad efectiva primero.
        #
        # En caso de empate se favorece al
        # pedido que llegó antes.
        indice = max(
            range(len(pendientes)),
            key=lambda i: (
                self.prioridad_efectiva(
                    pendientes[i]
                ),
                -pendientes[i].t_llegada,
            )
        )

        return indice


POLITICAS = {
    'fifo': FIFO,
    'prioridad': SegundaPolitica,
}
