import subprocess
import pymysql

resultado = subprocess.check_output(
    ["python3","/var/www/rpi-ultrasonido/python/ultrasonido.py"]
).decode().strip()

distancia = float(resultado)

conexion = pymysql.connect(
    host="localhost",
    user="webuser",
    password="1234",
    database="medidor_tinaco"
)

cursor = conexion.cursor()

sql = "INSERT INTO mediciones (distancia_cm) VALUES (%s)"

cursor.execute(sql,(distancia,))
conexion.commit()

cursor.close()
conexion.close()

print("Distancia guardada:", distancia)