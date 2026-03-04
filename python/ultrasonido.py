#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib
import time
import sys
import mysql.connector

GPIO = importlib.import_module("RPi.GPIO")

GPIO.setmode(GPIO.BCM)

TRIG = 23
ECHO = 24
V = 34300  # Velocidad sonido cm/s

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

GPIO.output(TRIG, False)
time.sleep(2)

GPIO.output(TRIG, True)
time.sleep(0.00001)
GPIO.output(TRIG, False)

while GPIO.input(ECHO) == 0:
    pulse_start = time.time()

while GPIO.input(ECHO) == 1:
    pulse_end = time.time()

t = pulse_end - pulse_start
distancia = round(t * (V / 2), 2)

if 2 < distancia < 400:
    status = "OK"
    measurement_text = f"Distancia: {distancia} cm"
else:
    status = "OUT_OF_RANGE"
    measurement_text = "Fuera de Rango"
    distancia = None

# -------- Conexión MariaDB --------
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="rpi_user",
        password="1234",
        database="rpi_ultrasonido"
    )

    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO measurements (distance_cm, status, raw_output) VALUES (%s, %s, %s)",
        (distancia, status, measurement_text)
    )

    conn.commit()
    cursor.close()
    conn.close()

except Exception as e:
    print("Error DB:", e, file=sys.stderr)

print(measurement_text)
GPIO.cleanup()