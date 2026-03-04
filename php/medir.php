<<?php
header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Método no permitido']);
    exit;
}

define('SCRIPT_PATH', '/var/www/html/rpi-ultrasonido/python/ultrasonido.py');
define('PYTHON_BIN',  '/usr/bin/python3');
define('TINACO_ALTO', 100); // Ajusta altura real

if (!file_exists(SCRIPT_PATH)) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'No se encontró el script']);
    exit;
}

$comando  = 'sudo -n ' . PYTHON_BIN . ' ' . escapeshellarg(SCRIPT_PATH) . ' 2>&1';
$salida   = [];
$exitCode = 0;

exec($comando, $salida, $exitCode);

if ($exitCode !== 0) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => implode(' | ', $salida)]);
    exit;
}

$lineaMedicion = '';
for ($i = count($salida) - 1; $i >= 0; $i--) {
    $linea = trim($salida[$i]);
    if ($linea !== '') {
        $lineaMedicion = $linea;
        break;
    }
}

$distancia  = null;
$porcentaje = null;
$estado     = 'desconocido';

if (preg_match('/[\d.]+/', $lineaMedicion, $match)) {
    $distancia  = (float)$match[0];
    $porcentaje = max(0, min(100,
        (int) round((1 - $distancia / TINACO_ALTO) * 100)
    ));

    if ($porcentaje <= 25) {
        $estado = 'critico';
    } elseif ($porcentaje <= 50) {
        $estado = 'bajo';
    } else {
        $estado = 'normal';
    }
}

require_once __DIR__ . '/conexion.php';

$raw = $lineaMedicion;

if ($distancia !== null) {
    $stmt = $conn->prepare(
        "INSERT INTO measurements (distance_cm, status, raw_output)
         VALUES (?, ?, ?)"
    );
    $stmt->bind_param("dss", $distancia, $estado, $raw);
} else {
    $stmt = $conn->prepare(
        "INSERT INTO measurements (distance_cm, status, raw_output)
         VALUES (NULL, ?, ?)"
    );
    $stmt->bind_param("ss", $estado, $raw);
}

$stmt->execute();
$stmt->close();
$conn->close();

echo json_encode([
    'ok'         => true,
    'texto'      => $lineaMedicion,
    'distancia'  => $distancia,
    'porcentaje' => $porcentaje,
    'estado'     => $estado,
    'timestamp'  => date('Y-m-d H:i:s')
]);