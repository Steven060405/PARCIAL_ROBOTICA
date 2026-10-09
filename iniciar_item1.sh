#!/usr/bin/env bash

set -eo pipefail

echo "======================================"
echo "   INICIO ITEM 1 - INTERPRETE LAYA"
echo "======================================"
echo

read -rp "IP de LAYA: " LAYA_IP

read -rp "Puerto de LAYA [8000]: " LAYA_PORT
LAYA_PORT="${LAYA_PORT:-8000}"

read -rp "Preset/identificador del profesor [manual_prueba]: " LAYA_PRESET
LAYA_PRESET="${LAYA_PRESET:-manual_prueba}"

read -rp "Modelo LAYA [typed-decisions]: " LAYA_MODEL
LAYA_MODEL="${LAYA_MODEL:-typed-decisions}"

LAYA_URL="http://${LAYA_IP}:${LAYA_PORT}"

echo
echo "Configuracion:"
echo "  URL    = ${LAYA_URL}"
echo "  preset = ${LAYA_PRESET}"
echo "  modelo = ${LAYA_MODEL}"
echo

source /opt/ros/humble/setup.bash
source "${HOME}/parcial_ws/install/setup.bash"

echo "Probando servidor LAYA..."
echo

curl \
  --fail \
  --silent \
  --show-error \
  --connect-timeout 3 \
  --max-time 5 \
  "${LAYA_URL}/health"

echo
echo
echo "LAYA responde correctamente."
echo

mkdir -p "${HOME}/parcial_ws/registros"

FECHA="$(date +%Y%m%d_%H%M%S)"

REGISTRO="${HOME}/parcial_ws/registros/config_${FECHA}.txt"

{
    echo "fecha=$(date --iso-8601=seconds)"
    echo "laya_url=${LAYA_URL}"
    echo "laya_ip=${LAYA_IP}"
    echo "laya_port=${LAYA_PORT}"
    echo "laya_preset=${LAYA_PRESET}"
    echo "laya_model=${LAYA_MODEL}"
    echo "timeout_s=5.0"
} > "${REGISTRO}"

echo "Configuracion guardada en:"
echo "${REGISTRO}"
echo

exec ros2 run parcial_interprete interprete_ordenes \
  --ros-args \
  -p laya_url:="${LAYA_URL}" \
  -p laya_preset:="${LAYA_PRESET}" \
  -p laya_model:="${LAYA_MODEL}" \
  -p timeout_s:=5.0
