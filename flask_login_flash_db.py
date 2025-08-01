# Estrutura do Projeto:
# - app.py (código principal)
# - iniciar.py (cria o banco)
# - schema.sql (script do banco)
# - templates/index.html (tela principal)
# - templates/login.html (tela de login)

# Arquivo: iniciar.py
import sqlite3

# Conectando no banco de dados (vai criar se não existir)
conexao = sqlite3.connect('banco.db')

# Abrindo o arquivo schema.sql e executando o script (criando as tabelas)
with open('schema.sql') as f:
    conexao.executescript(f.read())

# Fechando a conexão
conexao.close()

# Arquivo: schema.sql
-- DROP TABLE IF EXISTS users;
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    senha TEXT NOT NULL
);

# Arquivo: app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

# Função para conectar ao banco
def obter_conexao():
    conexao = sqlite3.connect('banco.db')
    conexao.row_factory = sqlite3.Row
    return conexao

# Iniciando o Flask
app = Flask(__name__)
app.secret_key = 'segredo-super-seguro'

# Configurando o Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Classe User para o Flask-Login
class User(UserMixin):
    def __init__(self, id, nome, email):
        self.id = id
        self.nome = nome
        self.email = email

# Função para carregar usuário pelo ID (Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    conn = obter_conexao()
    usuario = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if usuario:
        return User(id=usuario['id'], nome=usuario['nome'], email=usuario['email'])
    return None

# Rota Principal (só acessa se estiver logado)
@app.route('/')
@login_required
def index():
    return render_template('index.html', nome=current_user.nome)

# Rota de Cadastro
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        senha_hash = generate_password_hash(senha)

        conn = obter_conexao()
        conn.execute('INSERT INTO users (nome, email, senha) VALUES (?, ?, ?)', (nome, email, senha_hash))
        conn.commit()
        conn.close()

        flash('Cadastro realizado com sucesso!')
        return redirect(url_for('login'))

    return render_template('cadastro.html')

# Rota de Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = obter_conexao()
        usuario = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if usuario and check_password_hash(usuario['senha'], senha):
            user = User(id=usuario['id'], nome=usuario['nome'], email=usuario['email'])
            login_user(user)
            flash('Login realizado com sucesso!')
            return redirect(url_for('index'))
        else:
            flash('Email ou senha incorretos!')

    return render_template('login.html')

# Rota de Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da conta.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

# Arquivo: templates/index.html
# (HTML simplificado)
<!doctype html>
<html>
  <head><title>Bem-vindo</title></head>
  <body>
    <h1>Olá, {{ nome }}!</h1>
    <a href="{{ url_for('logout') }}">Sair</a>
  </body>
</html>

# Arquivo: templates/login.html
<!doctype html>
<html>
  <head><title>Login</title></head>
  <body>
    <h1>Login</h1>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for msg in messages %}<p>{{ msg }}</p>{% endfor %}
      {% endif %}
    {% endwith %}

    <form method="POST">
      <input type="email" name="email" placeholder="Email">
      <input type="password" name="senha" placeholder="Senha">
      <button type="submit">Entrar</button>
    </form>

    <a href="{{ url_for('cadastro') }}">Cadastre-se</a>
  </body>
</html>

# Arquivo: templates/cadastro.html
<!doctype html>
<html>
  <head><title>Cadastro</title></head>
  <body>
    <h1>Cadastro</h1>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for msg in messages %}<p>{{ msg }}</p>{% endfor %}
      {% endif %}
    {% endwith %}

    <form method="POST">
      <input type="text" name="nome" placeholder="Nome">
      <input type="email" name="email" placeholder="Email">
      <input type="password" name="senha" placeholder="Senha">
      <button type="submit">Cadastrar</button>
    </form>

    <a href="{{ url_for('login') }}">Já tem conta? Login</a>
  </body>
</html>
