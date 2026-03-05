<?php
/**
 * medir.php
 * Medidor Inteligente de Niveles – UTC
 * Ramos Arizpe, Coahuila · 2025
 *
 * Ejecuta ultrasonido.py, guarda la medición en MariaDB
 * y devuelve JSON al front-end.
 *
 * IMPORTANTE: No modifica ultrasonido.py en absoluto.
 */

// ── Limpiar output previo ──────────────────────────────
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

// ════════════════════════════════════════════════════════
//  CONFIGURACIÓN  ← ajusta estos valores
// ════════════════════════════════════════════════════════
define('SCRIPT_PATH', '/var/www/html/rpi-ultrasonido/python/ultrasonido.py');
define('PYTHON_BIN',  '/usr/bin/python3');
define('TINACO_ALTO', 100);      // Alto real del tinaco en cm
define('TINACO_ID',   1);        // ID del tinaco en la tabla tinacos

// Base de datos
// Usar configuración central en php/db.php
require_once __DIR__ . '/db.php';
// ════════════════════════════════════════════════════════

// ── Verificar script Python ────────────────────────────
if (!file_exists(SCRIPT_PATH)) {
    http_response_code(500);
    ob_end_clean();
    echo json_encode([
        'ok'    => false,
        'error' => 'No se encontró el script de medición',
        'texto' => 'Error: no se encontró el script de medición'
    ]);
    exit;
}

// ── Ejecutar ultrasonido.py ────────────────────────────
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
    echo json_encode(['ok' => false, 'error' => $mensaje, 'texto' => $mensaje]);
    exit;
}

// ── Buscar línea con el resultado ─────────────────────
$lineaMedicion = '';
for ($i = count($salida) - 1; $i >= 0; $i--) {
    $linea = trim($salida[$i]);
    if ($linea === '') continue;

    if (stripos($linea, 'Distancia:')          !== false ||
        stripos($linea, 'Fuera de Rango')       !== false ||
        stripos($linea, 'Sensor no detectado')  !== false) {
        $lineaMedicion = $linea;
        break;
    }
    if ($lineaMedicion === '') $lineaMedicion = $linea;
}

// ── Sensor fuera del tinaco o sin señal ───────────────
if (stripos($lineaMedicion, 'Sensor no detectado') !== false) {
    ob_end_clean();
    echo json_encode([
        'ok'         => true,
        'fuera'      => true,
        'texto'      => '⚠️ Sensor fuera del tinaco o sin obstáculo detectado',
        'distancia'  => null,
        'porcentaje' => null,
        'estado'     => 'sin_señal',
        'timestamp'  => date('Y-m-d H:i:s')
    ]);
    exit;
}

// ── Calcular distancia y porcentaje ───────────────────
$distancia  = null;
$porcentaje = null;
$estado     = 'desconocido';

$match = [];
if (preg_match('/[\d.]+/', $lineaMedicion, $match)) {
    $distancia  = (float) $match[0];
    $porcentaje = max(0, min(100,
        (int) round((1 - $distancia / TINACO_ALTO) * 100)
    ));

    if ($porcentaje <= 25)      $estado = 'critico';
    elseif ($porcentaje <= 50)  $estado = 'bajo';
    else                        $estado = 'normal';
}

// ── Guardar en MariaDB ────────────────────────────────
$dbError = null;

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

    } catch (Exception $e) {
        $dbError = $e->getMessage();
        error_log('[medidor_tinaco] Error BD: ' . $dbError);
    }
}

// ── Respuesta JSON ────────────────────────────────────
ob_end_clean();
echo json_encode([
    'ok'         => true,
    'fuera'      => false,
    'texto'      => $lineaMedicion,
    'distancia'  => $distancia,
    'porcentaje' => $porcentaje,
    'estado'     => $estado,
    'timestamp'  => date('Y-m-d H:i:s'),
    'db_error'   => $dbError,   // null si todo ok; elimina en producción
]);
