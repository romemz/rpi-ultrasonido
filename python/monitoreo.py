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


# ── Rangos de alerta ──────────────────────────────────────────
# lleno   → 85% o más   → "Tinaco casi lleno"  (notificación nueva)
# mitad   → 26% – 50%   → "Tinaco a la mitad"
# bajo    → 1%  – 25%   → "Nivel bajo de agua"
# vacio   → 0%          → "Tinaco SIN AGUA"
# normal  → 51% – 84%   → sin alerta
# ─────────────────────────────────────────────────────────────
def detectar_rango(p):
    if p >= 85:
        return "lleno"
    if p == 0:
        return "vacio"
    if 1 <= p <= 25:
        return "bajo"
    if 26 <= p <= 50:
        return "mitad"
    return None   # 51–84 → normal, sin alerta


def construir_mensaje(tipo, p):
    hora = datetime.now().strftime('%H:%M')
    if tipo == "lleno":
        return f"✅ Tinaco casi lleno — Lleno\nNivel actual: {p}%\n🕐 {hora}"
    if tipo == "mitad":
        return f"⚠️ Tinaco a la mitad\nNivel actual: {p}%\n🕐 {hora}"
    if tipo == "bajo":
        return f"🚨 Nivel bajo de agua\nNivel actual: {p}%\n🕐 {hora}"
    if tipo == "vacio":
        return f"🚫 Tinaco SIN AGUA\nNivel actual: {p}%\n🕐 {hora}"


def main():
    log("=== Monitoreo iniciado ===")

    salida = ejecutar_sensor()
    if not salida:
        log("Sin salida del sensor")
        return

    distancia, porcentaje = parsear_salida(salida)
    if porcentaje is None:
        log("No se pudo parsear la salida")
        return

    log(f"Nivel: {porcentaje}% | Distancia: {distancia} cm")

    # Escribir estado para el frontend
    escribir_estado(distancia, porcentaje)

    prev          = leer_prev()
    alerta_actual = detectar_rango(porcentaje)

    # Enviar Telegram SOLO si el rango CAMBIÓ
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
            log("Nivel normal (51-84%) → sin alerta")

    # Reiniciar alertas bajas si el nivel sube a zona normal (51-84)
    # Las alertas de "lleno" se reinician al bajar de 85
    if 51 <= porcentaje <= 84:
        if prev["alerta"] in ("vacio", "bajo", "mitad"):
            prev["alerta"] = None
            log("Nivel normal → alertas bajas reiniciadas")

    # Reiniciar alerta de lleno cuando baja de 85
    if porcentaje < 85 and prev["alerta"] == "lleno":
        prev["alerta"] = None
        log("Bajó de 85% → alerta de lleno reiniciada")

    prev["ultimo_nivel"] = porcentaje
    guardar_prev(prev)
    log("=== Monitoreo terminado ===")


if __name__ == "__main__":
    main()
