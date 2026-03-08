import time
import random
import sys

try:
    import RPi.GPIO as GPIO
    ON_RPI = True
except (ImportError, RuntimeError):
    ON_RPI = False

if not ON_RPI:
    # Entorno de desarrollo: simular una medición entre 5 y 95 cm
    distancia = round(random.uniform(5.0, 95.0), 2)
    print(distancia)
    sys.exit(0)

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

print(distancia)

GPIO.cleanup()