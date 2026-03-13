#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import json
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime

SCRIPT_SENSOR = '/var/www/html/rpi-ultrasonido/python/medidor_db.py'
PYTHON_BIN = '/usr/bin/python3'

ARCHIVO_PREV = '/var/www/html/rpi-ultrasonido/estado_tinaco.prev.json'

TELEGRAM_TOKEN = "TU_TOKEN"
TELEGRAM_CHAT_ID = "TU_CHAT_ID"


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def ejecutar_sensor():
    try:
        salida = subprocess.check_output(
            ['sudo', PYTHON_BIN, SCRIPT_SENSOR],
            stderr=subprocess.STDOUT,
            timeout=20
        ).decode().strip()

        return salida

    except Exception as e:
        log(f"ERROR SENSOR: {e}")
        return None


def parsear_salida(salida):

    dist = re.search(r'Distancia:\s*([\d.]+)', salida)
    nivel = re.search(r'Nivel:\s*(\d+)', salida)

    distancia = float(dist.group(1)) if dist else None
    porcentaje = int(nivel.group(1)) if nivel else None

    return distancia, porcentaje


def leer_prev():

    if os.path.exists(ARCHIVO_PREV):

        try:
            with open(ARCHIVO_PREV) as f:
                data = json.load(f)

                return {
                    "alerta": data.get("alerta"),
                    "ultimo_nivel": data.get("ultimo_nivel")
                }

        except:
            pass

    return {
        "alerta": None,
        "ultimo_nivel": None
    }


def guardar_prev(datos):

    with open(ARCHIVO_PREV, "w") as f:
        json.dump(datos, f)


def enviar_telegram(texto):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    datos = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": texto
    }).encode()

    req = urllib.request.Request(url, data=datos)

    urllib.request.urlopen(req)

    log("Mensaje enviado a Telegram")


def detectar_rango(p):

    if 40 <= p <= 50:
        return "mitad"

    if 15 <= p <= 25:
        return "bajo"

    if p <= 5:
        return "vacio"

    return None


def construir_mensaje(tipo, p):

    if tipo == "mitad":
        return f"⚠️ Tinaco a la mitad\nNivel actual {p}%"

    if tipo == "bajo":
        return f"🚨 Tinaco casi vacío\nNivel actual {p}%"

    if tipo == "vacio":
        return f"🚫 Tinaco SIN AGUA\nNivel actual {p}%"


def main():

    log("Monitoreo iniciado")

    salida = ejecutar_sensor()

    if not salida:
        return

    distancia, porcentaje = parsear_salida(salida)

    if porcentaje is None:
        return

    log(f"Nivel actual {porcentaje}%")

    prev = leer_prev()

    alerta_actual = detectar_rango(porcentaje)

    if alerta_actual and alerta_actual != prev["alerta"]:

        mensaje = construir_mensaje(alerta_actual, porcentaje)

        enviar_telegram(mensaje)

        prev["alerta"] = alerta_actual


    if porcentaje > 80:

        prev["alerta"] = None

        log("Tinaco lleno → reinicio de alertas")


    prev["ultimo_nivel"] = porcentaje

    guardar_prev(prev)

    log("Monitoreo terminado")


if __name__ == "__main__":
    main()