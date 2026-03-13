<?php
/**
 * estado.php – Medidor Inteligente de Niveles – UTC
 * Sirve estado_tinaco.json al frontend.
 */
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

$archivo = dirname(__DIR__) . '/estado_tinaco.json';

if (!file_exists($archivo)) {
    echo json_encode([
        'ok'=>false,'notificar'=>false,'mensaje'=>'',
        'porcentaje'=>null,'estado'=>'sin_datos','timestamp'=>null
    ]);
    exit;
}

$datos = json_decode(file_get_contents($archivo), true);
echo json_encode($datos ?: ['ok'=>false,'notificar'=>false,'mensaje'=>'']);
