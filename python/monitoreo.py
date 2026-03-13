#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import json
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime

# ───────── CONFIGURACIÓN ─────────

SCRIPT_SENSOR = '/var/www/html/rpi-ultrasonido/python/medidor_db.py'
PYTHON_BIN = '/usr/bin/python3'

ARCHIVO_ESTADO = '/var/www/html/rpi-ultrasonido/estado_tinaco.json'
ARCHIVO_PREV = '/var/www/html/rpi-ultrasonido/estado_tinaco.prev.json'

TELEGRAM_TOKEN = "8793840618:AAEOPUkxE9naCj86knQ3dPPIXwTO7roCGz4"
TELEGRAM_CHAT_ID = "-5244203258"

UMBRALES = [50,25,0]

# ───────── LOG ─────────

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# ───────── SENSOR ─────────

def ejecutar_medidor():

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


# ───────── PARSEAR ─────────

def parsear_salida(salida):

    if not salida:
        return None,None,None

    dist = re.search(r'Distancia:\s*([\d.]+)',salida)
    nivel = re.search(r'Nivel:\s*(\d+)',salida)
    estado = re.search(r'Estado:\s*([A-Za-z]+)',salida)

    distancia = float(dist.group(1)) if dist else None
    porcentaje = int(nivel.group(1)) if nivel else None

    estado_txt = estado.group(1) if estado else "Normal"

    return distancia,porcentaje,estado_txt


# ───────── ARCHIVOS ─────────

def leer_prev():

    if os.path.exists(ARCHIVO_PREV):

        try:
            with open(ARCHIVO_PREV) as f:
                return json.load(f)
        except:
            pass

    return {"umbrales_notificados":[]}


def guardar_prev(datos):

    try:
        with open(ARCHIVO_PREV,"w") as f:
            json.dump(datos,f)
    except Exception as e:
        log(f"ERROR GUARDAR: {e}")


# ───────── TELEGRAM ─────────

def enviar_telegram(texto):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:

        datos = urllib.parse.urlencode({
            "chat_id":TELEGRAM_CHAT_ID,
            "text":texto,
            "parse_mode":"HTML"
        }).encode()

        req = urllib.request.Request(url,data=datos)

        with urllib.request.urlopen(req) as resp:

            r = json.loads(resp.read())

            if r.get("ok"):
                log("Mensaje enviado a Telegram")
            else:
                log(f"Error Telegram: {r}")

    except Exception as e:

        log(f"Error enviando Telegram: {e}")


# ───────── MENSAJE ─────────

def construir_mensaje(p):

    fecha = datetime.now().strftime("%d/%m/%Y")
    hora = datetime.now().strftime("%H:%M")

    if p <= 5:

        emoji="🚫"
        texto="TINACO SIN AGUA"

    elif p <= 25:

        emoji="🚨"
        texto="TINACO CASI VACÍO"

    else:

        emoji="⚠️"
        texto="TINACO A LA MITAD"

    return f"""
{emoji} Medidor de Tinaco UTC

{texto}

Nivel actual: {p}%

Fecha: {fecha}
Hora: {hora}
"""


# ───────── MAIN ─────────

def main():

    log("Monitoreo iniciado")

    salida = ejecutar_medidor()

    if not salida:
        log("No se pudo leer sensor")
        return

    distancia,porcentaje,estado = parsear_salida(salida)

    if porcentaje is None:
        log("No se detectó porcentaje")
        return


    log(f"Nivel detectado: {porcentaje}%")

    prev = leer_prev()

    umbrales = prev["umbrales_notificados"]

    umbral = None

    for u in UMBRALES:

        if porcentaje <= u and u not in umbrales:

            umbral = u
            break


    # SI ES LA PRIMERA VEZ MANDA MENSAJE
    if not umbrales:

        enviar_telegram(f"📡 Sistema de monitoreo iniciado\nNivel actual: {porcentaje}%")

        umbrales.append(100)

        guardar_prev({"umbrales_notificados":umbrales})


    if umbral is not None:

        mensaje = construir_mensaje(porcentaje)

        enviar_telegram(mensaje)

        umbrales.append(umbral)

        guardar_prev({"umbrales_notificados":umbrales})


    # reset cuando se llena
    if porcentaje > 80:

        guardar_prev({"umbrales_notificados":[]})


    log("Monitoreo finalizado")


if __name__=="__main__":
    main()