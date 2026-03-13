#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
monitoreo.py
Medidor Inteligente de Niveles – UTC

Mide automáticamente el nivel del tinaco,
guarda estado en JSON y envía notificaciones
por Telegram cuando el nivel baja a:

50%  -> mitad
25%  -> casi vacío
0%   -> vacío
"""

import subprocess
import json
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────

SCRIPT_SENSOR  = '/var/www/html/rpi-ultrasonido/python/medidor_db.py'
PYTHON_BIN     = '/usr/bin/python3'

ARCHIVO_ESTADO = '/var/www/html/rpi-ultrasonido/estado_tinaco.json'
ARCHIVO_PREV   = '/var/www/html/rpi-ultrasonido/estado_tinaco.prev.json'

# TELEGRAM
TELEGRAM_TOKEN   = "8793840618:AAEOPUkxE9naCj86knQ3dPPIXwTO7roCGz4"
TELEGRAM_CHAT_ID = "-5244203258"

UMBRALES = [50,25,0]

# ─────────────────────────────────────────────

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


# ─────────────────────────────────────────────
# EJECUTAR SENSOR
# ─────────────────────────────────────────────

def ejecutar_medidor():

    try:

        salida = subprocess.check_output(
            ['sudo',PYTHON_BIN,SCRIPT_SENSOR],
            stderr=subprocess.STDOUT,
            timeout=20
        ).decode().strip()

        return salida

    except Exception as e:

        log(f"[ERROR SENSOR] {e}")
        return None


# ─────────────────────────────────────────────
# PARSEAR RESULTADO
# ─────────────────────────────────────────────

def parsear_salida(salida):

    if not salida:
        return None,None,None

    dist = re.search(r'Distancia:\s*([\d.]+)',salida)
    niv  = re.search(r'Nivel:\s*(\d+)',salida)
    est  = re.search(r'Estado:\s*([A-Za-z]+)',salida)

    distancia = float(dist.group(1)) if dist else None
    porcentaje = int(niv.group(1)) if niv else None

    mapa = {
        "Lleno":"normal",
        "Medio":"bajo",
        "Bajo":"critico"
    }

    estado = mapa.get(est.group(1) if est else "","normal")

    return distancia,porcentaje,estado


# ─────────────────────────────────────────────
# ARCHIVOS DE CONTROL
# ─────────────────────────────────────────────

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

        log(f"[ERROR GUARDAR] {e}")


# ─────────────────────────────────────────────
# GUARDAR ESTADO JSON
# ─────────────────────────────────────────────

def escribir_estado_json(distancia,porcentaje,estado,notificar,mensaje):

    datos = {
        "ok":True,
        "distancia":distancia,
        "porcentaje":porcentaje,
        "estado":estado,
        "notificar":notificar,
        "mensaje":mensaje,
        "timestamp":datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    try:

        with open(ARCHIVO_ESTADO,"w") as f:
            json.dump(datos,f,ensure_ascii=False)

    except Exception as e:

        log(f"[ERROR JSON] {e}")


# ─────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────

def enviar_telegram(texto):

    if not TELEGRAM_TOKEN:
        log("Token Telegram no configurado")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:

        datos = urllib.parse.urlencode({
            "chat_id":TELEGRAM_CHAT_ID,
            "text":texto,
            "parse_mode":"HTML"
        }).encode()

        req = urllib.request.Request(url,data=datos)

        with urllib.request.urlopen(req,timeout=10) as resp:

            r = json.loads(resp.read())

            if r.get("ok"):
                log("Telegram enviado correctamente")
            else:
                log(f"Error Telegram: {r}")

    except Exception as e:

        log(f"Error Telegram: {e}")


# ─────────────────────────────────────────────
# MENSAJE
# ─────────────────────────────────────────────

def construir_mensaje(p):

    hora = datetime.now().strftime("%H:%M")
    fecha = datetime.now().strftime("%d/%m/%Y")

    if p <= 5:

        emoji="🚫"
        titulo="TINACO SIN AGUA"
        detalle="El tinaco está vacío."

    elif p <= 25:

        emoji="🚨"
        titulo="TINACO CASI VACÍO"
        detalle=f"Nivel actual <b>{p}%</b>"

    else:

        emoji="⚠️"
        titulo="TINACO A LA MITAD"
        detalle=f"Nivel actual <b>{p}%</b>"

    return f"""
{emoji} <b>Medidor de Tinaco – UTC</b>

{titulo}

{detalle}

Nivel: <b>{p}%</b>

{fecha} {hora}
"""


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():

    log("Monitoreo iniciado")

    salida = ejecutar_medidor()

    if not salida:
        escribir_estado_json(None,None,"sin_señal",False,"")
        return

    distancia,porcentaje,estado = parsear_salida(salida)

    if porcentaje is None:

        escribir_estado_json(None,None,"sin_señal",False,"")
        return


    prev = leer_prev()

    umbrales = prev["umbrales_notificados"]

    umbral_cruzado = None

    for u in sorted(UMBRALES,reverse=True):

        if porcentaje <= u and u not in umbrales:

            umbral_cruzado = u
            break


    notificar=False
    mensaje=""


    if umbral_cruzado is not None:

        notificar=True

        msg_telegram = construir_mensaje(porcentaje)

        enviar_telegram(msg_telegram)

        umbrales.append(umbral_cruzado)

        mensaje=f"Alerta nivel {porcentaje}%"

        log(f"Alerta enviada {porcentaje}%")


    elif porcentaje > 55 and umbrales:

        umbrales=[]

        log("Tinaco lleno, reiniciando alertas")


    guardar_prev({"umbrales_notificados":umbrales})

    escribir_estado_json(distancia,porcentaje,estado,notificar,mensaje)


    log("Monitoreo terminado")


if __name__=="__main__":
    main()