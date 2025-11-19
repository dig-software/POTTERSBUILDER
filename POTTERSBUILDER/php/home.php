<?php
require 'config.php';
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
?>
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>POTTERSBUILDER — Welcome</title>
  <link rel="stylesheet" href="style.css">
  <link rel="icon" href="assets/asset.php?name=favicon" type="image/x-icon">
</head>
<body>
  <div class="container">
    <h1>Welcome to POTTERSBUILDER</h1>
    <p class="lead">An experimental knowledge assistant focused on Kenyan history.</p>
    <p>This site requires an account to access the full query interface.</p>
    <p>
      <a href="login.php">Login</a> or <a href="register.php">Create an account</a> to get started.
    </p>
    <hr>
    <p style="font-size:0.9em;color:#666;">If you already have the Python API running and want to run queries immediately, sign in and use the query interface.</p>
  </div>
</body>
</html>