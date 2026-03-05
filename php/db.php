<?php
/**
 * db.php
 * Medidor Inteligente de Niveles – UTC
 * Conexión a MariaDB
 */

define('DB_HOST', 'localhost');
define('DB_NAME', 'medidor_tinaco');
define('DB_USER', 'root');
define('DB_PASS', '1234');
define('DB_CHARSET', 'utf8mb4');

// Valores de conexión actualizados

function getDB() {
    static $pdo = null;
    if ($pdo === null) {
        try {
            $dsn = 'mysql:host=' . DB_HOST
                 . ';dbname='   . DB_NAME
                 . ';charset='  . DB_CHARSET;
            $pdo = new PDO($dsn, DB_USER, DB_PASS, [
                PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES   => false,
            ]);
        } catch (PDOException $e) {
            // Devuelve null si no hay conexión, medir.php lo maneja
            return null;
        }
    }
    return $pdo;
}