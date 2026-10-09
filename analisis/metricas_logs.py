#!/usr/bin/env python3

import glob
import os
import re
import statistics

PATRON = re.compile(
    r"success=True.*?"
    r"espera=([0-9.]+)s.*?"
    r"ejec=([0-9.]+)s"
)


def p95(xs):
    xs = sorted(xs)
    if not xs:
        return 0.0

    k = max(
        0,
        min(
            len(xs) - 1,
            int(round(
                0.95 * (len(xs) - 1)
            ))
        )
    )

    return xs[k]


def analizar(nombre, carpeta):
    print()
    print("=" * 60)
    print(nombre.upper())
    print("=" * 60)

    todas_esperas = []
    todas_ejecuciones = []

    archivos = sorted(
        glob.glob(
            os.path.join(
                carpeta,
                "*.log"
            )
        )
    )

    for ruta in archivos:
        esperas = []
        ejecuciones = []

        with open(
            ruta,
            encoding="utf-8",
            errors="ignore"
        ) as f:

            for linea in f:
                m = PATRON.search(linea)

                if m:
                    esperas.append(
                        float(m.group(1))
                    )

                    ejecuciones.append(
                        float(m.group(2))
                    )

        todas_esperas.extend(
            esperas
        )

        todas_ejecuciones.extend(
            ejecuciones
        )

        cliente = os.path.basename(
            ruta
        ).replace(".log", "")

        print()
        print(cliente)
        print(
            f"  goals       : {len(esperas)}"
        )

        if esperas:
            print(
                f"  espera media: "
                f"{statistics.mean(esperas):.3f} s"
            )

            print(
                f"  espera p95  : "
                f"{p95(esperas):.3f} s"
            )

            print(
                f"  espera max  : "
                f"{max(esperas):.3f} s"
            )

    print()
    print("RESUMEN GLOBAL")
    print(
        f"  goals       : "
        f"{len(todas_esperas)}"
    )

    if todas_esperas:
        print(
            f"  espera media: "
            f"{statistics.mean(todas_esperas):.3f} s"
        )

        print(
            f"  espera p95  : "
            f"{p95(todas_esperas):.3f} s"
        )

        print(
            f"  espera max  : "
            f"{max(todas_esperas):.3f} s"
        )

        print(
            f"  ejec media  : "
            f"{statistics.mean(todas_ejecuciones):.3f} s"
        )


analizar(
    "FIFO",
    "resultados_item2/fifo/logs"
)

analizar(
    "PRIORIDAD",
    "resultados_item2/prioridad/logs"
)
