<?php
/**
 * estado.php
 * Medidor Inteligente de Niveles – UTC
 * Ramos Arizpe, Coahuila · 2025
 *
 * Endpoint GET → devuelve el estado_tinaco.json generado por monitoreo.py.
 * El frontend lo consulta cada 60 s para notificaciones push.
 *
 * Ruta en el proyecto: php/estado.php
 */

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

// El JSON vive en la raíz del proyecto, un nivel arriba de php/
$archivo = dirname(__DIR__) . '/estado_tinaco.json';

if (!file_exists($archivo)) {
    echo json_encode([
        'ok'         => false,
        'notificar'  => false,
        'mensaje'    => '',
        'porcentaje' => null,
        'estado'     => 'sin_datos',
        'timestamp'  => null
    ]);
    exit;
}

$datos = json_decode(file_get_contents($archivo), true);

if (!$datos) {
    echo json_encode(['ok' => false, 'notificar' => false, 'mensaje' => '']);
    exit;
}

echo json_encode($datos);
