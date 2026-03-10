<?php
/**
 * medir.php
 * Medidor Inteligente de Niveles – UTC
 * Ramos Arizpe, Coahuila · 2025
 *
 * Ejecuta medidor_db.py (que ya guarda en MariaDB) y
 * devuelve JSON al frontend con distancia, porcentaje y estado.
 */

header('Content-Type: application/json');

$salida = shell_exec("sudo python3 /var/www/html/rpi-ultrasonido/python/medidor_db.py 2>&1");

$distancia = null;
$nivel     = 0;
$estado    = "normal";
$fuera     = false;

// ── Parsear salida de medidor_db.py ───────────────────
if (preg_match('/Distancia:\s*([0-9.]+)/', $salida, $match)) {
    $distancia = floatval($match[1]);
}
if (preg_match('/Nivel:\s*([0-9]+)/', $salida, $match)) {
    $nivel = intval($match[1]);
}
if (preg_match('/Estado:\s*([A-Za-zÁÉÍÓÚáéíóú]+)/', $salida, $match)) {
    $estadoRaw = $match[1];
    // Normalizar al esquema del frontend
    $mapa = ['Lleno' => 'normal', 'Medio' => 'bajo', 'Bajo' => 'critico'];
    $estado = isset($mapa[$estadoRaw]) ? $mapa[$estadoRaw] : 'normal';
}

// ── Detectar sensor sin señal ─────────────────────────
if ($distancia === null || stripos($salida, 'no detectado') !== false) {
    $fuera = true;
}

echo json_encode([
    "ok"         => true,
    "fuera"      => $fuera,
    "distancia"  => $distancia,
    "nivel"      => $nivel,
    "porcentaje" => $nivel,
    "estado"     => $estado,
    "hora"       => date("H:i:s"),
    "texto"      => $salida
]);
?>
