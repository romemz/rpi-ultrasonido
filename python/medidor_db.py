import os
import pymysql
import subprocess
import re

# Ejecutar ultrasonido.py en el mismo repositorio (ruta relativa)
ultra_path = os.path.join(os.path.dirname(__file__), 'ultrasonido.py')
resultado = subprocess.check_output(["python3", ultra_path]).decode()

print(resultado)

match = re.search(r"[\d.]+", resultado)

if match:

    distancia = float(match.group())
    try:
        conexion = pymysql.connect(
            host="192.168.0.19",
            user="webuser",
            password="1234",
            database="medidor_tinaco",
            connect_timeout=5
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

        print("DB_SAVED:OK")
    except Exception as e:
        # Imprimir error de BD para que php pueda detectarlo
        print("DB_SAVED:ERROR:" + str(e))