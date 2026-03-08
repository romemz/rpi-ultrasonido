<?php

header('Content-Type: application/json');

$salida = shell_exec("sudo python3 /var/www/html/rpi-ultrasonido/python/medidor_db.py 2>&1");

$distancia = 0;
$nivel = 0;
$estado = "Bajo";

preg_match('/Distancia:\s*([0-9.]+)/', $salida, $d);
preg_match('/Nivel:\s*([0-9]+)/', $salida, $n);
preg_match('/Estado:\s*(\w+)/', $salida, $e);

if(isset($d[1])) $distancia = floatval($d[1]);
if(isset($n[1])) $nivel = intval($n[1]);
if(isset($e[1])) $estado = $e[1];

echo json_encode([
    "distancia"=>$distancia,
    "nivel"=>$nivel,
    "estado"=>$estado,

    "porcentaje"=>$nivel,
    "promedio"=>$nivel,
    "maximo"=>$nivel,
    "minimo"=>$nivel,

    "hora"=>date("H:i:s"),
    "ok"=>true
]);

?>