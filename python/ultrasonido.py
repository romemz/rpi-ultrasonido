#!/usr/bin/env python3
import importlib
import time

GPIO = importlib.import_module("RPi.GPIO")

GPIO.setmode(GPIO.BCM)

TRIG = 23
ECHO = 24
V = 34300

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
    print(f"Distancia: {distancia}")
else:
    print("Fuera de Rango")

GPIO.cleanup()