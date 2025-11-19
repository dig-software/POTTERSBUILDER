<?php
require 'config.php';
if (session_status() === PHP_SESSION_NONE) {
  session_start();
}

// Require login to access index page
if (empty($_SESSION['user'])) {
  // redirect to login with reason so the login page can show a notice
  header('Location: login.php?reason=auth_required');
  exit;
}
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>POTTERSBUILDER — Query Kenyan History</title>
  <link rel="stylesheet" href="style.css">
  <link rel="icon" href="assets/asset.php?name=favicon" type="image/x-icon">
  <link rel="icon" href="assets/asset.php?name=favicon" type="image/x-icon">
</head>
<?php $body_class = !empty($_SESSION['user']) ? 'with-bg' : ''; ?>
<body class="<?= $body_class ?>">
  <div class="container">
    <h1>POTTERSBUILDER</h1>
    <p class="lead">Ask questions about Kenyan history. This frontend posts to the local API at <code><?php echo htmlspecialchars($API_URL); ?></code>.</p>
    <form method="post" action="query.php">
      <label for="query">Question</label>
      <textarea id="query" name="query" required rows="5" placeholder="e.g. Who was Jomo Kenyatta and why is he important?"></textarea>

      <label for="top_k">Top K (contexts to retrieve)</label>
      <input type="number" id="top_k" name="top_k" value="5" min="1" max="20">

      <label class="checkbox"><input type="checkbox" name="use_openai" value="1"> Use OpenAI synthesis via Python API (server must have OPENAI_API_KEY)</label>
      <label class="checkbox"><input type="checkbox" name="direct_openai" value="1"> Use OpenAI directly from this PHP frontend (server must have OPENAI_API_KEY)</label>
      <label class="checkbox"><input type="checkbox" name="use_web" value="1"> Search the web for additional contexts (uses Python API or web scraper)</label>

      <label for="web_max_sites">Max web sites</label>
      <input type="number" id="web_max_sites" name="web_max_sites" value="3" min="1" max="10">

      <div class="actions">
        <button type="submit">Ask</button>
      </div>
    </form>

    <footer>
      <small>Make sure the POTTERSBUILDER Python API is running (see project README).</small>
    </footer>
  </div>
</body>
</html>
