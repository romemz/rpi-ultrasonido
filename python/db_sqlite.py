#!/usr/bin/env python3
"""Helper SQLite para rpi-ultrasonido.

Provee conexión, inicialización y función `insert_measurement` con firma
compatible con llamadas previas. La base por defecto se crea en `../data/`.
"""
from __future__ import annotations
import os
import sqlite3
from typing import Optional, Tuple, Any

DEFAULT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DEFAULT_DB = os.path.normpath(os.path.join(DEFAULT_DIR, 'ultrasonido.db'))


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Crea la tabla `measurements` con columnas flexibles."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    # Si la tabla no existe, crearla. Si existe con esquema antiguo, migrarla.
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='measurements'")
    exists = cur.fetchone() is not None

    if not exists:
        cur.execute(
            """
            CREATE TABLE measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                measured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                distance_cm REAL,
                status TEXT,
                raw_output TEXT
            )
            """
        )
    else:
        # Comprobar columnas
        cur.execute("PRAGMA table_info(measurements)")
        cols = [r[1] for r in cur.fetchall()]
        if 'distance_cm' not in cols:
            # Migrar esquema antiguo -> nuevo
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS measurements_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    measured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    distance_cm REAL,
                    status TEXT,
                    raw_output TEXT
                )
                """
            )
            # Intentar copiar datos desde columnas antiguas si existen
            if 'distance' in cols and 'timestamp' in cols:
                cur.execute(
                    "INSERT INTO measurements_new (measured_at, distance_cm, status, raw_output) "
                    "SELECT timestamp, distance, NULL, NULL FROM measurements"
                )
            elif 'distance' in cols:
                cur.execute(
                    "INSERT INTO measurements_new (measured_at, distance_cm, status, raw_output) "
                    "SELECT NULL, distance, NULL, NULL FROM measurements"
                )
            # Reemplazar tabla
            cur.execute("DROP TABLE measurements")
            cur.execute("ALTER TABLE measurements_new RENAME TO measurements")
    conn.commit()
    conn.close()


def insert_measurement(distance: Optional[float], status: Optional[str] = None,
                       raw_output: Optional[str] = None,
                       db_path: Optional[str] = None) -> int:
    """Inserta una medición. Parámetros opcionales para compatibilidad.

    Returns: id del registro insertado.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO measurements (distance_cm, status, raw_output) VALUES (?, ?, ?)",
        (None if distance is None else float(distance), status, raw_output)
    )
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return rowid


if __name__ == '__main__':
    init_db()
    print('DB inicializada en:', DEFAULT_DB)