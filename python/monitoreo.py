#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
monitoreo.py
Medidor Inteligente de Niveles – UTC
Ramos Arizpe, Coahuila · 2025

Mide automáticamente, guarda en BD, escribe estado_tinaco.json
y manda notificaciones por Telegram cuando el tinaco llega a:
  - 50% (mitad)
  - 25% (casi vacío)
  -  0% (vacío)

Cron cada 5 minutos:
  sudo crontab -e
  */5 * * * * /usr/bin/python3 /var/www/html/rpi-ultrasonido/python/monitoreo.py >> /var/log/tinaco_monitoreo.log 2>&1
"""

import subprocess
import json
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime

# ══════════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ══════════════════════════════════════════════════════════
SCRIPT_SENSOR  = '/var/www/html/rpi-ultrasonido/python/medidor_db.py'
PYTHON_BIN     = '/usr/bin/python3'
ARCHIVO_ESTADO = '/var/www/html/rpi-ultrasonido/estado_tinaco.json'
ARCHIVO_PREV   = '/var/www/html/rpi-ultrasonido/estado_tinaco.prev.json'

# ── Telegram ───────────────────────────────────────────────
# PASO 1: Habla con @BotFather en Telegram → /newbot → copia el token
# PASO 2: Abre t.me/tu_bot → manda cualquier mensaje
# PASO 3: Entra a https://api.telegram.org/bot<TOKEN>/getUpdates
#         y copia el número "id" que aparece en "chat"
TELEGRAM_TOKEN   = '8793840618:AAEOPUkxE9naCj86knQ3dPPIXwTO7roCGz4'    # ← reemplaza
TELEGRAM_CHAT_ID = '8080882382'  # ← reemplaza

# Para varios usuarios o un grupo:
# TELEGRAM_CHAT_ID = ['111111111', '222222222', '-333333333']

# ── Umbrales exactos que disparan notificación ─────────────
UMBRALES = [50, 25, 0]
# ══════════════════════════════════════════════════════════


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def ejecutar_medidor():
    try:
        resultado = subprocess.check_output(
            ['sudo', PYTHON_BIN, SCRIPT_SENSOR],
            stderr=subprocess.STDOUT, timeout=20
        ).decode('utf-8').strip()
        return resultado
    except subprocess.TimeoutExpired:
        log("[ERROR] Timeout al ejecutar el sensor")
        return None
    except subprocess.CalledProcessError as e:
        log(f"[ERROR sensor] {e.output.decode()}")
        return None


def parsear_salida(salida):
    if not salida:
        return None, None, None
    dist_m  = re.search(r'Distancia:\s*([\d.]+)', salida)
    nivel_m = re.search(r'Nivel:\s*(\d+)', salida)
    est_m   = re.search(r'Estado:\s*([A-Za-z]+)', salida)
    distancia  = float(dist_m.group(1))  if dist_m  else None
    porcentaje = int(nivel_m.group(1))   if nivel_m else None
    mapa = {'Lleno': 'normal', 'Medio': 'bajo', 'Bajo': 'critico'}
    estado = mapa.get(est_m.group(1) if est_m else '', 'normal')
    return distancia, porcentaje, estado


def leer_prev():
    if os.path.exists(ARCHIVO_PREV):
        try:
            with open(ARCHIVO_PREV) as f:
                return json.load(f)
        except Exception:
            pass
    return {'umbrales_notificados': []}


def guardar_prev(datos):
    try:
        with open(ARCHIVO_PREV, 'w') as f:
            json.dump(datos, f)
        os.chmod(ARCHIVO_PREV, 0o644)
    except Exception as e:
        log(f"[ERROR] guardar_prev: {e}")


def escribir_estado_json(distancia, porcentaje, estado, notificar, mensaje):
    datos = {
        "ok": True, "distancia": distancia, "porcentaje": porcentaje,
        "estado": estado, "notificar": notificar, "mensaje": mensaje,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    try:
        with open(ARCHIVO_ESTADO, 'w') as f:
            json.dump(datos, f, ensure_ascii=False)
        os.chmod(ARCHIVO_ESTADO, 0o644)
    except Exception as e:
        log(f"[ERROR] escribir_estado_json: {e}")


def enviar_telegram(texto):
    if TELEGRAM_TOKEN == 'AQUI_VA_TU_TOKEN':
        log("[TELEGRAM] Token no configurado — omitiendo")
        return
    ids = TELEGRAM_CHAT_ID if isinstance(TELEGRAM_CHAT_ID, list) else [TELEGRAM_CHAT_ID]
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for chat_id in ids:
        try:
            datos = urllib.parse.urlencode({
                'chat_id': str(chat_id), 'text': texto, 'parse_mode': 'HTML'
            }).encode('utf-8')
            req = urllib.request.Request(url, data=datos, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            with urllib.request.urlopen(req, timeout=10) as resp:
                r = json.loads(resp.read())
                if r.get('ok'):
                    log(f"[TELEGRAM] ✅ Enviado a {chat_id}")
                else:
                    log(f"[TELEGRAM] ❌ Error API: {r}")
        except Exception as e:
            log(f"[TELEGRAM] ❌ Excepción ({chat_id}): {e}")


def construir_mensaje(porcentaje):
    hora  = datetime.now().strftime('%H:%M')
    fecha = datetime.now().strftime('%d/%m/%Y')
    if porcentaje <= 5:
        emoji  = '🚫'
        titulo = '¡TINACO SIN AGUA!'
        detalle = 'El tinaco no tiene agua.'
    elif porcentaje <= 25:
        emoji  = '🚨'
        titulo = 'Tinaco casi vacío'
        detalle = f'El tinaco está al <b>{porcentaje}%</b> de capacidad.'
    else:
        emoji  = '⚠️'
        titulo = 'Tinaco a la mitad'
        detalle = f'El tinaco está al <b>{porcentaje}%</b> de capacidad.'
    return (
        f"{emoji} <b>Medidor de Tinaco – UTC</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>{titulo}</b>\n"
        f"{detalle}\n"
        f"📏 Nivel: <b>{porcentaje}%</b>\n"
        f"🕐 {fecha} a las {hora}\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"<i>Universidad Tecnológica de Coahuila</i>"
    )


def main():
    log("=== Monitoreo automático iniciado ===")

    salida = ejecutar_medidor()
    if not salida:
        escribir_estado_json(None, None, 'sin_señal', False, '')
        return

    log(f"Sensor: {salida}")
    distancia, porcentaje, estado = parsear_salida(salida)

    if porcentaje is None:
        log("[WARN] No se pudo parsear la salida")
        escribir_estado_json(None, None, 'sin_señal', False, '')
        return

    log(f"Nivel: {porcentaje}% | Estado: {estado}")

    prev = leer_prev()
    umbrales_notificados = prev.get('umbrales_notificados', [])

    # ── Detectar qué umbral se cruza ──
    umbral_cruzado = None
    for u in sorted(UMBRALES, reverse=True):  # 50, 25, 0
        if porcentaje <= u and u not in umbrales_notificados:
            umbral_cruzado = u
            break

    notificar     = False
    msg_frontend  = ''

    if umbral_cruzado is not None:
        notificar    = True
        msg_telegram = construir_mensaje(porcentaje)
        if porcentaje <= 5:
            msg_frontend = f'🚫 Tinaco sin agua ({porcentaje}%)'
        elif porcentaje <= 25:
            msg_frontend = f'🚨 Tinaco casi vacío — {porcentaje}%'
        else:
            msg_frontend = f'⚠️ Tinaco a la mitad — {porcentaje}%'

        umbrales_notificados.append(umbral_cruzado)
        log(f"[NOTIF] Umbral {umbral_cruzado}% → enviando Telegram")
        enviar_telegram(msg_telegram)

    elif porcentaje > 55 and umbrales_notificados:
        # Tinaco se rellenó → resetear para volver a notificar
        log("[RESET] Tinaco lleno — reseteando umbrales")
        umbrales_notificados = []

    guardar_prev({'umbrales_notificados': umbrales_notificados})
    escribir_estado_json(distancia, porcentaje, estado, notificar, msg_frontend)
    log(f"=== Finalizado | Umbrales notificados: {umbrales_notificados} ===")


if __name__ == '__main__':
    main()
