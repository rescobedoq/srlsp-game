#src/signperu/data/migrations.py
"""Utilities to migrate abecedario patterns into the DB (simple serializer)."""
import json
from ..patterns import abecedario
from .db import DB

def migrate_patterns_to_db():
    db = DB.get_instance()
    conn = db.get_conn()
    cur = conn.cursor()
    patterns = abecedario.get_patterns()
    for p in patterns:
        cur.execute('INSERT INTO patterns (letra, vec) VALUES (?, ?)', (p.get('letra'), json.dumps(p.get('vec'))))
    conn.commit()
    print('Migrated %d patterns' % len(patterns))

if __name__ == '__main__':
    migrate_patterns_to_db()