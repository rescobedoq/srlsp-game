#src/signperu/services/user_manager.py
import sqlite3
from ..data.db import DB

class UserManager:
    def __init__(self):
        self.db = DB.get_instance()

    def create_user(self, username, password_hash):
        conn = self.db.get_conn()
        cur = conn.cursor()
        cur.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        return cur.lastrowid
