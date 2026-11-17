import os
import time
import psycopg2
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

def get_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        dbname=os.environ["DB_NAME"],
    )

def init_db():
    for _ in range(10):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS visitas (
                    id SERIAL PRIMARY KEY,
                    fecha TIMESTAMP DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mensajes (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    mensaje TEXT NOT NULL,
                    fecha TIMESTAMP DEFAULT NOW()
                );
            """)
            conn.commit()
            conn.close()
            return
        except psycopg2.OperationalError:
            time.sleep(2)
    raise RuntimeError("No se pudo conectar a la base de datos")

PAGINA = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Alan Agila - Docker + PostgreSQL</title>
  <style>
    body { font-family: Arial, sans-serif; background:#f4f6f8; display:flex; justify-content:center; padding:30px; }
    .card { background:#fff; padding:30px; border-radius:12px; box-shadow:0 2px 10px #0002; width:480px; text-align:center; }
    h1 { color:#0db7ed; margin-bottom:5px; }
    .ok { background:#28a745; color:#fff; padding:6px 14px; border-radius:20px; font-size:14px; display:inline-block; }
    input, textarea { width:100%; padding:8px; margin:6px 0; box-sizing:border-box; }
    button { background:#0db7ed; color:#fff; border:0; padding:10px 20px; border-radius:6px; cursor:pointer; }
    ul { text-align:left; padding-left:18px; }
    li { margin-bottom:8px; }
    small { color:#777; }
  </style>
</head>
<body>
  <div class="card">
    <h1>¡Alan Agila!</h1>
    <h2>Yo estudio en Yavirac</h2>
    <span class="ok">Conectado a PostgreSQL ✔</span>
    <p>Visitas registradas en la BD: <b>{{ visitas }}</b></p>

    <h3>Deja un mensaje</h3>
    <form method="POST" action="/guardar">
      <input type="text" name="nombre" placeholder="Tu nombre" required maxlength="100">
      <textarea name="mensaje" placeholder="Tu mensaje" required rows="3"></textarea>
      <button type="submit">Guardar en la base de datos</button>
    </form>

    <h3>Mensajes guardados ({{ mensajes|length }})</h3>
    <ul>
      {% for m in mensajes %}
        <li><b>{{ m[0] }}</b>: {{ m[1] }}<br><small>{{ m[2].strftime('%d/%m/%Y %H:%M:%S') }}</small></li>
      {% else %}
        <li>Aún no hay mensajes.</li>
      {% endfor %}
    </ul>
  </div>
</body>
</html>
"""

@app.route("/")
def index():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO visitas DEFAULT VALUES;")
    cur.execute("SELECT COUNT(*) FROM visitas;")
    visitas = cur.fetchone()[0]
    cur.execute("SELECT nombre, mensaje, fecha FROM mensajes ORDER BY id DESC LIMIT 10;")
    mensajes = cur.fetchall()
    conn.commit()
    conn.close()
    return render_template_string(PAGINA, visitas=visitas, mensajes=mensajes)

@app.route("/guardar", methods=["POST"])
def guardar():
    nombre = request.form["nombre"].strip()
    mensaje = request.form["mensaje"].strip()
    if nombre and mensaje:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO mensajes (nombre, mensaje) VALUES (%s, %s);",
            (nombre, mensaje),
        )
        conn.commit()
        conn.close()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
