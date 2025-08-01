from flask import Flask, redirect, render_template, url_for
from flask import request, flash

import sqlite3

def obter_conexao():
    conexao = sqlite3.connect('banco.db')
    conexao.row_factory = sqlite3.Row
    return conexao

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == "POST":
        nome = request.form.get('nome')

        conn = obter_conexao()
        SQL = "INSERT INTO users(nome) VALUES(?)"
        conn.execute(SQL, (nome,))
        conn.commit()
        conn.close()

        # flash
        return redirect(url_for('index'))

    conn = obter_conexao()
    SQL = "SELECT * FROM users"
    lista = conn.execute(SQL).fetchall()
    conn.close()
    return render_template('index.html', lista = lista)