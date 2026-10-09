#!/usr/bin/env python3

import csv
import sys


def revisar(ruta):
    filas = 0
    ejecutando = 0
    max_cola = 0
    errores = []

    ultimo_completados = 0

    with open(ruta, newline='') as f:
        for n, fila in enumerate(
            csv.DictReader(f),
            start=2
        ):
            filas += 1

            cliente = fila[
                'executing_client'
            ].strip()

            gid = fila[
                'executing_goal_id'
            ].strip()

            cola = int(
                fila['queue_length']
                or 0
            )

            completados = int(
                fila['total_completed']
                or 0
            )

            max_cola = max(
                max_cola,
                cola
            )

            if cliente or gid:
                ejecutando += 1

            # Consistencia:
            # si hay cliente debe existir goal_id
            # y viceversa.
            if bool(cliente) != bool(gid):
                errores.append(
                    f'fila {n}: '
                    f'cliente/gid inconsistente'
                )

            # total_completed no debe retroceder.
            if completados < ultimo_completados:
                errores.append(
                    f'fila {n}: '
                    f'total_completed retrocedio'
                )

            ultimo_completados = completados

    print()
    print(f'Archivo: {ruta}')
    print(f'Filas: {filas}')
    print(
        f'Filas con un goal ejecutándose: '
        f'{ejecutando}'
    )
    print(
        f'Máxima longitud de cola: '
        f'{max_cola}'
    )
    print(
        f'Total completados final: '
        f'{ultimo_completados}'
    )

    if errores:
        print('RESULTADO: ERROR')
        for e in errores[:10]:
            print(' ', e)
        return False

    print(
        'RESULTADO: OK — '
        'estado de ejecución consistente'
    )

    return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(
            'Uso: verificar_exclusion.py '
            'queue_state.csv [...]'
        )

    ok = True

    for ruta in sys.argv[1:]:
        ok = revisar(ruta) and ok

    raise SystemExit(
        0 if ok else 1
    )
