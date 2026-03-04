<?php
$host = "localhost";
$user = "rpi_user";
$pass = "1234";
$db   = "rpi_ultrasonido";

$conn = new mysqli($host, $user, $pass, $db);

if ($conn->connect_error) {
    die("Error de conexión: " . $conn->connect_error);
}
?>