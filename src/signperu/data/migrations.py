#srlsp-game/src/signperu/data/migrations.py
"""Utilidades para migrar patterns (JSON) al DB SQLite.
Uso desde CLI (ejemplo):
    python -m signperu.data.migrations --json ../patterns/patterns.json --upsert --verbose
El script:
- lee un JSON con lista de objetos {'letra': 'A', 'vec': [...], 'meta': {...} (opcional)}
- valida estructura y longitud (si EXPECTED_LENGTH está disponible)
- inserta o actualiza (upsert) en la tabla 'patterns' de la DB
- añade columna 'meta' si no existe (ALTER TABLE ADD COLUMN meta TEXT)
"""
import argparse
import json
import os
from typing import List, Dict, Any, Optional

from .db import DB
from ..patterns import abecedario

# Intentamos obtener la longitud esperada del vector desde core.features (si existe)
try:
    from ..core.features import EXPECTED_LENGTH
except Exception:
    EXPECTED_LENGTH = None  # si es None, no validamos longitud estricta

def _ensure_meta_column(conn):
    """Asegura que la tabla 'patterns' tenga la columna 'meta' (TEXT)."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(patterns)")
    cols = [row[1] for row in cur.fetchall()]  # row[1] es name
    if 'meta' not in cols:
        # ALTER TABLE para añadir columna meta
        cur.execute("ALTER TABLE patterns ADD COLUMN meta TEXT")
        conn.commit()

def _load_patterns_from_file(path: str) -> List[Dict[str, Any]]:
    """Carga patterns desde un archivo JSON y valida formato básico."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo JSON no encontrado: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("El JSON debe contener una lista de patterns.")
    return data

def _validate_pattern(p: Dict[str, Any], expected_len: Optional[int] = None) -> bool:
    """Valida que 'p' tenga 'letra' y 'vec' y opcionalmente que vec tenga longitud esperada."""
    if not isinstance(p, dict):
        return False
    if 'letra' not in p or 'vec' not in p:
        return False
    if expected_len is not None:
        vec = p.get('vec')
        if not isinstance(vec, list) or len(vec) != expected_len:
            return False
    return True


def migrate_patterns_to_db(json_path: Optional[str] = None,
                           upsert: bool = True,
                           overwrite: bool = False,
                           dry_run: bool = False,
                           verbose: bool = False) -> Dict[str, int]:
    """
    Migra patterns JSON a la tabla 'patterns' de la DB.

    Args:
        json_path: ruta al archivo JSON; si None usa abecedario.get_patterns()
        upsert: si True, actualiza patrón existente (por 'letra'); si False, inserta solo nuevos.
        overwrite: si True y upsert==True fuerza actualización aunque ya exista (reemplaza vec/meta).
                   Si overwrite==False y upsert==True actualiza solo si contenido distinto.
        dry_run: si True no modifica la DB (solo reporta).
        verbose: imprime logs detallados.

    Retorna:
        dict con conteos: {'inserted': N, 'updated': M, 'skipped': K, 'errors': E}
    """
    # Cargar patterns fuente
    if json_path:
        patterns = _load_patterns_from_file(json_path)
    else:
        # usar abecedario.get_patterns() si no se pasa archivo
        patterns = abecedario.get_patterns()

    counts = {'inserted': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

    # Validación previa (estructura)
    valid_patterns = []
    for p in patterns:
        if _validate_pattern(p, EXPECTED_LENGTH):
            valid_patterns.append(p)
        else:
            counts['errors'] += 1
            if verbose:
                print("Pattern inválido o longitud distinta (será ignorado):", p.get('letra', str(p)))

    if len(valid_patterns) == 0:
        if verbose:
            print("No hay patterns válidos para migrar.")
        return counts

    db = DB.get_instance()
    conn = db.get_conn()

    # Asegurar columna 'meta' (opcional)
    try:
        _ensure_meta_column(conn)
    except Exception as e:
        if verbose:
            print("Advertencia: no se pudo asegurar columna 'meta':", e)

    cur = conn.cursor()

    # Procesar cada pattern
    for p in valid_patterns:
        letra = p['letra']
        vec = p['vec']
        meta = p.get('meta', None)
        vec_json = json.dumps(vec, ensure_ascii=False)
        meta_json = json.dumps(meta, ensure_ascii=False) if meta is not None else None

        try:
            cur.execute("SELECT id, vec, meta FROM patterns WHERE letra = ?", (letra,))
            row = cur.fetchone()
            if row:
                # ya existe
                existing_vec_json = row[1]
                existing_meta = row[2]
                if upsert:
                    # decidir actualizar o no
                    should_update = overwrite or (existing_vec_json != vec_json or existing_meta != meta_json)
                    if should_update:
                        if not dry_run:
                            cur.execute("UPDATE patterns SET vec = ?, meta = ? WHERE letra = ?",
                                        (vec_json, meta_json, letra))
                        counts['updated'] += 1
                        if verbose:
                            print(f"Actualizado pattern letra='{letra}'")
                    else:
                        counts['skipped'] += 1
                        if verbose:
                            print(f"Omitido (sin cambios) pattern letra='{letra}'")
                else:
                    counts['skipped'] += 1
                    if verbose:
                        print(f"Omitido (ya existe) pattern letra='{letra}'")
            else:
                # no existe -> insertar
                if not dry_run:
                    cur.execute("INSERT INTO patterns (letra, vec, meta) VALUES (?, ?, ?)",
                                (letra, vec_json, meta_json))
                counts['inserted'] += 1
                if verbose:
                    print(f"Insertado pattern letra='{letra}'")
        except Exception as e:
            counts['errors'] += 1
            if verbose:
                print(f"Error procesando pattern letra='{letra}': {e}")

    if not dry_run:
        conn.commit()
    if verbose:
        print("Migración completada. Resumen:", counts)

    return counts

def export_patterns_from_db(output_json: str):
    """Exporta todos los patterns guardados en la DB a un archivo JSON (útil para backup)."""
    db = DB.get_instance()
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT letra, vec, meta FROM patterns")
    out = []
    for letra, vec_json, meta_json in cur.fetchall():
        try:
            vec = json.loads(vec_json) if vec_json else None
        except Exception:
            vec = None
        try:
            meta = json.loads(meta_json) if meta_json else None
        except Exception:
            meta = None
        out.append({'letra': letra, 'vec': vec, 'meta': meta})
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Exportados {len(out)} patterns en {output_json}")

def _parse_args_and_run():
    parser = argparse.ArgumentParser(description="Migra patterns JSON a la DB (tabla patterns).")
    parser.add_argument("--json", "-j", help="Ruta al archivo JSON de patterns (por defecto usa abecedario.get_patterns())")
    parser.add_argument("--no-upsert", dest="upsert", action="store_false", help="No actualizar patrones existentes (solo insertar nuevos).")
    parser.add_argument("--overwrite", action="store_true", help="Forzar actualización (reemplaza vec/meta incluso si igual).")
    parser.add_argument("--dry-run", action="store_true", help="No modifica la DB, solo muestra acciones.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Imprime información detallada.")
    parser.add_argument("--export", "-e", help="Exporta patterns actuales de la DB a un JSON especificado y sale.")
    args = parser.parse_args()

    if args.export:
        export_patterns_from_db(args.export)
        return

    counts = migrate_patterns_to_db(json_path=args.json,
                                    upsert=args.upsert,
                                    overwrite=args.overwrite,
                                    dry_run=args.dry_run,
                                    verbose=args.verbose)
    print("Resultado:", counts)

if __name__ == "__main__":
    _parse_args_and_run()
