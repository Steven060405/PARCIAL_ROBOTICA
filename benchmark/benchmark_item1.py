#!/usr/bin/env python3

import csv
import re
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import rclpy
from rclpy.node import Node

from parcial_interfaces.srv import InterpretarOrden
from parcial_interprete.clasificador import clasificar_local


BASE = Path.home() / "parcial_ws" / "benchmark"
ENTRADA = BASE / "frases_50.csv"


def bool_csv(valor):
    return str(valor).strip().lower() in {
        "true", "1", "si", "sí", "yes"
    }


def bool_texto(valor):
    if valor is None:
        return ""

    if isinstance(valor, bool):
        return valor

    texto = str(valor).strip().lower()

    if texto == "true":
        return True

    if texto == "false":
        return False

    return ""


def extraer_prioridad_laya(detalle):
    m = re.search(
        r"prioridad_laya=(\d+)",
        detalle
    )

    if m:
        return int(m.group(1))

    return ""


def extraer_permitido_laya(detalle):
    m = re.search(
        r"permitido_laya=(True|False)",
        detalle
    )

    if m:
        return m.group(1) == "True"

    return ""


def coincide(a, b):
    return a == b


def porcentaje(aciertos, total):
    if total == 0:
        return 0.0

    return 100.0 * aciertos / total


def percentil(valores, p):
    """
    Percentil con interpolacion lineal.
    p debe estar entre 0 y 1.
    """
    valores = sorted(valores)

    if not valores:
        return float("nan")

    if len(valores) == 1:
        return valores[0]

    posicion = (len(valores) - 1) * p

    inferior = int(posicion)
    superior = min(
        inferior + 1,
        len(valores) - 1
    )

    fraccion = posicion - inferior

    return (
        valores[inferior]
        + (
            valores[superior]
            - valores[inferior]
        ) * fraccion
    )


def resumen_tiempos(nombre, valores):
    valores = [
        float(x)
        for x in valores
        if x is not None
        and float(x) >= 0.0
    ]

    if not valores:
        return (
            f"{nombre}: sin datos validos"
        )

    mediana = statistics.median(valores)
    p95 = percentil(valores, 0.95)

    return (
        f"{nombre}: "
        f"n={len(valores)}, "
        f"mediana={mediana:.3f} ms, "
        f"p95={p95:.3f} ms"
    )


class BenchmarkItem1(Node):

    def __init__(self):
        super().__init__(
            "benchmark_item1"
        )

        self.cliente = self.create_client(
            InterpretarOrden,
            "/interpretar_orden"
        )

    def llamar(self, frase):

        peticion = InterpretarOrden.Request()
        peticion.frase = frase

        futuro = self.cliente.call_async(
            peticion
        )

        rclpy.spin_until_future_complete(
            self,
            futuro,
            timeout_sec=15.0
        )

        if not futuro.done():
            raise TimeoutError(
                "El servicio ROS no respondio "
                "en 15 segundos."
            )

        if futuro.exception() is not None:
            raise RuntimeError(
                str(futuro.exception())
            )

        return futuro.result()


def main():

    if not ENTRADA.exists():
        print(
            f"ERROR: no existe {ENTRADA}"
        )
        sys.exit(1)

    with ENTRADA.open(
        newline="",
        encoding="utf-8"
    ) as f:

        frases = list(
            csv.DictReader(f)
        )

    if not frases:
        print(
            "ERROR: el CSV no contiene frases."
        )
        sys.exit(1)

    print(
        f"Frases cargadas: {len(frases)}"
    )

    rclpy.init()

    nodo = BenchmarkItem1()

    print(
        "Esperando /interpretar_orden ..."
    )

    if not nodo.cliente.wait_for_service(
        timeout_sec=10.0
    ):
        print(
            "ERROR: /interpretar_orden "
            "no esta disponible."
        )

        nodo.destroy_node()
        rclpy.shutdown()
        sys.exit(1)

    print("Servicio disponible.")
    print()

    resultados = []

    total = len(frases)

    for indice, fila in enumerate(
        frases,
        start=1
    ):

        frase = fila["frase"].strip()

        esperado = {
            "accion": fila[
                "accion_esperada"
            ].strip(),

            "objeto": fila[
                "objeto_esperado"
            ].strip(),

            "color": fila[
                "color_esperado"
            ].strip(),

            "prioridad": int(
                fila[
                    "prioridad_esperada"
                ]
            ),

            "permitido": bool_csv(
                fila[
                    "permitido_esperado"
                ]
            ),
        }

        print(
            f"[{indice:02d}/{total:02d}] "
            f"{frase}"
        )

        # ---------------------------
        # KEYWORDS
        # ---------------------------
        keywords = clasificar_local(
            frase
        )

        inicio_cliente = time.perf_counter()

        try:

            respuesta = nodo.llamar(
                frase
            )

            tiempo_cliente_ms = (
                time.perf_counter()
                - inicio_cliente
            ) * 1000.0

        except Exception as error:

            print(
                "  ERROR servicio:",
                type(error).__name__,
                error
            )

            continue

        # ---------------------------
        # SALIDA FINAL
        # ---------------------------
        final = {
            "accion": respuesta.accion,
            "objeto": respuesta.objeto,
            "color": respuesta.color,
            "prioridad": int(
                respuesta.prioridad
            ),
            "permitido": bool(
                respuesta.permitido
            ),
        }

        # ---------------------------
        # SALIDA CRUDA LAYA
        # Accion, objeto y color de la
        # respuesta final corresponden
        # a LAYA si no hubo fallback.
        # ---------------------------
        laya_disponible = (
            not respuesta.degradado
        )

        if laya_disponible:

            laya = {
                "accion": respuesta.accion,
                "objeto": respuesta.objeto,
                "color": respuesta.color,

                "prioridad":
                    extraer_prioridad_laya(
                        respuesta.detalle
                    ),

                "permitido":
                    extraer_permitido_laya(
                        respuesta.detalle
                    ),
            }

        else:

            laya = {
                "accion": "",
                "objeto": "",
                "color": "",
                "prioridad": "",
                "permitido": "",
            }

        # ---------------------------
        # ACIERTOS POR CAMPO
        # ---------------------------
        aciertos_keywords = {
            campo: coincide(
                keywords[campo],
                esperado[campo]
            )
            for campo in esperado
        }

        aciertos_final = {
            campo: coincide(
                final[campo],
                esperado[campo]
            )
            for campo in esperado
        }

        if laya_disponible:

            aciertos_laya = {
                campo: coincide(
                    laya[campo],
                    esperado[campo]
                )
                for campo in esperado
            }

        else:

            aciertos_laya = {
                campo: ""
                for campo in esperado
            }

        fila_salida = {
            "numero": indice,
            "frase": frase,

            # Esperado
            "accion_esperada":
                esperado["accion"],
            "objeto_esperado":
                esperado["objeto"],
            "color_esperado":
                esperado["color"],
            "prioridad_esperada":
                esperado["prioridad"],
            "permitido_esperado":
                esperado["permitido"],

            # LAYA crudo
            "laya_disponible":
                laya_disponible,
            "accion_laya":
                laya["accion"],
            "objeto_laya":
                laya["objeto"],
            "color_laya":
                laya["color"],
            "prioridad_laya":
                laya["prioridad"],
            "permitido_laya":
                laya["permitido"],

            # Keywords
            "accion_keywords":
                keywords["accion"],
            "objeto_keywords":
                keywords["objeto"],
            "color_keywords":
                keywords["color"],
            "prioridad_keywords":
                keywords["prioridad"],
            "permitido_keywords":
                keywords["permitido"],

            # Sistema final
            "accion_final":
                final["accion"],
            "objeto_final":
                final["objeto"],
            "color_final":
                final["color"],
            "prioridad_final":
                final["prioridad"],
            "permitido_final":
                final["permitido"],

            "degradado":
                respuesta.degradado,
            "metodo":
                respuesta.metodo,
            "detalle":
                respuesta.detalle,

            # Aciertos LAYA
            "laya_accion_ok":
                aciertos_laya["accion"],
            "laya_objeto_ok":
                aciertos_laya["objeto"],
            "laya_color_ok":
                aciertos_laya["color"],
            "laya_prioridad_ok":
                aciertos_laya["prioridad"],
            "laya_permitido_ok":
                aciertos_laya["permitido"],

            # Aciertos keywords
            "keywords_accion_ok":
                aciertos_keywords["accion"],
            "keywords_objeto_ok":
                aciertos_keywords["objeto"],
            "keywords_color_ok":
                aciertos_keywords["color"],
            "keywords_prioridad_ok":
                aciertos_keywords["prioridad"],
            "keywords_permitido_ok":
                aciertos_keywords["permitido"],

            # Aciertos sistema final
            "final_accion_ok":
                aciertos_final["accion"],
            "final_objeto_ok":
                aciertos_final["objeto"],
            "final_color_ok":
                aciertos_final["color"],
            "final_prioridad_ok":
                aciertos_final["prioridad"],
            "final_permitido_ok":
                aciertos_final["permitido"],

            "laya_total_ok":
                (
                    all(
                        aciertos_laya.values()
                    )
                    if laya_disponible
                    else ""
                ),

            "keywords_total_ok":
                all(
                    aciertos_keywords.values()
                ),

            "final_total_ok":
                all(
                    aciertos_final.values()
                ),

            # Tiempos
            "tiempo_cliente_ms":
                tiempo_cliente_ms,

            "tiempo_proceso_ms":
                respuesta.tiempo_proceso_ms,

            "http_total_ms":
                respuesta.http_total_ms,

            "inferencia_laya_ms":
                respuesta.inferencia_laya_ms,

            "rtt_red_ms":
                respuesta.rtt_red_ms,
        }

        resultados.append(
            fila_salida
        )

        print(
            "  final:",
            final,
            "| metodo:",
            respuesta.metodo
        )

    nodo.destroy_node()
    rclpy.shutdown()

    if not resultados:
        print(
            "ERROR: no se obtuvo "
            "ningun resultado."
        )
        sys.exit(1)

    marca = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    salida_csv = (
        BASE
        / f"resultados_item1_{marca}.csv"
    )

    with salida_csv.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        escritor = csv.DictWriter(
            f,
            fieldnames=resultados[0].keys()
        )

        escritor.writeheader()
        escritor.writerows(
            resultados
        )

    # ==========================
    # RESUMEN EXACTITUD
    # ==========================
    campos = [
        "accion",
        "objeto",
        "color",
        "prioridad",
        "permitido",
    ]

    lineas = []

    lineas.append(
        "RESUMEN BENCHMARK ITEM 1"
    )
    lineas.append(
        "=" * 50
    )
    lineas.append(
        f"Frases procesadas: "
        f"{len(resultados)}"
    )

    laya_validas = [
        r for r in resultados
        if r["laya_disponible"]
    ]

    lineas.append(
        f"LAYA disponible: "
        f"{len(laya_validas)}/"
        f"{len(resultados)}"
    )

    lineas.append("")

    lineas.append(
        "EXACTITUD POR CAMPO"
    )
    lineas.append(
        "-" * 50
    )

    for campo in campos:

        # LAYA
        laya_ok = sum(
            1
            for r in laya_validas
            if r[
                f"laya_{campo}_ok"
            ] is True
        )

        # Keywords
        kw_ok = sum(
            1
            for r in resultados
            if r[
                f"keywords_{campo}_ok"
            ] is True
        )

        # Final
        final_ok = sum(
            1
            for r in resultados
            if r[
                f"final_{campo}_ok"
            ] is True
        )

        lineas.append(
            f"{campo.upper():10s} | "
            f"LAYA "
            f"{porcentaje(laya_ok, len(laya_validas)):6.2f}% | "
            f"Keywords "
            f"{porcentaje(kw_ok, len(resultados)):6.2f}% | "
            f"Final "
            f"{porcentaje(final_ok, len(resultados)):6.2f}%"
        )

    lineas.append("")
    lineas.append(
        "EXACTITUD TOTAL "
        "(TODOS LOS CAMPOS)"
    )
    lineas.append(
        "-" * 50
    )

    laya_total_ok = sum(
        1
        for r in laya_validas
        if r["laya_total_ok"] is True
    )

    kw_total_ok = sum(
        1
        for r in resultados
        if r["keywords_total_ok"] is True
    )

    final_total_ok = sum(
        1
        for r in resultados
        if r["final_total_ok"] is True
    )

    lineas.append(
        f"LAYA: "
        f"{porcentaje(laya_total_ok, len(laya_validas)):.2f}%"
    )

    lineas.append(
        f"Keywords: "
        f"{porcentaje(kw_total_ok, len(resultados)):.2f}%"
    )

    lineas.append(
        f"Sistema final: "
        f"{porcentaje(final_total_ok, len(resultados)):.2f}%"
    )

    lineas.append("")
    lineas.append(
        "LATENCIAS"
    )
    lineas.append(
        "-" * 50
    )

    lineas.append(
        resumen_tiempos(
            "Cliente ROS",
            [
                r["tiempo_cliente_ms"]
                for r in resultados
            ]
        )
    )

    lineas.append(
        resumen_tiempos(
            "Proceso nodo",
            [
                r["tiempo_proceso_ms"]
                for r in resultados
            ]
        )
    )

    lineas.append(
        resumen_tiempos(
            "HTTP total",
            [
                r["http_total_ms"]
                for r in resultados
            ]
        )
    )

    lineas.append(
        resumen_tiempos(
            "Inferencia LAYA",
            [
                r["inferencia_laya_ms"]
                for r in resultados
            ]
        )
    )

    lineas.append(
        resumen_tiempos(
            "RTT/overhead estimado",
            [
                r["rtt_red_ms"]
                for r in resultados
            ]
        )
    )

    degradados = sum(
        1
        for r in resultados
        if r["degradado"]
    )

    lineas.append("")
    lineas.append(
        f"Respuestas degradadas/fallback: "
        f"{degradados}/{len(resultados)}"
    )

    salida_resumen = (
        BASE
        / f"resumen_item1_{marca}.txt"
    )

    salida_resumen.write_text(
        "\n".join(lineas) + "\n",
        encoding="utf-8"
    )

    print()
    print(
        "\n".join(lineas)
    )

    print()
    print(
        "CSV guardado en:"
    )
    print(
        salida_csv
    )

    print()
    print(
        "Resumen guardado en:"
    )
    print(
        salida_resumen
    )


if __name__ == "__main__":
    main()
