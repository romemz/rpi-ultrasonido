#!/usr/bin/env python3
"""sqlite_web.py

Servidor HTTP mínimo para ver la tabla `measurements` de la base SQLite
sin instalar Apache/PHP. Uso:

  python3 python/sqlite_web.py --db data/ultrasonido.db --port 8000

Accede en el navegador a `http://<RASPBERRY_IP>:8000/`.
Parámetros:
  ?limit=N    mostrar N filas (por defecto 200)
  ?limit=all  mostrar todas las filas (cuidado con tablas grandes)
  /api/json   devuelve JSON con las filas
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sqlite3
import json
import argparse
import html
from pathlib import Path


class SQLiteHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        limit = qs.get('limit', [None])[0]
        try:
            if limit is None:
                limit_val = 200
            elif limit == 'all':
                limit_val = None
            else:
                limit_val = int(limit)
        except Exception:
            limit_val = 200

        if parsed.path.startswith('/api'):
            self.send_json(limit_val)
        else:
            self.send_html(limit_val)

    def send_json(self, limit):
        rows = query_db(self.server.db_path, limit)
        out = [dict(r) for r in rows]
        body = json.dumps(out, default=str, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, limit):
        rows = query_db(self.server.db_path, limit)
        title = 'Mediciones - SQLite Viewer'
        body = ['<!doctype html><meta charset="utf-8">', f'<h1>{html.escape(title)}</h1>']
        body.append('<p>Use <code>?limit=all</code> to show all rows (beware large tables).</p>')
        body.append('<table border="1" cellpadding="6" cellspacing="0">')
        body.append('<tr><th>ID</th><th>Fecha</th><th>Distancia (cm)</th><th>Estado</th><th>Raw</th></tr>')
        for r in rows:
            body.append('<tr>' +
                        f'<td>{r[0]}</td>' +
                        f'<td>{html.escape(str(r[1]))}</td>' +
                        f'<td>{html.escape(str(r[2]))}</td>' +
                        f'<td>{html.escape(str(r[3]))}</td>' +
                        f'<td>{html.escape(str(r[4]))}</td>' +
                        '</tr>')
        body.append('</table>')
        body.append('<p><a href="?limit=10">10</a> · <a href="?limit=50">50</a> · <a href="?limit=200">200</a> · <a href="?limit=all">All</a></p>')
        html_body = '\n'.join(body).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html_body)))
        self.end_headers()
        self.wfile.write(html_body)


def query_db(db_path, limit=None):
    db = Path(db_path)
    if not db.exists():
        return []
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if limit is None:
        cur.execute('SELECT id, measured_at, distance_cm, status, raw_output FROM measurements ORDER BY id DESC')
    else:
        cur.execute('SELECT id, measured_at, distance_cm, status, raw_output FROM measurements ORDER BY id DESC LIMIT ?', (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


def run_server(db_path, host='0.0.0.0', port=8000):
    server = HTTPServer((host, port), SQLiteHandler)
    server.db_path = db_path
    print('Serving', db_path, 'on', f'http://{host}:{port}/')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopping server')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--db', default='data/ultrasonido.db', help='Path to sqlite DB')
    p.add_argument('--host', default='0.0.0.0', help='Host to bind')
    p.add_argument('--port', type=int, default=8000, help='Port')
    args = p.parse_args()
    run_server(args.db, args.host, args.port)


if __name__ == '__main__':
    main()
