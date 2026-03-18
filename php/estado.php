<?php
header('Content-Type: application/json');

// Lee el estado_tinaco.json generado por monitoreo.py (vía cron cada 1 min)
// NO ejecuta el sensor aquí — eso lo hace el cron
$archivo = "/var/www/html/rpi-ultrasonido/estado_tinaco.json";

if (!file_exists($archivo)) {
    echo json_encode([
        "ok"         => false,
        "mensaje"    => "Sin datos aún",
        "porcentaje" => 0
    ]);
    exit;
}

$datos = json_decode(file_get_contents($archivo), true);

if (!$datos) {
    echo json_encode(["ok" => false, "mensaje" => "Error al leer datos"]);
    exit;
}

echo json_encode($datos);
?>
