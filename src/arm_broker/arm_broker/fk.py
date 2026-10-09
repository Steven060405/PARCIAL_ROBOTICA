"""Cinematica directa del JetCobot usando la tabla DH final."""

import math


JOINT_NAMES = [
    '1_Joint',
    '2_Joint',
    '3_Joint',
    '4_Joint',
    '5_Joint',
    '6_Joint',
]


# ============================================================
# TABLA DH FINAL
#
# Cada fila:
# (
#   alpha_rad,
#   a_mm,
#   d_mm,
#   theta_offset_rad
# )
#
# Tabla original:
#
# 1: theta1        d=134.75   a=0      alpha=+90
# 2: theta2 - 90   d=0        a=-110   alpha=0
# 3: theta3        d=0        a=-96    alpha=0
# 4: theta4 - 90   d=63.4     a=0      alpha=+90
# 5: theta5 + 90   d=75.05    a=0      alpha=-90
# 6: theta6        d=50       a=0      alpha=0
# ============================================================

DH = [
    (
        math.pi / 2.0,
        0.0,
        134.75,
        0.0
    ),

    (
        0.0,
        -110.0,
        0.0,
        -math.pi / 2.0
    ),

    (
        0.0,
        -96.0,
        0.0,
        0.0
    ),

    (
        math.pi / 2.0,
        0.0,
        63.4,
        -math.pi / 2.0
    ),

    (
        -math.pi / 2.0,
        0.0,
        75.05,
        math.pi / 2.0
    ),

    (
        0.0,
        0.0,
        50.0,
        0.0
    ),
]


JOINT_LIMITS = [
    (-2.93, 2.93),
    (-2.36, 2.36),
    (-2.53, 2.53),
    (-2.58, 2.58),
    (-2.93, 2.93),
    (-3.14, 3.14),
]


ALCANCE_MIN_MM = 80.0
ALCANCE_MAX_MM = 480.0


def _t(alpha, a, d, theta):
    """
    Transformacion DH estandar.

    T =
    RotZ(theta)
    TransZ(d)
    TransX(a)
    RotX(alpha)
    """

    ca = math.cos(alpha)
    sa = math.sin(alpha)

    ct = math.cos(theta)
    st = math.sin(theta)

    return [
        [
            ct,
            -st * ca,
            st * sa,
            a * ct
        ],

        [
            st,
            ct * ca,
            -ct * sa,
            a * st
        ],

        [
            0.0,
            sa,
            ca,
            d
        ],

        [
            0.0,
            0.0,
            0.0,
            1.0
        ],
    ]


def _mul(A, B):

    return [
        [
            sum(
                A[i][k] * B[k][j]
                for k in range(4)
            )
            for j in range(4)
        ]
        for i in range(4)
    ]


def fk_matriz(q):
    """
    Matriz homogenea 4x4 desde
    la base hasta el efector final.
    """

    if len(q) != 6:
        raise ValueError(
            f'Se esperaban 6 articulaciones, '
            f'llegaron {len(q)}'
        )

    T = [
        [
            1.0 if i == j else 0.0
            for j in range(4)
        ]
        for i in range(4)
    ]

    for (
        alpha,
        a,
        d,
        offset
    ), theta in zip(DH, q):

        Ti = _t(
            alpha,
            a,
            d,
            float(theta) + offset
        )

        T = _mul(
            T,
            Ti
        )

    return T


def fk(q):
    """
    Posicion del efector final.

    Devuelve:
        (x, y, z)

    Unidades:
        milimetros
    """

    T = fk_matriz(q)

    x = float(T[0][3])
    y = float(T[1][3])
    z = float(T[2][3])

    return (
        x,
        y,
        z
    )


def dentro_de_limites(q):

    if len(q) != 6:

        return (
            False,
            f'se esperaban 6 angulos, '
            f'llegaron {len(q)}'
        )

    for i, (
        valor,
        (lo, hi)
    ) in enumerate(
        zip(q, JOINT_LIMITS)
    ):

        if not lo <= valor <= hi:

            return (
                False,
                f'{JOINT_NAMES[i]} fuera de rango: '
                f'{valor:.3f} rad, '
                f'limite [{lo}, {hi}]'
            )

    return (
        True,
        ''
    )


def dentro_del_workspace(q):

    x, y, z = fk(q)

    r = math.sqrt(
        x * x
        + y * y
        + z * z
    )

    if r > ALCANCE_MAX_MM:

        return (
            False,
            f'efector a {r:.0f} mm de la base, '
            f'maximo {ALCANCE_MAX_MM:.0f}'
        )

    if r < ALCANCE_MIN_MM:

        return (
            False,
            f'efector a {r:.0f} mm de la base, '
            f'demasiado cerca'
        )

    if z < 0.0:

        return (
            False,
            f'z = {z:.0f} mm: '
            f'el efector quedaria bajo la base'
        )

    return (
        True,
        ''
    )


def paso_articular(
    q_desde,
    q_hasta
):

    if (
        len(q_desde) != 6
        or len(q_hasta) != 6
    ):
        return float('inf')

    return max(
        abs(b - a)
        for a, b
        in zip(
            q_desde,
            q_hasta
        )
    )
