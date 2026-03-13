<?php

header('Content-Type: application/json');

// 1️⃣ Medir sensor e insertar en base de datos
$salida = shell_exec("sudo /usr/bin/python3 /var/www/html/rpi-ultrasonido/python/medidor_db.py 2>&1");

// 2️⃣ Ejecutar sistema de alertas Telegram
shell_exec("sudo /usr/bin/python3 /var/www/html/rpi-ultrasonido/python/monitoreo.py 2>&1");

// Variables
$distancia = 0;
$nivel = 0;
$estado = "Desconocido";

// Leer datos de la salida del sensor
if(preg_match('/Distancia:\s*([0-9.]+)/', $salida, $match)){
    $distancia = floatval($match[1]);
}

if(preg_match('/Nivel:\s*([0-9]+)/', $salida, $match)){
    $nivel = intval($match[1]);
}

if(preg_match('/Estado:\s*([A-Za-z]+)/', $salida, $match)){
    $estado = $match[1];
}

// Respuesta para la app web
echo json_encode([
    "ok" => true,
    "distancia" => $distancia,
    "nivel" => $nivel,
    "porcentaje" => $nivel,
    "estado" => $estado,
    "promedio" => $nivel,
    "maximo" => $nivel,
    "minimo" => $nivel,
    "hora" => date("H:i:s"),
    "texto" => $salida
]);

?>