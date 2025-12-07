#srlsp-game/src/signperu/persistence/db_manager.py
# db_manager.py
# Gestor de base de datos SQLite como Singleton.
import sqlite3
import threading
import os
from signperu import config

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS games (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS scores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  game_id INTEGER NOT NULL,
  score INTEGER,
  date_played TEXT DEFAULT CURRENT_TIMESTAMP,
  details TEXT,
  FOREIGN KEY(user_id) REFERENCES users(id),
  FOREIGN KEY(game_id) REFERENCES games(id)
);
CREATE TABLE IF NOT EXISTS progress (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  sign TEXT NOT NULL,
  attempts INTEGER DEFAULT 0,
  successes INTEGER DEFAULT 0,
  last_practiced TEXT,
  FOREIGN KEY(user_id) REFERENCES users(id)
);
"""

class DBManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path=None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path=None):
        if getattr(self, "_initialized", False):
            return
        self.db_path = db_path or config.DB_PATH
        # crear carpeta si no existe
        folder = os.path.dirname(self.db_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()
        self._initialized = True

    def _ensure_schema(self):
        cur = self.conn.cursor()
        cur.executescript(_SCHEMA_SQL)
        self.conn.commit()

    # Operaciones comunes
    def create_user(self, username):
        cur = self.conn.cursor()
        try:
            cur.execute("INSERT INTO users(username) VALUES (?)", (username,))
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            # usuario ya existe, devolvemos su id
            cur.execute("SELECT id FROM users WHERE username = ?", (username,))
            row = cur.fetchone()
            return row["id"] if row else None

    def get_user(self, username):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        return dict(row) if row else None

    def save_score(self, user_id, game_name, score, details=None):
        cur = self.conn.cursor()
        # asegurar que el juego existe
        cur.execute("INSERT OR IGNORE INTO games(name) VALUES (?)", (game_name,))
        cur.execute("SELECT id FROM games WHERE name = ?", (game_name,))
        game_id = cur.fetchone()["id"]
        cur.execute("INSERT INTO scores(user_id, game_id, score, details) VALUES (?,?,?,?)",
                    (user_id, game_id, score, details))
        self.conn.commit()
        return cur.lastrowid

    def close(self):
        try:
            self.conn.close()
        except:
            pass
