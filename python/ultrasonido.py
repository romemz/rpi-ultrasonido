import RPi.GPIO as GPIO
import time
import sys

TRIG = 23
ECHO = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

GPIO.output(TRIG, False)
time.sleep(0.5)

try:

    # Pulso de disparo
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    inicio = time.time()
    timeout = inicio + 0.04

    while GPIO.input(ECHO) == 0:
        inicio = time.time()
        if inicio > timeout:
            print("0")
            GPIO.cleanup()
            sys.exit()

    fin = time.time()
    timeout = fin + 0.04

    while GPIO.input(ECHO) == 1:
        fin = time.time()
        if fin > timeout:
            print("0")
            GPIO.cleanup()
            sys.exit()

    duracion = fin - inicio

    distancia = (duracion * 34300) / 2
    distancia = round(distancia,2)

    print(distancia)

except Exception as e:

    print("0")

finally:

    GPIO.cleanup()