#srlsp-game/src/signperu/persistence/db_manager.py
# db_manager.py
# Gestor de base de datos SQLite como Singleton.
import sqlite3
import threading
from signperu import config
from pathlib import Path

class DBManager:
    _instance = None
    _lock = threading.Lock()

    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._conn.commit()

    @classmethod
    def get_instance(cls, db_path="data/signperu.db"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = DBManager(db_path)
        return cls._instance

    def execute(self, sql, params=()):
        cur = self._conn.cursor()
        cur.execute(sql, params)
        self._conn.commit()
        return cur

    def query(self, sql, params=()):
        cur = self._conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass
