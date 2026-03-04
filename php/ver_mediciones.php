<?php
// ver_mediciones.php
// Muestra las últimas mediciones desde la base SQLite en una tabla HTML.

header('Content-Type: text/html; charset=utf-8');

$limit = isset($_GET['limit']) ? (int)$_GET['limit'] : 100;
if ($limit <= 0) $limit = 100;

$dbPath = __DIR__ . '/../data/ultrasonido.db';
if (!file_exists($dbPath)) {
    http_response_code(404);
    echo '<h1>Base de datos no encontrada</h1>';
    exit;
}

try {
    $pdo = new PDO('sqlite:' . $dbPath);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $stmt = $pdo->prepare('SELECT id, measured_at, distance_cm, status, raw_output FROM measurements ORDER BY id DESC LIMIT :limit');
    $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
    $stmt->execute();
    $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
} catch (Exception $e) {
    http_response_code(500);
    echo '<h1>Error al leer la base:</h1><pre>' . htmlspecialchars($e->getMessage()) . '</pre>';
    exit;
}

echo '<!doctype html><meta charset="utf-8"><title>Mediciones</title>';
echo '<h1>Últimas ' . htmlspecialchars($limit) . ' mediciones</h1>';
echo '<table border="1" cellpadding="6" cellspacing="0">';
echo '<tr><th>ID</th><th>Fecha</th><th>Distancia (cm)</th><th>Estado</th><th>Raw</th></tr>';
foreach ($rows as $r) {
    echo '<tr>';
    echo '<td>' . htmlspecialchars($r['id']) . '</td>';
    echo '<td>' . htmlspecialchars($r['measured_at']) . '</td>';
    echo '<td>' . htmlspecialchars($r['distance_cm']) . '</td>';
    echo '<td>' . htmlspecialchars($r['status']) . '</td>';
    echo '<td>' . htmlspecialchars($r['raw_output']) . '</td>';
    echo '</tr>';
}
echo '</table>';
echo '<p><a href="?limit=10">Ver 10</a> · <a href="?limit=50">50</a> · <a href="?limit=200">200</a></p>';

?>
