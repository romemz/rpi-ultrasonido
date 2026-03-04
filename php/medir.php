<?php
/**
 * medir.php
 * Medidor Inteligente de Niveles – UTC
 * Ramos Arizpe, Coahuila · 2025
 *
 * Ejecuta ultrasonido.py en la Raspberry Pi y devuelve
 * la medición en formato JSON al front-end.
 */

// ── Limpiar cualquier output previo ───────────────────
// Evita que warnings de PHP o mensajes extra rompan el JSON
if (ob_get_level()) ob_end_clean();
ob_start();

// ── Cabeceras ──────────────────────────────────────────
header('Content-Type: application/json; charset=utf-8');

// Solo aceptar POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    ob_end_clean();
    echo json_encode(['ok' => false, 'error' => 'Método no permitido']);
    exit;
}

// ── Configuración ──────────────────────────────────────
define('SCRIPT_PATH', '/var/www/html/rpi-ultrasonido/python/ultrasonido.py');
define('PYTHON_BIN',  '/usr/bin/python3');
define('TINACO_ALTO', 100); // ← Ajusta al alto real de tu tinaco en cm

// ── Verificar que existe el script Python ──────────────
if (!file_exists(SCRIPT_PATH)) {
    http_response_code(500);
    ob_end_clean();
    echo json_encode([
        'ok'    => false,
        'error' => 'No se encontró el script de medición',
        'texto' => 'Error: no se encontro el script de medicion'
    ]);
    exit;
}

// ── Ejecutar el script ─────────────────────────────────
$comando  = 'sudo -n ' . PYTHON_BIN . ' ' . escapeshellarg(SCRIPT_PATH) . ' 2>&1';
$salida   = [];
$exitCode = 0;
exec($comando, $salida, $exitCode);

// ── Error de ejecución ─────────────────────────────────
if ($exitCode !== 0) {
    $errorStr = implode(' | ', $salida);
    $mensaje  = (stripos($errorStr, 'password is required') !== false ||
                stripos($errorStr, 'sudo:') !== false)
        ? 'Error de permisos: configura sudoers para www-data'
        : 'Error al ejecutar el sensor: ' . $errorStr;

    http_response_code(500);
    ob_end_clean();
    echo json_encode([
        'ok'    => false,
        'error' => $mensaje,
        'texto' => $mensaje
    ]);
    exit;
}

// ── Buscar la línea con el resultado ──────────────────
$lineaMedicion = '';
for ($i = count($salida) - 1; $i >= 0; $i--) {
    $linea = trim($salida[$i]);
    if ($linea === '') continue;

    if (stripos($linea, 'Distancia:')     !== false ||
        stripos($linea, 'Fuera de Rango') !== false) {
        $lineaMedicion = $linea;
        break;
    }

    if ($lineaMedicion === '') {
        $lineaMedicion = $linea;
    }
}

// ── Calcular porcentaje si hay número ─────────────────
$distancia  = null;
$porcentaje = null;
$estado     = 'desconocido';

$match = [];
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

// ── Respuesta JSON ─────────────────────────────────────
// Limpiamos buffer antes de responder
ob_end_clean();
echo json_encode([
    'ok'         => true,
    'texto'      => $lineaMedicion,  // texto plano igual que el original
    'distancia'  => $distancia,      // float o null
    'porcentaje' => $porcentaje,     // 0-100 o null
    'estado'     => $estado,         // 'normal' | 'bajo' | 'critico' | 'desconocido'
    'timestamp'  => date('Y-m-d H:i:s')
]);