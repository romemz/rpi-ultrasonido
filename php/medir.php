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
require_once _DIR_ . '/db.php';
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
                'INSERT INTO mediciones (distancia, porcentaje, estado)
                 VALUES (:distancia, :porcentaje, :estado)'
            );
            $stmt->execute([
                ':distancia'  => $distancia,
                ':porcentaje' => $porcentaje,
                ':estado'     => $estado,
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
        $hoy  = date('Y-m-d');
        $stmt = $pdo->prepare(
            'SELECT
                COUNT(*)        AS total,
                ROUND(AVG(porcentaje)) AS promedio,
                MAX(porcentaje) AS maximo,
                MIN(porcentaje) AS minimo
             FROM mediciones
             WHERE DATE(fecha) = :hoy'
        );
        $stmt->execute([':hoy' => $hoy]);
        $row = $stmt->fetch();
        if ($row && $row['total'] > 0) {
            $resumen = [
                'total'    => (int) $row['total'],
                'promedio' => (int) $row['promedio'],
                'maximo'   => (int) $row['maximo'],
                'minimo'   => (int) $row['minimo'],
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