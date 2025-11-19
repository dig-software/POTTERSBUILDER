<?php
require 'config.php';
if (session_status() === PHP_SESSION_NONE) {
  session_start();
}

$query = trim($_POST['query'] ?? '');
$top_k = isset($_POST['top_k']) ? intval($_POST['top_k']) : 5;
$use_openai = (isset($_POST['use_openai']) && $_POST['use_openai']) ? true : false;

if ($query === '') {
    header('Location: index.php');
    exit;
}

$use_web = (isset($_POST['use_web']) && $_POST['use_web']) ? true : false;
$web_max_sites = isset($_POST['web_max_sites']) ? intval($_POST['web_max_sites']) : 3;

$payload = array(
  'query' => $query,
  'top_k' => $top_k,
  'use_openai' => $use_openai,
  'use_web' => $use_web,
  'web_max_sites' => $web_max_sites,
);

$ch = curl_init($API_URL);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type: application/json'));
curl_setopt($ch, CURLOPT_POST, true);

// Force retrieval-only call to the Python backend so we get contexts
$api_payload = $payload;
$api_payload['use_openai'] = false;
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($api_payload));

$response = curl_exec($ch);
$httpcode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$err = curl_error($ch);
curl_close($ch);

// If the user asked to call OpenAI directly, and we have a key, do a grounded synthesis
$direct_openai = (isset($_POST['direct_openai']) && $_POST['direct_openai']) ? true : false;
if ($direct_openai) {
  if (empty($OPENAI_API_KEY)) {
    $error_msg = 'Direct OpenAI requested but OPENAI_API_KEY is not set on the server.';
    $response = null;
  } else {
    // Parse backend response to extract contexts
    $api_data = null;
    if ($response !== false) {
      $api_data = json_decode($response, true);
      if (json_last_error() !== JSON_ERROR_NONE) {
        $error_msg = 'Invalid JSON from backend API when fetching contexts.';
      }
    } else {
      $error_msg = 'Backend API request failed: ' . $err;
    }

    $contexts = array();
    if (is_array($api_data) && isset($api_data['contexts']) && is_array($api_data['contexts'])) {
      $contexts = $api_data['contexts'];
    }

    // Build system prompt from template if available
    $system = "You are an assistant. Answer concisely using only the provided contexts. If not present, say you don't know.";
    if (!empty($PROMPT_TEMPLATE) && file_exists($PROMPT_TEMPLATE)) {
      $t = @file_get_contents($PROMPT_TEMPLATE);
      if ($t !== false && trim($t) !== '') { $system = $t; }
    }

    // Build user message: include contexts labeled by number
    $user_parts = array();
    $user_parts[] = "---CONTEXT---";
    if (!empty($contexts)) {
      foreach ($contexts as $i => $c) {
        $src = isset($c['source']) ? $c['source'] : 'unknown';
        $txt = isset($c['text']) ? $c['text'] : '';
        $user_parts[] = "Source " . ($i+1) . " ($src):\n" . $txt;
      }
    } else {
      $user_parts[] = "(No retrieved contexts returned by backend)";
    }
    $user_parts[] = "---QUESTION---";
    $user_parts[] = $query;
    $user_content = implode("\n\n", $user_parts);

    $messages = array(
      array('role' => 'system', 'content' => $system),
      array('role' => 'user', 'content' => $user_content),
    );

    $openai_payload = json_encode(array('model' => 'gpt-3.5-turbo','messages' => $messages,'max_tokens'=>400));
    $ch2 = curl_init('https://api.openai.com/v1/chat/completions');
    curl_setopt($ch2, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch2, CURLOPT_HTTPHEADER, array('Content-Type: application/json','Authorization: Bearer ' . $OPENAI_API_KEY));
    curl_setopt($ch2, CURLOPT_POST, true);
    curl_setopt($ch2, CURLOPT_POSTFIELDS, $openai_payload);
    $oresp = curl_exec($ch2);
    $ohttp = curl_getinfo($ch2, CURLINFO_HTTP_CODE);
    $oerr = curl_error($ch2);
    curl_close($ch2);
    if ($oresp === false) {
      $error_msg = 'OpenAI request failed: ' . $oerr;
      $response = null;
    } else {
      $ojson = json_decode($oresp, true);
      if (json_last_error() !== JSON_ERROR_NONE) {
        $error_msg = 'Invalid JSON from OpenAI: ' . substr($oresp,0,2000);
        $response = null;
      } else {
        $answer_text = null;
        if (isset($ojson['choices'][0]['message']['content'])) {
          $answer_text = $ojson['choices'][0]['message']['content'];
        } elseif (isset($ojson['choices'][0]['text'])) {
          $answer_text = $ojson['choices'][0]['text'];
        }
        $resp_data = array('query'=>$query, 'answer'=>$answer_text, 'contexts'=>$contexts);
        $response = json_encode($resp_data);
        $httpcode = $ohttp;
      }
    }
  }
}

  $resp_data = null;
  $error_msg = null;
  if ($response === false) {
    $error_msg = 'Request failed: ' . $err;
  } else {
    // Try to decode JSON; on failure include raw body for debugging
    $resp_data = json_decode($response, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
      $trimmed = substr($response, 0, 2000);
      $error_msg = "Invalid JSON response from API. HTTP code: $httpcode. Raw response (truncated 2000 chars):\n" . $trimmed;
    } elseif ($httpcode < 200 || $httpcode >= 300) {
      $err_detail = is_array($resp_data) && isset($resp_data['detail']) ? $resp_data['detail'] : $response;
      $error_msg = "API returned status $httpcode: $err_detail";
    }
  }

?>
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Results — POTTERSBUILDER</title>
  <link rel="stylesheet" href="style.css">
  <link rel="icon" href="assets/asset.php?name=favicon" type="image/x-icon">
</head>
<?php $body_class = !empty($_SESSION['user']) ? 'with-bg' : ''; ?>
<body class="<?= $body_class ?>">
  <div class="container">
    <h1>Query results</h1>
    <p><a href="index.php">← New query</a></p>

    <?php if ($error_msg): ?>
      <div class="error"><?= htmlspecialchars($error_msg) ?></div>
    <?php else: ?>
      <h2>Question</h2>
      <p><?= nl2br(htmlspecialchars($query)) ?></p>

      <?php if (!empty($resp_data['answer'])): ?>
        <h3>Answer</h3>
        <div class="answer"><?= nl2br(htmlspecialchars($resp_data['answer'])) ?></div>
      <?php else: ?>
        <div class="note">No synthesized answer returned; showing retrieved contexts.</div>
      <?php endif; ?>

      <?php if (!empty($resp_data['contexts'])): ?>
        <h3>Retrieved Contexts</h3>
        <ol class="contexts">
          <?php foreach ($resp_data['contexts'] as $c): ?>
            <li>
              <div class="ctx-source"><?= htmlspecialchars($c['source'] ?? 'unknown') ?> <span class="score">(score: <?= htmlspecialchars(round($c['score'],4)) ?>)</span></div>
              <div class="ctx-text"><?= nl2br(htmlspecialchars(mb_substr($c['text'],0,2000))) ?></div>
            </li>
          <?php endforeach; ?>
        </ol>
      <?php else: ?>
        <div>No contexts returned.</div>
      <?php endif; ?>
    <?php endif; ?>

  </div>
</body>
</html>
