<?php
/**
 * db.php
 * Conexion a MariaDB en la Raspberry Pi
 */

define('DB_HOST', '192.168.0.19'); // IP de la Raspberry
define('DB_NAME', 'medidor_tinaco');
define('DB_USER', 'webuser');
define('DB_PASS', '1234');

function getDB(){

    try{

        $pdo = new PDO(
            "mysql:host=".DB_HOST.";dbname=".DB_NAME.";charset=utf8",
            DB_USER,
            DB_PASS
        );

        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        return $pdo;

    }catch(PDOException $e){

        echo json_encode([
            "ok"=>false,
            "error"=>"Error conectando a la base de datos"
        ]);

        exit;
    }
}
?>