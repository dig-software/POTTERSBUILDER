<?php
session_start();
require 'config.php';
require 'db.php';
if (session_status() === PHP_SESSION_NONE) {
  session_start();
}

$error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
  $username = trim($_POST['username'] ?? '');
  $password = $_POST['password'] ?? '';
  if ($username === '' || $password === '') {
    $error = 'Please provide username and password.';
  } else {
    // check via DB
    $existing = find_user_by_username($username);
    if ($existing) {
      $error = 'Username already taken.';
    } else {
      $hash = password_hash($password, PASSWORD_DEFAULT);
      try {
        create_user($username, $hash, null, null, 0);
                // After successful registration, redirect to the login page with a success flag
                header('Location: login.php?registered=1');
        exit;
      } catch (Exception $e) {
        $error = 'Error creating user: ' . $e->getMessage();
      }
    }
  }
}
?>
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Register — POTTERSBUILDER</title>
  <link rel="stylesheet" href="style.css">
  <link rel="icon" href="assets/asset.php?name=favicon" type="image/x-icon">
</head>
<?php $body_class = !empty($_SESSION['user']) ? 'with-bg' : ''; ?>
<body class="<?= $body_class ?>">
<div class="container">
  <h1>Register</h1>
  <?php if ($error): ?>
    <div class="error"><?= htmlspecialchars($error) ?></div>
  <?php endif; ?>
  <form method="post">
    <label for="username">Username</label>
    <input id="username" name="username" required>

    <label for="password">Password</label>
    <input id="password" name="password" type="password" required>

    <div class="actions">
      <button type="submit">Create account</button>
      &nbsp; <a href="index.php">Cancel</a>
    </div>
  </form>
</div>
</body>
</html>