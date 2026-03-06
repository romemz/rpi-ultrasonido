import pymysql
import subprocess
import re

resultado = subprocess.check_output(
    ["python3","/var/www/html/rpi-ultrasonido/python/ultrasonido.py"]
).decode()

print(resultado)

match = re.search(r"[\d.]+", resultado)

if match:

    distancia = float(match.group())

    conexion = pymysql.connect(
        host="localhost",
        user="webuser",
        password="1234",
        database="medidor_tinaco"
    )

    cursor = conexion.cursor()

    sql = """
    INSERT INTO mediciones (tinaco_id, distancia_cm)
    VALUES (1,%s)
    """

    cursor.execute(sql,(distancia,))
    conexion.commit()

    cursor.close()
    conexion.close()