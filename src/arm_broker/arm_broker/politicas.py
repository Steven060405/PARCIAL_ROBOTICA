"""Políticas de cola para el broker del JetCobot."""

import threading
import time


class Pedido:
    def __init__(
        self,
        goal_handle,
        client_id,
        priority,
        joint_positions
    ):
        self.goal_handle = goal_handle

        self.goal_id = bytes(
            goal_handle.goal_id.uuid
        ).hex()[:12]

        self.client_id = client_id
        self.priority = int(priority)

        self.joint_positions = list(
            joint_positions
        )

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
            f'<{self.client_id} '
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
