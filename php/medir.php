<?php
/**
 * medir.php
 * Ejecuta ultrasonido.py, guarda la medición en MariaDB
 * y devuelve JSON al front-end.
 */

// Limpiar output previo
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

// Configuración: usar ruta relativa al repositorio (rpi-ultrasonido-master)
define('PYTHON_BIN',  'python3');
$scriptPath = realpath(__DIR__ . '/../python/ultrasonido.py');
if ($scriptPath === false) {
    // Fallback a la ruta clásica por si no está donde esperamos
    $scriptPath = '/var/www/html/rpi-ultrasonido/python/ultrasonido.py';
}
define('TINACO_ALTO', 100);      // alto real en cm
define('TINACO_ID',   1);

require_once __DIR__ . '/db.php';

// Ejecutar script Python
$comando  = PYTHON_BIN . ' ' . escapeshellarg($scriptPath) . ' 2>&1';
$salida   = [];
$exitCode = 0;
exec($comando, $salida, $exitCode);

if ($exitCode !== 0) {
    $errorStr = implode(' | ', $salida);
    http_response_code(500);
    ob_end_clean();
    echo json_encode(['ok' => false, 'error' => 'Error al ejecutar el sensor', 'detalle' => $errorStr]);
    exit;
}

// Buscar línea con el resultado
$lineaMedicion = '';
for ($i = count($salida) - 1; $i >= 0; $i--) {
    $linea = trim($salida[$i]);
    if ($linea === '') continue;

    if (stripos($linea, 'Distancia:') !== false || stripos($linea, 'Fuera de Rango') !== false || stripos($linea, 'Sensor no detectado') !== false) {
        $lineaMedicion = $linea;
        break;
    }
    if ($lineaMedicion === '') $lineaMedicion = $linea;
}

// Manejo de casos sin señal
if (stripos($lineaMedicion, 'Sensor no detectado') !== false) {
    ob_end_clean();
    echo json_encode([
        'ok'         => true,
        'fuera'      => true,
        'texto'      => '⚠️ Sensor fuera del tinaco o sin obstáculo detectado',
        'distancia'  => null,
        'porcentaje' => null,
        'estado'     => 'sin_señal',
        'timestamp'  => date('Y-m-d H:i:s'),
        'db_saved'   => null,
        'db_msg'     => null,
    ]);
    exit;
}

$distancia  = null;
$porcentaje = null;
$estado     = 'desconocido';

$match = [];
if (preg_match('/[\d.]+/', $lineaMedicion, $match)) {
    $distancia  = (float) $match[0];
    $porcentaje = max(0, min(100, (int) round((1 - $distancia / TINACO_ALTO) * 100)));

    if ($porcentaje <= 25)      $estado = 'critico';
    elseif ($porcentaje <= 50)  $estado = 'bajo';
    else                        $estado = 'normal';
}

$db_saved = null;
$db_msg = null;
if ($distancia !== null) {
    try {
        $pdo = getDB();
        if ($pdo === null) throw new Exception('No hay conexión a la base de datos');
        $pdo->setAttribute(PDO::ATTR_TIMEOUT, 3);

        $stmt = $pdo->prepare(
            'INSERT INTO mediciones (tinaco_id, distancia_cm, porcentaje, estado)
             VALUES (:tinaco_id, :distancia_cm, :porcentaje, :estado)'
        );
        $stmt->execute([
            ':tinaco_id'    => TINACO_ID,
            ':distancia_cm' => $distancia,
            ':porcentaje'   => $porcentaje,
            ':estado'       => $estado,
        ]);

        $db_saved = true;
        $db_msg = 'Guardado correctamente';
    } catch (Exception $e) {
        $db_saved = false;
        $db_msg = $e->getMessage();
        error_log('[medidor_tinaco] Error BD: ' . $db_msg);
    }
}

ob_end_clean();
echo json_encode([
    'ok'         => true,
    'fuera'      => false,
    'texto'      => $lineaMedicion,
    'distancia'  => $distancia,
    'porcentaje' => $porcentaje,
    'estado'     => $estado,
    'timestamp'  => date('Y-m-d H:i:s'),
    'db_saved'   => $db_saved,
    'db_msg'     => $db_msg,
]);
