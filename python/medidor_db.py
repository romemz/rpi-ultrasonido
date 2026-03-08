import subprocess
import pymysql

# Ejecutar el sensor
resultado = subprocess.check_output(
    ["python3","/var/www/html/rpi-ultrasonido/python/ultrasonido.py"]
).decode().strip()

distancia = float(resultado)

# Altura total del tinaco en cm
altura_tinaco = 120

porcentaje = int((1 - distancia/altura_tinaco)*100)

if porcentaje < 0:
    porcentaje = 0

if porcentaje > 100:
    porcentaje = 100

# Estado del tinaco
if porcentaje >= 70:
    estado = "Lleno"
elif porcentaje >= 30:
    estado = "Medio"
else:
    estado = "Bajo"

# Conexión a base de datos
conexion = pymysql.connect(
    host="localhost",
    user="webuser",
    password="1234",
    database="medidor_tinaco"
)

cursor = conexion.cursor()

sql = """
INSERT INTO mediciones
(distancia, porcentaje, estado)
VALUES (%s,%s,%s)
"""

cursor.execute(sql,(distancia,porcentaje,estado))

conexion.commit()

cursor.close()
conexion.close()

print("Distancia:",distancia,"cm | Nivel:",porcentaje,"% | Estado:",estado)