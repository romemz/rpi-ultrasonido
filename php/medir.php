<?php

header('Content-Type: application/json');

// 1️⃣ Ejecutar medición (sensor + base de datos)
$salida = shell_exec("sudo /usr/bin/python3 /var/www/html/rpi-ultrasonido/python/medidor_db.py 2>&1");

// 2️⃣ Ejecutar monitoreo en segundo plano (Telegram)
exec("sudo /usr/bin/python3 /var/www/html/rpi-ultrasonido/python/monitoreo.py > /dev/null 2>&1 &");

// Variables
$distancia = 0;
$nivel = 0;
$estado = "Desconocido";

if(preg_match('/Distancia:\s*([0-9.]+)/', $salida, $match)){
    $distancia = floatval($match[1]);
}

if(preg_match('/Nivel:\s*([0-9]+)/', $salida, $match)){
    $nivel = intval($match[1]);
}

if(preg_match('/Estado:\s*([A-Za-z]+)/', $salida, $match)){
    $estado = $match[1];
}

echo json_encode([
    "ok" => true,
    "distancia" => $distancia,
    "nivel" => $nivel,
    "porcentaje" => $nivel,
    "estado" => $estado,
    "hora" => date("H:i:s"),
    "texto" => $salida
]);

?>