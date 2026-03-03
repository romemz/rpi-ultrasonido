<?php
header('Content-Type: text/plain; charset=UTF-8');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo 'Método no permitido';
    exit;
}

$pythonScript = realpath(__DIR__ . '/../python/ultrasonido.py');

if ($pythonScript === false || !file_exists($pythonScript)) {
    http_response_code(500);
    echo 'No se encontró el script de medición';
    exit;
}

$pythonCandidates = ['/usr/bin/python3', 'python3'];
$output = [];
$exitCode = 1;
$ran = false;

foreach ($pythonCandidates as $pythonBin) {
    $output = [];
    $exitCode = 1;
    $command = escapeshellcmd($pythonBin) . ' ' . escapeshellarg($pythonScript) . ' 2>&1';

    exec($command, $output, $exitCode);

    if (!empty($output) || $exitCode === 0) {
        $ran = true;
        break;
    }
}

if (!$ran || empty($output)) {
    http_response_code(500);
    echo 'No se pudo ejecutar la medición';
    exit;
}

$lineas = array_values(array_filter(array_map('trim', $output), static function ($linea) {
    return $linea !== '';
}));

if (empty($lineas)) {
    http_response_code(500);
    echo 'Sin respuesta del sensor';
    exit;
}

$ultimo = end($lineas);

echo $ultimo;
