#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib
import time
import pymysql

GPIO = importlib.import_module("RPi.GPIO")

GPIO.setmode(GPIO.BCM)

TRIG = 23
ECHO = 24
V = 34300

# CONEXION A LA BASE DE DATOS
conexion = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    database="medidor_tinaco"
)

cursor = conexion.cursor()

print("Medicion de la distancia en curso")

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

    porcentaje = int((1 - distancia / 100) * 100)

    if porcentaje < 25:
        estado = "critico"
    elif porcentaje < 50:
        estado = "bajo"
    else:
        estado = "normal"

    print("Distancia:", distancia, "cm")

    sql = """
    INSERT INTO mediciones (tinaco_id, distancia_cm, porcentaje, estado)
    VALUES (%s,%s,%s,%s)
    """

    cursor.execute(sql, (1, distancia, porcentaje, estado))
    conexion.commit()

    print("Dato guardado en la base de datos")

else:
    print("Fuera de rango")

GPIO.cleanup()

cursor.close()
conexion.close()