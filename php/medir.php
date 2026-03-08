<?php

header("Content-Type: application/json");

$script = "/var/www/html/rpi-ultrasonido/python/medidor_db.py";

$output = shell_exec("sudo python3 $script");

echo json_encode([
"ok" => true,
"resultado" => $output
]);