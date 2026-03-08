<?php
/**
 * db.php
 * Medidor Inteligente de Niveles – UTC
 * Conexión a MariaDB
 */

define('DB_HOST', '192.168.0.19');
define('DB_NAME', 'medidor_db');
define('DB_USER', 'medidor_user');
define('DB_PASS', 'medidor2025');
define('DB_CHARSET', 'utf8mb4');

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