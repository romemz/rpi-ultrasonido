#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import json
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime

# CONFIGURACIÓN
SCRIPT_SENSOR = '/var/www/html/rpi-ultrasonido/python/medidor_db.py'
PYTHON_BIN = '/usr/bin/python3'

ARCHIVO_PREV = '/var/www/html/rpi-ultrasonido/estado_tinaco.prev.json'

TELEGRAM_TOKEN = "8793840618:AAEOPUkxE9naCj86knQ3dPPIXwTO7roCGz4"
TELEGRAM_CHAT_ID = "-5244203258"

UMBRALES = [50,25,0]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


# EJECUTA EL SENSOR
def ejecutar_sensor():

    try:

        salida = subprocess.check_output(
            ['sudo',PYTHON_BIN,SCRIPT_SENSOR],
            stderr=subprocess.STDOUT,
            timeout=20
        ).decode().strip()

        return salida

    except Exception as e:

        log(f"ERROR SENSOR: {e}")
        return None


# PARSEA RESULTADO
def parsear_salida(salida):

    dist = re.search(r'Distancia:\s*([\d.]+)',salida)
    nivel = re.search(r'Nivel:\s*(\d+)',salida)

    distancia = float(dist.group(1)) if dist else None
    porcentaje = int(nivel.group(1)) if nivel else None

    return distancia,porcentaje


# LEE ARCHIVO DE CONTROL
def leer_prev():

    if os.path.exists(ARCHIVO_PREV):

        try:
            with open(ARCHIVO_PREV) as f:
                return json.load(f)
        except:
            pass

    return {"umbrales":[]}


# GUARDA ARCHIVO DE CONTROL
def guardar_prev(datos):

    with open(ARCHIVO_PREV,"w") as f:
        json.dump(datos,f)


# ENVÍA MENSAJE TELEGRAM
def enviar_telegram(texto):

    url=f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    datos=urllib.parse.urlencode({
        "chat_id":TELEGRAM_CHAT_ID,
        "text":texto
    }).encode()

    req=urllib.request.Request(url,data=datos)

    urllib.request.urlopen(req)

    log("Mensaje enviado")


# CONSTRUYE MENSAJE
def construir_mensaje(p):

    if p <= 5:

        return f"🚫 ALERTA\nTinaco SIN AGUA\nNivel actual {p}%"

    elif p <= 25:

        return f"🚨 ALERTA\nTinaco casi vacío\nNivel actual {p}%"

    else:

        return f"⚠️ ALERTA\nTinaco a la mitad\nNivel actual {p}%"


# MAIN
def main():

    log("Monitoreo iniciado")

    salida=ejecutar_sensor()

    if not salida:
        return

    distancia,porcentaje=parsear_salida(salida)

    if porcentaje is None:
        return

    log(f"Nivel actual {porcentaje}%")

    prev=leer_prev()

    umbrales_notificados=prev["umbrales"]


    # DETECTAR UMBRAL
    for u in UMBRALES:

        if porcentaje <= u and u not in umbrales_notificados:

            mensaje=construir_mensaje(porcentaje)

            enviar_telegram(mensaje)

            umbrales_notificados.append(u)

            guardar_prev({"umbrales":umbrales_notificados})

            break


    # SI SE LLENA OTRA VEZ RESETEA
    if porcentaje > 80:

        guardar_prev({"umbrales":[]})

        log("Tinaco lleno → reinicio de alertas")


    log("Monitoreo terminado")


if __name__=="__main__":
    main()