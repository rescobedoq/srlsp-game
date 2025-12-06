#srlsp-game/src/signperu/data/data.py
import os, sqlite3, threading

class DB:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, path=None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(path)
            return cls._instance

    def __init__(self, path=None):
        if path is None:
            home = os.path.expanduser('~')
            appdir = os.path.join(home, '.local', 'share', 'proyectotosenias')
            os.makedirs(appdir, exist_ok=True)
            path = os.path.join(appdir, 'signperu.db')
        self._path = path
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._ensure_schema()

    def _ensure_schema(self):
        cur = self._conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            game_id TEXT,
            level INTEGER,
            score INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            letra TEXT,
            vec TEXT
        )''')
        self._conn.commit()

    def get_conn(self):
        return self._conn
