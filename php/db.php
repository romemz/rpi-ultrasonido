<?php
/**
 * db.php
 * Conexion a MariaDB en la Raspberry Pi
 */
define('DB_HOST', '192.168.0.19'); // IP de la Raspberry
define('DB_NAME', 'medidor_tinaco');
define('DB_USER', 'webuser');
define('DB_PASS', '1234');
define('DB_CHARSET', 'utf8mb4');

function getDB() {
    static $pdo = null;
    if ($pdo !== null) return $pdo;

    try {
        $dsn = 'mysql:host=' . DB_HOST . ';dbname=' . DB_NAME . ';charset=' . DB_CHARSET;
        $pdo = new PDO($dsn, DB_USER, DB_PASS, [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false,
        ]);
        return $pdo;
    } catch (PDOException $e) {
        error_log('[medidor_tinaco] Error de conexión: ' . $e->getMessage());
        return null;
    }
}

?>