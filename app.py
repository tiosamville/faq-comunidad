import os
from flask import Flask, render_template, request, redirect
import sqlite3
from difflib import SequenceMatcher

app = Flask(__name__)

# Configuración para que la base de datos siempre se encuentre en la carpeta del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'base_preguntas.db')

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

@app.route('/admin')
def admin():
    conn = get_db()
    preguntas = conn.execute('SELECT * FROM preguntas').fetchall()
    conn.close()
    return render_template('admin.html', preguntas=preguntas)

@app.route('/actualizar/<int:id>', methods=['POST'])
def actualizar(id):
    nueva_respuesta = request.form['respuesta']
    conn = get_db()
    conn.execute('UPDATE preguntas SET respuesta = ?, estado = "publicada" WHERE id = ?', (nueva_respuesta, id))
    conn.commit()
    conn.close()
    return redirect('/admin')
    
@app.route('/responder/<int:id>', methods=['POST'])
def responder(id):
    respuesta = request.form['respuesta']
    conn = get_db()
    conn.execute('UPDATE preguntas SET respuesta = ?, estado = "publicada" WHERE id = ?', (respuesta, id))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/eliminar/<int:id>')
def eliminar(id):
    conn = get_db()
    conn.execute('DELETE FROM preguntas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/admin')

if __name__ == '__main__':
    init_db()
    # En producción (Render), debug debe estar en False
    app.run(debug=False)