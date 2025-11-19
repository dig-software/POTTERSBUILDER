-- SQLite schema for POTTERSBUILDER users and preferences
-- Run with: sqlite3 pottersbuilder.db < schema_sqlite.sql

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  email TEXT,
  display_name TEXT,
  is_admin INTEGER NOT NULL DEFAULT 0,
  prefs TEXT, -- JSON stored as TEXT
  created_at DATETIME DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Optional table for audit / query logs (simple)
CREATE TABLE IF NOT EXISTS query_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  query_text TEXT NOT NULL,
  top_k INTEGER,
  use_web INTEGER,
  created_at DATETIME DEFAULT (datetime('now')),
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_query_logs_user ON query_logs(user_id);
