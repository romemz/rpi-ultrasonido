<?php

header('Content-Type: application/json');

$salida = shell_exec("sudo python3 /var/www/html/rpi-ultrasonido/python/medidor_db.py 2>&1");

if($salida){
    echo json_encode([
        "ok"=>true,
        "texto"=>$salida
    ]);
}else{
    echo json_encode([
        "ok"=>false,
        "error"=>"Error al ejecutar el sensor"
    ]);
}

?>