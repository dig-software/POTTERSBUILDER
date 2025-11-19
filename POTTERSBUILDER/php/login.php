<?php
require 'config.php';
require 'db.php';
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

$error = '';
$notice = '';
// Show notices if redirected
if (!empty($_GET['reason']) && $_GET['reason'] === 'auth_required') {
  $notice = 'Please sign in to continue.';
}
if (!empty($_GET['registered']) && $_GET['registered'] === '1') {
  $notice = 'Registration successful. Please sign in.';
}
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['username'] ?? '');
    $password = $_POST['password'] ?? '';
    if ($username === '' || $password === '') {
        $error = 'Please provide username and password.';
    } else {
        $found = find_user_by_username($username);
        if (!$found) {
            $error = 'Invalid username or password.';
        } else {
            $stored = $found['password_hash'] ?? '';
            if (!password_verify($password, $stored)) {
                $error = 'Invalid username or password.';
            } else {
                $_SESSION['user'] = ['username' => $found['username']];
                header('Location: index.php'); exit;
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
  <title>Login — POTTERSBUILDER</title>
  <link rel="stylesheet" href="style.css">
    <link rel="icon" href="assets/asset.php?name=favicon" type="image/x-icon">
</head>
<?php $body_class = !empty($_SESSION['user']) ? 'with-bg' : ''; ?>
<body class="<?= $body_class ?>">
<div class="container">
  <h1>Login</h1>
  <?php if ($notice && !$error): ?>
    <div class="note"><?= htmlspecialchars($notice) ?></div>
  <?php endif; ?>
  <?php if ($error): ?>
    <div class="error"><?= htmlspecialchars($error) ?></div>
  <?php endif; ?>
  <form method="post">
    <label for="username">Username</label>
    <input id="username" name="username" required>

    <label for="password">Password</label>
    <input id="password" name="password" type="password" required>

    <div class="actions">
      <button type="submit">Sign in</button>
      &nbsp; <a href="index.php">Cancel</a>
    </div>
  </form>
</div>
</body>
</html>