<<?php

header('Content-Type: application/json');

// Ejecutar monitoreo (esto mide sensor y maneja alertas)
shell_exec("sudo /usr/bin/python3 /var/www/html/rpi-ultrasonido/python/monitoreo.py 2>&1");

// Leer el estado generado
$archivo = "/var/www/html/rpi-ultrasonido/estado_tinaco.json";

if(!file_exists($archivo)){
    echo json_encode([
        "ok"=>false,
        "mensaje"=>"No hay datos",
        "porcentaje"=>0
    ]);
    exit;
}

$datos = json_decode(file_get_contents($archivo), true);

echo json_encode($datos);

?>