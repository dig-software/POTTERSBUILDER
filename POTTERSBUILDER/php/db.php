<?php
// Lightweight PDO wrapper for MySQL used by the PHP frontend.
// Usage: require 'db.php'; $db = get_db();

function get_db() {
    static $pdo = null;
    if ($pdo !== null) return $pdo;

    // Read MySQL connection settings from environment variables.
    $host = getenv('PB_MYSQL_HOST') ?: '127.0.0.1';
    $port = getenv('PB_MYSQL_PORT') ?: '3306';
    $db   = getenv('PB_MYSQL_DB') ?: 'pottersbuilder';
    $user = getenv('PB_MYSQL_USER') ?: 'root';
    $pass = getenv('PB_MYSQL_PASS') ?: '';
    $charset = getenv('PB_MYSQL_CHARSET') ?: 'utf8mb4';

    $dsn = "mysql:host={$host};port={$port};dbname={$db};charset={$charset}";
    try {
        $pdo = new PDO($dsn, $user, $pass, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
        // Optional: tune session settings
        try { $pdo->exec("SET SESSION sql_mode=''"); } catch (Exception $e) {}
    } catch (Exception $e) {
        die('DB connection error: ' . $e->getMessage());
    }
    return $pdo;
}

// Convenience: find user by username
function find_user_by_username($username) {
    $pdo = get_db();
    $stmt = $pdo->prepare('SELECT * FROM users WHERE lower(username)=lower(:u) LIMIT 1');
    $stmt->execute([':u' => $username]);
    return $stmt->fetch(PDO::FETCH_ASSOC);
}

// Utility: create user (username, password_hash, email=null, display_name=null)
function create_user($username, $password_hash, $email=null, $display_name=null, $is_admin=0) {
    $pdo = get_db();
    $stmt = $pdo->prepare('INSERT INTO users (username,password_hash,email,display_name,is_admin) VALUES (:u,:p,:e,:d,:a)');
    $stmt->execute([':u'=>$username,':p'=>$password_hash,':e'=>$email,':d'=>$display_name,':a'=>$is_admin]);
    return $pdo->lastInsertId();
}

?>