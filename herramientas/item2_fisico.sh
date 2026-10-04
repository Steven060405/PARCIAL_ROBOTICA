#!/usr/bin/env bash
set -eo pipefail

REPO="$HOME/PARCIAL_ROBOTICA"
RESULTADOS="$REPO/resultados_item2"
PID_BROKER="$RESULTADOS/.broker_fisico.pid"
PID_DRIVER="$RESULTADOS/.driver_fisico.pid"

cargar_entorno() {
    source /opt/ros/humble/setup.bash

    if [ -f "$HOME/jetcobot_colcon_ws/install/setup.bash" ]; then
        source "$HOME/jetcobot_colcon_ws/install/setup.bash"
    fi

    if [ ! -f "$REPO/install/setup.bash" ]; then
        echo "ERROR: no existe $REPO/install/setup.bash"
        echo "Primero ejecuta:"
        echo "  cd $REPO"
        echo "  colcon build --symlink-install --packages-select arm_broker_interfaces arm_broker"
        exit 1
    fi

    source "$REPO/install/setup.bash"

    export ROS_DOMAIN_ID=62
    export ROS_LOCALHOST_ONLY=0
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    export ROS_DISCOVERY_SERVER="127.0.0.1:11811"
    export FASTRTPS_DEFAULT_PROFILES_FILE="$HOME/super_client_configuration_file.xml"
}

status_item2() {
    cargar_entorno

    echo "===== NODOS ====="
    ros2 node list 2>/dev/null || true

    echo
    echo "===== /joint_states ====="
    ros2 topic info /joint_states -v 2>/dev/null || true

    echo
    echo "===== /move_arm ====="
    ros2 action info /move_arm 2>/dev/null || true

    echo
    echo "===== PUERTO ====="
    sudo fuser -v /dev/ttyUSB0 2>&1 || true
}

stop_item2() {
    echo "Deteniendo Item 2..."

    echo
    echo "[1/2] Deteniendo driver fisico..."

    DRIVER_PIDS="$(pgrep -f 'sync_plan_nx' || true)"

    if [ -n "$DRIVER_PIDS" ]; then
        echo "PID(s) sync_plan_nx: $DRIVER_PIDS"
        kill -TERM $DRIVER_PIDS 2>/dev/null || true

        for i in $(seq 1 10); do
            sleep 0.3
            pgrep -f 'sync_plan_nx' >/dev/null || break
        done
    fi

    echo
    echo "[2/2] Deteniendo arm_broker..."

    BROKER_PIDS="$(pgrep -f 'arm_broker.*broker' || true)"

    if [ -n "$BROKER_PIDS" ]; then
        echo "PID(s) arm_broker: $BROKER_PIDS"
        kill -TERM $BROKER_PIDS 2>/dev/null || true

        for i in $(seq 1 10); do
            sleep 0.3
            pgrep -f 'arm_broker.*broker' >/dev/null || break
        done
    fi

    rm -f "PIDDRIVER""PID_BROKER"

    echo
    echo "===== VERIFICACION ====="

    if pgrep -f 'sync_plan_nx' >/dev/null; then
        echo "ADVERTENCIA: sync_plan_nx sigue activo"
    else
        echo "sync_plan_nx: detenido"
    fi

    if pgrep -f 'arm_broker.*broker' >/dev/null; then
        echo "ADVERTENCIA: arm_broker sigue activo"
    else
        echo "arm_broker: detenido"
    fi

    echo
    echo "===== PUERTO ====="
    sudo fuser -v /dev/ttyUSB0 2>&1 || true

    echo
    echo "Item 2 detenido."
}

start_item2() {
    cargar_entorno
    mkdir -p "$RESULTADOS"

    echo "=========================================="
    echo " ITEM 2 - DESPLIEGUE FISICO SEGURO"
    echo "=========================================="

    echo
    echo "[1/6] Verificando puerto serial..."

    if sudo fuser /dev/ttyUSB0 >/dev/null 2>&1; then
        echo "ERROR: /dev/ttyUSB0 ya esta siendo utilizado:"
        sudo fuser -v /dev/ttyUSB0 || true
        echo
        echo "No se iniciara nada para evitar conflicto serial."
        exit 1
    fi

    echo "Puerto libre."

    echo
    echo "[2/6] Verificando que no exista otro broker local..."

    if ros2 node list 2>/dev/null | grep -qx "/arm_broker"; then
        echo "ERROR: ya existe /arm_broker en este grafo."
        echo "Ejecuta primero:"
        echo "  $0 stop"
        exit 1
    fi

    echo
    echo "[3/6] Iniciando arm_broker..."

    setsid ros2 run arm_broker broker --ros-args \
        -p politica:=fifo \
        -p paso_max_rad:=1.6 \
        -p duracion_movimiento_s:=1.0 \
        -p pasos_interpolacion:=5 \
        > "$RESULTADOS/item2_broker_runtime.log" 2>&1 &

    BROKER_PID=$!
    echo "BROKERPID">"PID_BROKER"

    OK=0
    for i in $(seq 1 20); do
        sleep 0.5
        if ros2 action info /move_arm 2>/dev/null | grep -q "Action servers: 1"; then
            OK=1
            break
        fi
    done

    if [ "$OK" -ne 1 ]; then
        echo "ERROR: /move_arm no aparecio."
        echo "Revisa:"
        echo "  $RESULTADOS/item2_broker_runtime.log"
        stop_item2
        exit 1
    fi

    echo "Broker listo."

    echo
    echo "[4/6] Leyendo posicion fisica actual..."

    Q_REAL="$(
python3 - <<'PY'
from pymycobot.mycobot import MyCobot
import math
import time
import sys

mc = MyCobot('/dev/ttyUSB0', 1000000)
time.sleep(0.4)

q = mc.get_angles()

if not q or len(q) != 6:
    print("ERROR", file=sys.stderr)
    sys.exit(1)

rad = [round(math.radians(v), 6) for v in q]
print("[" + ", ".join(str(v) for v in rad) + "]")
PY
    )"

    echo "q fisico = $Q_REAL"

    echo
    echo "[5/6] Sincronizando broker SIN driver fisico..."

    SYNC_LOG="$RESULTADOS/item2_sync_runtime.log"

    ros2 action send_goal \
        /move_arm \
        arm_broker_interfaces/action/MoveArm \
        "{joint_positions: $Q_REAL, client_id: 'sync_automatica', priority: 5}" \
        --feedback 2>&1 | tee "$SYNC_LOG"

    if ! grep -q "Goal finished with status: SUCCEEDED" "$SYNC_LOG"; then
        echo
        echo "ERROR: no se pudo sincronizar el broker."
        echo "NO se iniciara el driver fisico."
        stop_item2
        exit 1
    fi

    echo
    echo "[6/6] Iniciando UN solo sync_plan_nx..."

    setsid ros2 run jetcobot_driver sync_plan_nx --ros-args \
        -p port:=/dev/ttyUSB0 \
        -p baud:=1000000 \
        -p speed:=10 \
        -p min_period_s:=0.10 \
        -p min_delta_deg:=0.5 \
        > "$RESULTADOS/item2_driver_runtime.log" 2>&1 &

    DRIVER_PID=$!
    echo "DRIVERPID">"PID_DRIVER"

    sleep 2

    echo
    echo "=========================================="
    echo " ITEM 2 DESPLEGADO"
    echo "=========================================="
    echo
    status_item2
}

case "${1:-}" in
    start)
        start_item2
        ;;
    stop)
        stop_item2
        ;;
    status)
        status_item2
        ;;
    *)
        echo "Uso:"
        echo "  $0 start"
        echo "  $0 status"
        echo "  $0 stop"
        exit 1
        ;;
esac
