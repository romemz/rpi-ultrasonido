#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import json
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime

SCRIPT_SENSOR  = '/var/www/html/rpi-ultrasonido/python/medidor_db.py'
PYTHON_BIN     = '/usr/bin/python3'
ARCHIVO_PREV   = '/var/www/html/rpi-ultrasonido/estado_tinaco.prev.json'
ARCHIVO_ESTADO = '/var/www/html/rpi-ultrasonido/estado_tinaco.json'

TELEGRAM_TOKEN   = "8793840618:AAEOPUkxE9naCj86knQ3dPPIXwTO7roCGz4"
TELEGRAM_CHAT_ID = "-5244203258"


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def ejecutar_sensor():
    try:
        salida = subprocess.check_output(
            [PYTHON_BIN, SCRIPT_SENSOR],
            stderr=subprocess.STDOUT,
            timeout=20
        ).decode().strip()
        return salida
    except Exception as e:
        log(f"ERROR SENSOR: {e}")
        return None


def parsear_salida(salida):
    dist   = re.search(r'Distancia:\s*([\d.]+)', salida)
    nivel  = re.search(r'Nivel:\s*(\d+)', salida)
    distancia  = float(dist.group(1))  if dist  else None
    porcentaje = int(nivel.group(1))   if nivel else None
    return distancia, porcentaje


def leer_prev():
    if os.path.exists(ARCHIVO_PREV):
        try:
            with open(ARCHIVO_PREV) as f:
                data = json.load(f)
                return {
                    "alerta":       data.get("alerta"),
                    "ultimo_nivel": data.get("ultimo_nivel")
                }
        except:
            pass
    return {"alerta": None, "ultimo_nivel": None}


def guardar_prev(datos):
    with open(ARCHIVO_PREV, "w") as f:
        json.dump(datos, f)


def escribir_estado(distancia, porcentaje):
    """Escribe estado_tinaco.json para que el frontend lo lea."""
    datos = {
        "ok":         True,
        "distancia":  distancia,
        "porcentaje": porcentaje,
        "timestamp":  datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    try:
        with open(ARCHIVO_ESTADO, 'w') as f:
            json.dump(datos, f, ensure_ascii=False)
        os.chmod(ARCHIVO_ESTADO, 0o644)
    except Exception as e:
        log(f"ERROR escribir estado: {e}")


def enviar_telegram(texto):
    url   = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    datos = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text":    texto
    }).encode()
    req = urllib.request.Request(url, data=datos)
    urllib.request.urlopen(req, timeout=10)
    log("Mensaje enviado a Telegram")


# ── Rangos de alerta ──────────────────────────
# Solo notifica al cruzar 50 %, 25 % y 0 %
# No repite si ya está en el mismo rango
def detectar_rango(p):
    if p == 0:
        return "vacio"
    if 1 <= p <= 25:
        return "bajo"
    if 26 <= p <= 50:
        return "mitad"
    return None   # > 50 → normal, sin alerta


def construir_mensaje(tipo, p):
    hora = datetime.now().strftime('%H:%M')
    if tipo == "mitad":
        return f"⚠️ Tinaco a la mitad\nNivel actual: {p}%\n🕐 {hora}"
    if tipo == "bajo":
        return f"🚨 Nivel bajo de agua\nNivel actual: {p}%\n🕐 {hora}"
    if tipo == "vacio":
        return f"🚫 Tinaco SIN AGUA\nNivel actual: {p}%\n🕐 {hora}"


def main():
    log("=== Monitoreo iniciado ===")

    # 1. Ejecutar sensor + guardar en BD
    salida = ejecutar_sensor()
    if not salida:
        log("Sin salida del sensor")
        return

    distancia, porcentaje = parsear_salida(salida)
    if porcentaje is None:
        log("No se pudo parsear la salida")
        return

    log(f"Nivel actual: {porcentaje}% | Distancia: {distancia} cm")

    # 2. Escribir estado para el frontend
    escribir_estado(distancia, porcentaje)

    # 3. Leer estado previo para comparar
    prev = leer_prev()

    # 4. Detectar rango actual
    alerta_actual = detectar_rango(porcentaje)

    # 5. Enviar Telegram SOLO si el rango CAMBIÓ
    if alerta_actual and alerta_actual != prev["alerta"]:
        mensaje = construir_mensaje(alerta_actual, porcentaje)
        try:
            enviar_telegram(mensaje)
        except Exception as e:
            log(f"ERROR Telegram: {e}")
        prev["alerta"] = alerta_actual
        log(f"Alerta enviada: {alerta_actual}")
    else:
        if alerta_actual:
            log(f"Rango '{alerta_actual}' ya notificado → sin duplicado")
        else:
            log("Nivel normal → sin alerta")

    # 6. Si vuelve a estar por encima de 50 % → reiniciar alertas
    if porcentaje >= 51:
        prev["alerta"] = None
        log("Nivel normal → alertas reiniciadas")

    # 7. Guardar estado
    prev["ultimo_nivel"] = porcentaje
    guardar_prev(prev)

    log("=== Monitoreo terminado ===")


if __name__ == "__main__":
    main()
