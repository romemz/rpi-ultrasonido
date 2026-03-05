<?php
/**
 * medir.php
 * Medidor Inteligente de Niveles – UTC
 * Ramos Arizpe, Coahuila · 2025
 *
 * Ejecuta ultrasonido.py, calcula el nivel y
 * guarda cada medición en MariaDB.
 */

// ── Buffer limpio ──────────────────────────────────────────
if (ob_get_level()) ob_end_clean();
ob_start();

// ── Cabeceras ──────────────────────────────────────────────
header('Content-Type: application/json; charset=utf-8');

// Solo POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    ob_end_clean();
    echo json_encode(['ok' => false, 'error' => 'Método no permitido']);
    exit;
}

// ── Configuración ──────────────────────────────────────────
define('SCRIPT_PATH', '/var/www/html/rpi-ultrasonido/python/ultrasonido.py');
define('PYTHON_BIN',  '/usr/bin/python3');
define('TINACO_ALTO', 100); // ← Alto real del tinaco en cm

// ── Conexión BD ────────────────────────────────────────────
require_once __DIR__ . '/db.php';
$pdo = getDB();

// ── Verificar script Python ────────────────────────────────
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

// ── Ejecutar script ────────────────────────────────────────
$comando  = 'sudo -n ' . PYTHON_BIN . ' ' . escapeshellarg(SCRIPT_PATH) . ' 2>&1';
$salida   = [];
$exitCode = 0;
exec($comando, $salida, $exitCode);

// ── Error de ejecución ─────────────────────────────────────
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

// ── Buscar línea con resultado ─────────────────────────────
$lineaMedicion = '';
for ($i = count($salida) - 1; $i >= 0; $i--) {
    $linea = trim($salida[$i]);
    if ($linea === '') continue;
    if (stripos($linea, 'Distancia:')     !== false ||
        stripos($linea, 'Fuera de Rango') !== false) {
        $lineaMedicion = $linea;
        break;
    }
    if ($lineaMedicion === '') $lineaMedicion = $linea;
}

// ── Calcular porcentaje ────────────────────────────────────
$distancia  = null;
$porcentaje = null;
$estado     = 'desconocido';
$guardado   = false;

$match = [];
if (preg_match('/[\d.]+/', $lineaMedicion, $match)) {
    $distancia  = (float) $match[0];
    $porcentaje = max(0, min(100,
        (int) round((1 - $distancia / TINACO_ALTO) * 100)
    ));

    if ($porcentaje <= 25)      $estado = 'critico';
    elseif ($porcentaje <= 50)  $estado = 'bajo';
    else                        $estado = 'normal';

    // ── Guardar en MariaDB ─────────────────────────────────
    if ($pdo !== null) {
        try {
            $stmt = $pdo->prepare(
                'INSERT INTO measurements (distance_cm, status, raw_output)
                 VALUES (:distance_cm, :status, :raw_output)'
            );
            $stmt->execute([
                ':distance_cm' => $distancia,
                ':status'      => $estado,
                ':raw_output'  => $lineaMedicion,
            ]);
            $guardado = true;
        } catch (PDOException $e) {
            // No interrumpe la medición si la BD falla
            $guardado = false;
        }
    }
}

// ── Resumen del día desde BD ───────────────────────────────
$resumen = ['total' => 0, 'promedio' => null, 'maximo' => null, 'minimo' => null];

    if ($pdo !== null) {
        try {
            $hoy = date('Y-m-d');
            $stmt = $pdo->prepare(
                'SELECT
                    COUNT(*) AS total,
                    ROUND(AVG( (1 - COALESCE(distance_cm,0) / :tinaco) * 100 )) AS promedio,
                    MAX( ROUND((1 - COALESCE(distance_cm,0) / :tinaco) * 100) ) AS maximo,
                    MIN( ROUND((1 - COALESCE(distance_cm,0) / :tinaco) * 100) ) AS minimo
                 FROM measurements
                 WHERE DATE(measured_at) = :hoy'
            );
            $stmt->execute([':hoy' => $hoy, ':tinaco' => TINACO_ALTO]);
            $row = $stmt->fetch();
            if ($row && $row['total'] > 0) {
                $resumen = [
                    'total'    => (int) $row['total'],
                    'promedio' => is_null($row['promedio']) ? null : (int) $row['promedio'],
                    'maximo'   => is_null($row['maximo']) ? null : (int) $row['maximo'],
                    'minimo'   => is_null($row['minimo']) ? null : (int) $row['minimo'],
                ];
            }
        } catch (PDOException $e) {
            // Resumen vacío si falla la consulta
        }
    }

// ── Respuesta JSON ─────────────────────────────────────────
ob_end_clean();
echo json_encode([
    'ok'         => true,
    'texto'      => $lineaMedicion,
    'distancia'  => $distancia,
    'porcentaje' => $porcentaje,
    'estado'     => $estado,
    'timestamp'  => date('Y-m-d H:i:s'),
    'guardado'   => $guardado,
    'resumen'    => $resumen,
]);