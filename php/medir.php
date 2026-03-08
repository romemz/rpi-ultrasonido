<?php

header('Content-Type: application/json');

// Ejecutar el script Python
$salida = shell_exec("sudo python3 /var/www/html/rpi-ultrasonido/python/medidor_db.py 2>&1");

// Valores por defecto
$distancia = 0;
$nivel = 0;
$estado = "Desconocido";

// Extraer datos del texto que devuelve Python
if(preg_match('/Distancia:\s*([0-9.]+)/', $salida, $d)){
    $distancia = floatval($d[1]);
}

if(preg_match('/Nivel:\s*([0-9]+)/', $salida, $n)){
    $nivel = intval($n[1]);
}

if(preg_match('/Estado:\s*(\w+)/', $salida, $e)){
    $estado = $e[1];
}

// Hora actual
$hora = date("H:i:s");

// Enviar JSON que espera el frontend
echo json_encode([
    "ok" => true,
    "distancia" => $distancia,
    "nivel" => $nivel,
    "estado" => $estado,
    "hora" => $hora,
    "texto" => "Distancia: $distancia cm | Nivel: $nivel % | Estado: $estado"
]);

?>