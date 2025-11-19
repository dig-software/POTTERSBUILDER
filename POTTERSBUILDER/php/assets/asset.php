<?php
// Simple asset proxy for binary files stored in repo root.
// Use safe mapping to avoid arbitrary file reads.
$map = [
  'bg' => __DIR__ . '/../../52a457cc-07d1-48d1-a310-bed3407dfaa3.png',
  'favicon' => __DIR__ . '/../../pottersbuilder.ico',
];
$name = $_GET['name'] ?? '';
if (!isset($map[$name])) {
  header('HTTP/1.1 404 Not Found');
  echo 'Not found';
  exit;
}
$path = $map[$name];
if (!file_exists($path)) {
  header('HTTP/1.1 404 Not Found');
  echo 'Not found';
  exit;
}
$ext = pathinfo($path, PATHINFO_EXTENSION);
switch (strtolower($ext)) {
  case 'png': $ctype = 'image/png'; break;
  case 'jpg': case 'jpeg': $ctype = 'image/jpeg'; break;
  case 'ico': $ctype = 'image/x-icon'; break;
  default: $ctype = 'application/octet-stream';
}
header('Content-Type: ' . $ctype);
header('Cache-Control: public, max-age=86400');
readfile($path);
exit;
?>