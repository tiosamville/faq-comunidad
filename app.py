import os
from flask import Flask, render_template, request, redirect, Response
from functools import wraps
import sqlite3
from difflib import SequenceMatcher

app = Flask(__name__)

# RUTA CORRECTA PARA RENDER: usa /tmp para la base de datos
DB_PATH = '/tmp/base_preguntas.db'

# --- SEGURIDAD PRIVADA ---
def check_auth(username, password):
    # Esto busca el usuario y contraseña en la configuración de Render
    # Si no los encuentra, usará 'invitado' (por seguridad)
    secret_user = os.environ.get('ADMIN_USER_NEW', 'invitado')
    secret_pass = os.environ.get('ADMIN_PASS_NEW', 'incorrecto')
    return username == secret_user and password == secret_pass
# -------------------------

def authenticate():
    return Response('Acceso denegado', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
# ----------------------------------

def es_similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > 0.6

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS preguntas 
                    (id INTEGER PRIMARY KEY, pregunta TEXT, respuesta TEXT, estado TEXT)''')
    conn.commit()
    conn.close()

# Inicializar la base de datos al arrancar
init_db()

@app.route('/')
def index():
    conn = get_db()
    preguntas = conn.execute('SELECT * FROM preguntas WHERE estado = "publicada"').fetchall()
    conn.close()
    return render_template('index.html', preguntas=preguntas)

@app.route('/enviar', methods=['POST'])
def enviar():
    pregunta_nueva = request.form['pregunta']
    conn = get_db()
    preguntas_existentes = conn.execute('SELECT * FROM preguntas WHERE estado = "publicada"').fetchall()
    for p in preguntas_existentes:
        if es_similar(pregunta_nueva, p['pregunta']):
            conn.close()
            return render_template('mensaje.html', pregunta_existente=p['pregunta'], respuesta_existente=p['respuesta'])
    conn.execute('INSERT INTO preguntas (pregunta, respuesta, estado) VALUES (?, "", "pendiente")', (pregunta_nueva,))
    conn.commit()
    conn.close()
    return redirect('/')

# RUTAS PROTEGIDAS CON @requires_auth
@app.route('/admin')
@requires_auth
def admin():
    conn = get_db()
    preguntas = conn.execute('SELECT * FROM preguntas').fetchall()
    conn.close()
    return render_template('admin.html', preguntas=preguntas)

@app.route('/actualizar/<int:id>', methods=['POST'])
@requires_auth
def actualizar(id):
    nueva_respuesta = request.form['respuesta']
    conn = get_db()
    conn.execute('UPDATE preguntas SET respuesta = ?, estado = "publicada" WHERE id = ?', (nueva_respuesta, id))
    conn.commit()
    conn.close()
    return redirect('/admin')
    
@app.route('/responder/<int:id>', methods=['POST'])
@requires_auth
def responder(id):
    respuesta = request.form['respuesta']
    conn = get_db()
    conn.execute('UPDATE preguntas SET respuesta = ?, estado = "publicada" WHERE id = ?', (respuesta, id))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/eliminar/<int:id>')
@requires_auth
def eliminar(id):
    conn = get_db()
    conn.execute('DELETE FROM preguntas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=False)
