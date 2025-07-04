from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os

app = Flask(__name__)
app.secret_key = 'chave-da-biblioteca'

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Arquivos ---
USUARIOS_ARQ = 'usuarios.json'
LIVROS_ARQ = 'livros.json'

# --- Dados ---
if os.path.exists(USUARIOS_ARQ):
    with open(USUARIOS_ARQ, 'r') as f:
        usuarios = json.load(f)
else:
    usuarios = {}

def salvar_usuarios():
    with open(USUARIOS_ARQ, 'w') as f:
        json.dump(usuarios, f, indent=4)

if os.path.exists(LIVROS_ARQ):
    with open(LIVROS_ARQ, 'r') as f:
        livros = json.load(f)
else:
    livros = {"Python para Iniciantes": 3, "Aventuras de Alice": 2, "Flask na Prática": 1}
    with open(LIVROS_ARQ, 'w') as f:
        json.dump(livros, f, indent=4)

# --- Usuário para Flask-Login ---
class User(UserMixin):
    def __init__(self, nome):
        self.id = nome

@login_manager.user_loader
def load_user(user_id):
    if user_id in usuarios:
        return User(user_id)

# --- Rotas ---
@app.route('/')
def index():
    ultimo = request.cookies.get('ultimo_livro')
    return f'<h1>Bem-vindo à Biblioteca!</h1><p>Último livro emprestado: {ultimo or "nenhum"}</p>'

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        if nome in usuarios:
            flash('Usuário já existe.', 'erro')
            return redirect(url_for('cadastro'))
        usuarios[nome] = generate_password_hash(senha)
        salvar_usuarios()
        flash('Cadastro feito com sucesso!', 'sucesso')
        return redirect(url_for('login'))
    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        if nome in usuarios and check_password_hash(usuarios[nome], senha):
            login_user(User(nome))
            session['usuario'] = nome
            flash('Login feito com sucesso!', 'sucesso')
            return redirect(url_for('livros'))
        flash('Usuário ou senha incorretos.', 'erro')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Você saiu da conta.', 'sucesso')
    return redirect(url_for('login'))

@app.route('/livros')
@login_required
def livros_view():
    return render_template('livros.html', livros=livros)

@app.route('/emprestar/<livro>')
@login_required
def emprestar(livro):
    if livros.get(livro, 0) > 0:
        livros[livro] -= 1
        with open(LIVROS_ARQ, 'w') as f:
            json.dump(livros, f, indent=4)
        flash(f'Você emprestou "{livro}"!', 'sucesso')
        resp = make_response(redirect(url_for('livros_view')))
        resp.set_cookie('ultimo_livro', livro)
        return resp
    flash('Este livro está indisponível no momento.', 'erro')
    return redirect(url_for('livros_view'))
