<?php

header('Content-Type: application/json');

// Ejecutar el script Python
$salida = shell_exec("sudo python3 /var/www/html/rpi-ultrasonido/python/medidor_db.py 2>&1");

// Buscar los datos dentro del texto que imprime Python
preg_match('/Distancia:\s*([0-9.]+)/', $salida, $distancia);
preg_match('/Nivel:\s*([0-9]+)/', $salida, $nivel);
preg_match('/Estado:\s*(\w+)/', $salida, $estado);

// Valores seguros si algo falla
$distancia_val = isset($distancia[1]) ? floatval($distancia[1]) : 0;
$nivel_val = isset($nivel[1]) ? intval($nivel[1]) : 0;
$estado_val = isset($estado[1]) ? $estado[1] : "Desconocido";

// Enviar JSON al frontend
echo json_encode([
    "distancia" => $distancia_val,
    "nivel" => $nivel_val,
    "estado" => $estado_val,
    "texto" => $salida
]);

?>