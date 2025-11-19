<?php
// Migration script: create SQLite DB from schema and import existing users.json
require 'db.php';

echo "Connecting to MySQL and importing users.json (if present)...\n";
$pdo = get_db();

$users_file = __DIR__ . '/users.json';
if (file_exists($users_file)) {
    echo "Importing users from users.json...\n";
    $arr = json_decode(file_get_contents($users_file), true);
    if (!is_array($arr)) {
        echo "users.json invalid or empty.\n";
    } else {
        $count = 0;
        foreach ($arr as $u) {
            if (!isset($u['username']) || !isset($u['password'])) continue;
            $username = $u['username'];
            $password_hash = $u['password'];
            $email = $u['email'] ?? null;
            $display = $u['display_name'] ?? null;
            // check existing
            $stmt = $pdo->prepare('SELECT id FROM users WHERE lower(username)=lower(:u) LIMIT 1');
            $stmt->execute([':u' => $username]);
            $exists = $stmt->fetch();
            if ($exists) continue;
            try {
                $stmt = $pdo->prepare('INSERT INTO users (username,password_hash,email,display_name,is_admin,created_at) VALUES (:u,:p,:e,:d,0,NOW())');
                $stmt->execute([':u'=>$username,':p'=>$password_hash,':e'=>$email,':d'=>$display]);
                $count++;
            } catch (Exception $e) {
                // skip on error
            }
        }
        echo "Imported $count users.\n";
    }
} else {
    echo "No users.json found to import.\n";
}

echo "Migration complete.\n";
?>