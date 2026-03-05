<?php
/**
 * historial.php
 * Medidor Inteligente de Niveles – UTC
 * Ramos Arizpe, Coahuila · 2025
 *
 * Devuelve en JSON:
 *   - Las últimas N mediciones del tinaco (para el panel Historial)
 *   - El resumen del día: total, promedio, máximo, mínimo, última hora
 *
 * Uso desde el front-end:
 *   GET  php/historial.php              → últimas 8 mediciones + resumen hoy
 *   GET  php/historial.php?limite=20    → últimas 20 mediciones + resumen hoy
 *   GET  php/historial.php?todos=1      → todos los registros de hoy
 */

if (ob_get_level()) ob_end_clean();
ob_start();

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');   // siempre datos frescos

// ════════════════════════════════════════════════════════
//  CONFIGURACIÓN  (debe coincidir con medir.php)
// ════════════════════════════════════════════════════════
define('DB_HOST',  'localhost');
define('DB_NAME',  'medidor_tinaco');
define('DB_USER',  'medidor_user');
define('DB_PASS',  'medidor2025');   // ← igual que en medir.php
define('TINACO_ID', 1);
// ════════════════════════════════════════════════════════

$limite = isset($_GET['todos']) && $_GET['todos'] == '1'
    ? 500
    : max(1, min(100, (int)($_GET['limite'] ?? 8)));

try {
    $pdo = new PDO(
        'mysql:host=' . DB_HOST . ';dbname=' . DB_NAME . ';charset=utf8mb4',
        DB_USER,
        DB_PASS,
        [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_TIMEOUT            => 3,
        ]
    );

    // ── Últimas N mediciones ──────────────────────────
    $stmtHist = $pdo->prepare(
        'SELECT id, distancia_cm, porcentaje, estado,
                DATE_FORMAT(creado_en, "%H:%i:%s") AS hora,
                DATE_FORMAT(creado_en, "%d/%m/%Y") AS fecha
         FROM  mediciones
         WHERE tinaco_id = :tid
         ORDER BY creado_en DESC
         LIMIT :lim'
    );
    $stmtHist->bindValue(':tid', TINACO_ID, PDO::PARAM_INT);
    $stmtHist->bindValue(':lim', $limite,   PDO::PARAM_INT);
    $stmtHist->execute();
    $lecturas = $stmtHist->fetchAll();

    // ── Resumen del día actual ────────────────────────
    $stmtResumen = $pdo->prepare(
        'SELECT
             COUNT(*)                            AS total,
             ROUND(AVG(porcentaje), 0)           AS promedio,
             MAX(porcentaje)                     AS maximo,
             MIN(porcentaje)                     AS minimo,
             DATE_FORMAT(MAX(creado_en), "%H:%i:%s") AS ultima_hora,
             DATE_FORMAT(MAX(creado_en), "%d/%m/%Y")  AS ultima_fecha
         FROM mediciones
         WHERE tinaco_id = :tid
           AND DATE(creado_en) = CURDATE()'
    );
    $stmtResumen->execute([':tid' => TINACO_ID]);
    $resumen = $stmtResumen->fetch();

    // Convertir a tipos correctos
    $resumen['total']    = (int)   $resumen['total'];
    $resumen['promedio'] = $resumen['promedio'] !== null ? (int) $resumen['promedio'] : null;
    $resumen['maximo']   = $resumen['maximo']   !== null ? (int) $resumen['maximo']   : null;
    $resumen['minimo']   = $resumen['minimo']   !== null ? (int) $resumen['minimo']   : null;

    ob_end_clean();
    echo json_encode([
        'ok'      => true,
        'lecturas' => $lecturas,
        'resumen'  => $resumen,
    ]);

} catch (PDOException $e) {
    error_log('[medidor_tinaco] historial.php Error BD: ' . $e->getMessage());
    http_response_code(500);
    ob_end_clean();
    echo json_encode([
        'ok'    => false,
        'error' => 'No se pudo conectar a la base de datos',
    ]);
}
