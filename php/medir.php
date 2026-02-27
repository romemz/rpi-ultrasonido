<?php
// Ejecuta el script Python encargado de controlar el sensor ultrasonido.
// Importante: el proyecto está en /var/www/html/rpi-ultrasonido

$scriptPath = '/var/www/html/rpi-ultrasonido/python/ultrasonido.py';

if (!file_exists($scriptPath)) {
	http_response_code(500);
	echo 'Error: no se encontro el script de medicion';
	exit;
}

$command = 'python3 ' . escapeshellarg($scriptPath) . ' 2>&1';
$output = [];
$exitCode = 0;
exec($command, $output, $exitCode);

if ($exitCode !== 0) {
	http_response_code(500);
	echo 'Error al medir: ' . implode(' | ', $output);
	exit;
}

echo trim(implode("\n", $output));
?>
