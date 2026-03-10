#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" 
monitoreo.py
Medidor Inteligente de Niveles – UTC
Ramos Arizpe, Coahuila · 2025

Mide automáticamente cada vez que el cron lo llama,
guarda en MariaDB y escribe estado_tinaco.json para
que el frontend muestre notificaciones push.

Configurar en cron (cada 5 minutos):
  sudo crontab -e
  */5 * * * * /usr/bin/python3 /var/www/html/rpi-ultrasonido/python/monitoreo.py >> /var/log/tinaco_monitoreo.log 2>&1

NO modifica ultrasonido.py ni medidor_db.py
"""

import subprocess
import pymysql
import json
import os
from datetime import datetime

# ══════════════════════════════════════════
#  CONFIGURACIÓN  ← ajusta si es necesario
# ══════════════════════════════════════════
SCRIPT_SENSOR  = '/var/www/html/rpi-ultrasonido/python/medidor_db.py'
PYTHON_BIN     = '/usr/bin/python3'
ARCHIVO_ESTADO = '/var/www/html/rpi-ultrasonido/estado_tinaco.json'

TINACO_ALTO    = 100      # cm del tinaco
TINACO_ID      = 1

DB_HOST = 'localhost'
DB_NAME = 'medidor_tinaco'
DB_USER = 'medidor_app'
DB_PASS = 'medidor2025'   # ← igual que en medir.php

UMBRAL_CRITICO = 25       # % → alerta crítica
UMBRAL_BAJO    = 50       # % → alerta precaución
# ══════════════════════════════════════════


def ejecutar_medidor():
    """Llama a medidor_db.py que ya guarda en BD y devuelve la salida."""
    try:
        resultado = subprocess.check_output(
            ['sudo', PYTHON_BIN, SCRIPT_SENSOR],
            stderr=subprocess.STDOUT,
            timeout=20
        ).decode('utf-8').strip()
        return resultado
    except subprocess.TimeoutExpired:
        print("[ERROR] Timeout al ejecutar el sensor")
        return None
    except subprocess.CalledProcessError as e:
        print(f"[ERROR sensor] {e.output.decode()}")
        return None


def parsear_salida(salida):
    """
    medidor_db.py imprime:
    Distancia: 45.23 cm | Nivel: 54 % | Estado: Medio
    Extrae los valores numéricos y el estado.
    """
    if not salida:
        return None, None, None
    import re
    dist = re.search(r'Distancia:\s*([\d.]+)', salida)
    nivel = re.search(r'Nivel:\s*(\d+)', salida)
    estado_txt = re.search(r'Estado:\s*([A-Za-z]+)', salida)

    distancia   = float(dist.group(1))   if dist   else None
    porcentaje  = int(nivel.group(1))    if nivel  else None
    estado_raw  = estado_txt.group(1)    if estado_txt else None

    # Normalizar estado al esquema de la BD
    mapa = {'Lleno': 'normal', 'Medio': 'bajo', 'Bajo': 'critico'}
    estado_bd = mapa.get(estado_raw, 'normal')

    return distancia, porcentaje, estado_bd


def escribir_estado(distancia, porcentaje, estado, notificar, mensaje):
    datos = {
        "ok":         True,
        "distancia":  distancia,
        "porcentaje": porcentaje,
        "estado":     estado,
        "notificar":  notificar,
        "mensaje":    mensaje,
        "timestamp":  datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    try:
        with open(ARCHIVO_ESTADO, 'w') as f:
            json.dump(datos, f, ensure_ascii=False)
        os.chmod(ARCHIVO_ESTADO, 0o644)
    except Exception as e:
        print(f"[ERROR escritura JSON] {e}")


def leer_estado_prev():
    archivo = ARCHIVO_ESTADO + '.prev'
    if os.path.exists(archivo):
        try:
            with open(archivo) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def guardar_estado_prev(estado):
    archivo = ARCHIVO_ESTADO + '.prev'
    try:
        with open(archivo, 'w') as f:
            json.dump({'estado': estado}, f)
        os.chmod(archivo, 0o644)
    except Exception:
        pass


# ══════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════
def main():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Monitoreo automático")

    salida = ejecutar_medidor()
    if not salida:
        escribir_estado(None, None, 'sin_señal', False, '')
        return

    print(f"[Sensor] {salida}")
    distancia, porcentaje, estado = parsear_salida(salida)

    if distancia is None or porcentaje is None:
        print("[WARN] No se pudo parsear la salida del sensor")
        escribir_estado(None, None, 'sin_señal', False, '')
        return

    # ── Decidir notificación (solo cuando cambia de estado) ────
    prev        = leer_estado_prev()
    estado_prev = prev.get('estado', 'normal')
    notificar   = False
    mensaje     = ''

    if estado == 'critico' and estado_prev != 'critico':
        notificar = True
        mensaje   = f'🚨 ¡Tinaco casi vacío! Nivel crítico: {porcentaje}% — Rellena de inmediato.'
    elif estado == 'bajo' and estado_prev not in ('bajo', 'critico'):
        notificar = True
        mensaje   = f'⚠️ Tinaco a la mitad: {porcentaje}% — Considera rellenarlo pronto.'

    guardar_estado_prev(estado)
    escribir_estado(distancia, porcentaje, estado, notificar, mensaje)

    print(f"[OK] {porcentaje}% | Estado: {estado} | Notificar: {notificar}")


if __name__ == '__main__':
    main()
