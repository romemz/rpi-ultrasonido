<?php

header("Content-Type: application/json");

$script = "/var/www/html/rpi-ultrasonido/python/medidor_db.py";

$output = shell_exec("sudo python3 $script 2>&1");

// Separar líneas y detectar marca de guardado en BD (DB_SAVED:...)
$lines = preg_split('/\r\n|\r|\n/', trim($output));
$db_saved = null;
$db_msg = null;

if (!empty($lines)) {
    $last = end($lines);
    if (strpos($last, 'DB_SAVED:') === 0) {
        // Extraer resultado de DB y quitar última línea del resultado impreso
        $parts = explode(':', $last, 3);
        if (isset($parts[1]) && $parts[1] === 'OK') {
            $db_saved = true;
            $db_msg = 'Guardado correctamente';
        } else {
            $db_saved = false;
            $db_msg = isset($parts[2]) ? $parts[2] : 'Error desconocido al guardar';
        }
        // Reconstruir el output sin la línea de DB
        array_pop($lines);
    }
}

$sensor_output = implode("\n", $lines);

// Si la salida del script contiene un documento HTML (p. ej. 404 de Apache),
// devolvemos un JSON de error para evitar mostrar HTML crudo en la UI.
$lower = strtolower($sensor_output);
if (strpos($lower, '<!doctype') !== false || strpos($lower, '<html') !== false || strpos($lower, 'not found') !== false) {
    echo json_encode([
        "ok" => false,
        "error" => 'Recurso no encontrado o error remoto',
        "resultado_raw" => $sensor_output,
        "db_saved" => $db_saved,
        "db_msg" => $db_msg
    ]);
    exit;
}

echo json_encode([
    "ok" => true,
    "resultado" => $sensor_output,
    "db_saved" => $db_saved,
    "db_msg" => $db_msg
]);