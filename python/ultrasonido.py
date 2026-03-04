#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pyright: reportMissingImports=false
"""
Tomado en gran parte de:
https://electrosome.com/hc-sr04-ultrasonic-sensor-raspberry-pi/

Formula para calcular la distancia

d = V * (t / 2)
V = velocidad del sonido
t = tiempo, que tarda la señal de ir del emisor al obstaculo y volver al receptor
"""

import importlib
import time

# Importar helper DB (puede lanzar si falta)
from db_sqlite import insert_measurement

GPIO = importlib.import_module("RPi.GPIO")
GPIO.setmode(GPIO.BCM)

TRIG = 23  # pin 23 como TRIG
ECHO = 24  # pin 24 como ECHO
V = 34300  # Velocidad del sonido 34300 cm/s

print("Medicion de la distancia en curso")

GPIO.setup(TRIG, GPIO.OUT)  # TRIG como salida
GPIO.setup(ECHO, GPIO.IN)  # ECHO como entrada

GPIO.output(TRIG, False)  # TRIG en estado bajo
print("Espere que el sensor se estabilice")
time.sleep(2)  # Esperar 2 segundos

GPIO.output(TRIG, True)  # TRIG en estado alto
time.sleep(0.00001)  # Delay de 0.00001 segundos
GPIO.output(TRIG, False)  # TRIG en estado bajo

while GPIO.input(ECHO) == 0:  # Comprueba si ECHO está en estado bajo
    pulse_start = time.time()  # Guarda el tiempo transcurrido en estado bajo

while GPIO.input(ECHO) == 1:  # Comprueba si ECHO está en estado alto
    pulse_end = time.time()  # Guarda el tiempo transcurrido en estado alto

t = pulse_end - pulse_start
distancia = t * (V / 2)
distancia = round(distancia, 2)

try:
    if 2 < distancia < 400:  # Comprueba si la distancia está dentro del rango
        print("Distancia:", distancia, "cm")
        try:
            insert_measurement(distancia, 'ok', f'Distancia: {distancia} cm')
        except Exception as e:
            print("Error guardando en DB:", e)
    else:
        print("Fuera de Rango")
        try:
            insert_measurement(None, 'out_of_range', 'Fuera de Rango')
        except Exception as e:
            print("Error guardando en DB:", e)
finally:
    GPIO.cleanup()  # Limpia los pines
