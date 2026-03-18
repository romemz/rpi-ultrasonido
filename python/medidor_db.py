import subprocess
import pymysql

# Ejecutar el sensor
resultado = subprocess.check_output(
    ["python3","/var/www/html/rpi-ultrasonido/python/ultrasonido.py"]
).decode().strip()

# Extraer solo el número de la distancia
distancia = float(resultado)

# Altura total del tinaco en cm  ← CAMBIADO de 25 a 22
altura_tinaco = 22

# Calcular porcentaje
porcentaje = int((1 - distancia/altura_tinaco) * 100)

# Limitar valores
if porcentaje < 0:
    porcentaje = 0

if porcentaje > 100:
    porcentaje = 100

# Determinar estado
if porcentaje >= 70:
    estado = "Lleno"
elif porcentaje >= 30:
    estado = "Medio"
else:
    estado = "Bajo"

# Conectar a la base de datos
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
