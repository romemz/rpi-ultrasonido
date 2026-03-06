<?php

require_once "db.php";

header('Content-Type: application/json');

$distancia = rand(10,90); // prueba de medición

$porcentaje = 100 - $distancia;

if($porcentaje > 100){
    $porcentaje = 100;
}

$estado = "normal";

if($porcentaje <= 25){
    $estado = "critico";
}
elseif($porcentaje <= 50){
    $estado = "bajo";
}

try{

    $pdo = getDB();

    $sql = "INSERT INTO mediciones
            (tinaco_id, distancia_cm, porcentaje, estado)
            VALUES
            (1, :distancia, :porcentaje, :estado)";

    $stmt = $pdo->prepare($sql);

    $stmt->execute([
        ":distancia"=>$distancia,
        ":porcentaje"=>$porcentaje,
        ":estado"=>$estado
    ]);

    echo json_encode([
        "ok"=>true,
        "distancia"=>$distancia,
        "porcentaje"=>$porcentaje,
        "estado"=>$estado
    ]);

}catch(Exception $e){

    echo json_encode([
        "ok"=>false,
        "error"=>$e->getMessage()
    ]);
}
?>