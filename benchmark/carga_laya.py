#!/usr/bin/env python3

import time
import requests

URL = "http://192.168.56.1:8000/v1/systemone"

payload = {
    "state": "recoge el cubo rojo",
    "lang": "es",
    "model": "typed-decisions",
    "questions": {
        "accion": {
            "type": "choice",
            "instructions": (
                "Selecciona exactamente que accion ordena "
                "realizar la persona al robot."
            ),
            "criteria": {
                "recoger": (
                    "La persona ordena recoger, tomar, "
                    "agarrar o coger un objeto."
                ),
                "depositar": (
                    "La persona ordena colocar, poner, "
                    "llevar o depositar un objeto."
                ),
                "detener": (
                    "La persona ordena detener, parar "
                    "o cancelar el movimiento."
                )
            }
        }
    }
}

sesion = requests.Session()
sesion.trust_env = False

numero = 0

print("Generador de carga LAYA activo.")
print("Detener con Ctrl+C.")
print()

try:
    while True:
        numero += 1
        inicio = time.perf_counter()

        try:
            r = sesion.post(
                URL,
                json=payload,
                timeout=15
            )

            ms = (
                time.perf_counter() - inicio
            ) * 1000.0

            print(
                f"[carga {numero:04d}] "
                f"HTTP={r.status_code} "
                f"tiempo={ms:.1f} ms"
            )

        except Exception as e:
            print(
                f"[carga {numero:04d}] "
                f"ERROR {type(e).__name__}"
            )

        time.sleep(0.5)

except KeyboardInterrupt:
    print()
    print("Carga detenida.")
