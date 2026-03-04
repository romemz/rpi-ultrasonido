<?php
/**
 * medir.php
 * Medidor Inteligente de Niveles – UTC
 */

// Limpiar buffer
if (ob_get_level()) ob_end_clean();
ob_start();

header('Content-Type: application/json; charset=utf-8');

// Solo POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    ob_end_clean();
    echo json_encode(['ok' => false, 'error' => 'Método no permitido']);
    exit;
}

// Rutas
define('SCRIPT_PATH', '/var/www/html/rpi-ultrasonido/python/ultrasonido.py');
define('PYTHON_BIN',  '/var/www/html/rpi-ultrasonido/python/venv/bin/python');
define('TINACO_ALTO', 100); // Ajusta altura real

if (!file_exists(SCRIPT_PATH)) {
    http_response_code(500);
    ob_end_clean();
    echo json_encode([
        'ok' => false,
        'error' => 'No se encontró el script'
    ]);
    exit;
}

// Ejecutar Python
$comando  = 'sudo -n ' . PYTHON_BIN . ' ' . escapeshellarg(SCRIPT_PATH) . ' 2>&1';
$salida   = [];
$exitCode = 0;

exec($comando, $salida, $exitCode);

if ($exitCode !== 0) {
    http_response_code(500);
    ob_end_clean();
    echo json_encode([
        'ok' => false,
        'error' => implode(' | ', $salida)
    ]);
    exit;
}

// Buscar línea medición
$lineaMedicion = '';
for ($i = count($salida) - 1; $i >= 0; $i--) {
    $linea = trim($salida[$i]);
    if ($linea === '') continue;

    if (stripos($linea, 'Distancia:') !== false ||
        stripos($linea, 'Fuera de Rango') !== false) {
        $lineaMedicion = $linea;
        break;
    }
}

$distancia  = null;
$porcentaje = null;
$estado     = 'desconocido';

if (preg_match('/[\d.]+/', $lineaMedicion, $match)) {
    $distancia  = (float) $match[0];
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

ob_end_clean();
echo json_encode([
    'ok'         => true,
    'texto'      => $lineaMedicion,
    'distancia'  => $distancia,
    'porcentaje' => $porcentaje,
    'estado'     => $estado,
    'timestamp'  => date('Y-m-d H:i:s')
]);