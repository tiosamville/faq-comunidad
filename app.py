import os
import psycopg2
from flask import Flask, render_template, request, redirect, Response
from functools import wraps
from difflib import SequenceMatcher

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    # Se agrega connect_timeout para evitar que la red se bloquee en Render
    return psycopg2.connect(DATABASE_URL, sslmode='require', connect_timeout=10)

def check_auth(username, password):
    secret_user = os.environ.get('ADMIN_USER_NEW', 'admin')
    secret_pass = os.environ.get('ADMIN_PASS_NEW', '123456')
    return username == secret_user and password == secret_pass

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response('Acceso denegado', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated

def es_similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > 0.6

@app.route('/')
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, pregunta, respuesta, estado FROM preguntas WHERE estado = %s', ('publicada',))
    preguntas = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', preguntas=preguntas)

@app.route('/enviar', methods=['POST'])
def enviar():
    pregunta_nueva = request.form['pregunta']
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT pregunta, respuesta FROM preguntas WHERE estado = %s', ('publicada',))
    preguntas_existentes = cur.fetchall()
    
    for p in preguntas_existentes:
        if es_similar(pregunta_nueva, p[0]):
            cur.close()
            conn.close()
            return render_template('mensaje.html', pregunta_existente=p[0], respuesta_existente=p[1])
    
    cur.execute('INSERT INTO preguntas (pregunta, respuesta, estado) VALUES (%s, %s, %s)', (pregunta_nueva, '', 'pendiente'))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/')

@app.route('/gestion_privada_2026')
@requires_auth
def admin():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, pregunta, respuesta, estado FROM preguntas ORDER BY id DESC')
    preguntas = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', preguntas=preguntas)

@app.route('/actualizar/<int:id>', methods=['POST'])
@requires_auth
def actualizar(id):
    nueva_respuesta = request.form['respuesta']
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE preguntas SET respuesta = %s, estado = %s WHERE id = %s', (nueva_respuesta, 'publicada', id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/gestion_privada_2026')

@app.route('/responder/<int:id>', methods=['POST'])
@requires_auth
def responder(id):
    respuesta = request.form['respuesta']
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE preguntas SET respuesta = %s, estado = %s WHERE id = %s', (respuesta, 'publicada', id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/gestion_privada_2026')

@app.route('/eliminar/<int:id>')
@requires_auth
def eliminar(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM preguntas WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/gestion_privada_2026')

if __name__ == '__main__':
    app.run(debug=False)
