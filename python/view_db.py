#!/usr/bin/env python3
"""view_db.py -- pequeño visor CLI para la DB de ultrasonido

Uso:
    python view_db.py [--limit N]

Muestra las últimas N filas de `data/ultrasonido.db`.
"""
from __future__ import annotations
import sqlite3
import argparse
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / 'data' / 'ultrasonido.db'

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--limit', '-n', type=int, default=20, help='Número de filas a mostrar')
    args = p.parse_args()

    if not DB.exists():
        print('No se encontró la base de datos en', DB)
        return

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute('SELECT id, measured_at, distance_cm, status, raw_output FROM measurements ORDER BY id DESC LIMIT ?', (args.limit,))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print('No hay registros')
        return

    print(f'Últimas {len(rows)} mediciones (más recientes primero):')
    print('-' * 72)
    for r in rows:
        print(f'ID={r[0]:5d}  Fecha={r[1]}  Dist={r[2]} cm  Estado={r[3]}  Raw={r[4]}')

if __name__ == '__main__':
    main()
