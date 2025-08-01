# Estrutura do Projeto:
# - app.py (código principal)
# - iniciar.py (cria o banco)
# - schema.sql (script do banco)
# - templates/index.html (tela principal)
# - templates/login.html (tela de login)
# - templates/cadastro.html (tela de cadastro)
# - templates/adicionar_livro.html (adicionar livro)

# Arquivo: iniciar.py
import sqlite3

# Conectando no banco de dados (vai criar se não existir)
conexao = sqlite3.connect('banco.db')

# Ativando Foreign Keys durante a criação das tabelas
conexao.execute('PRAGMA foreign_keys = ON')

# Abrindo o arquivo schema.sql e executando o script (criando as tabelas)
with open('schema.sql') as f:
    conexao.executescript(f.read())

# Fechando a conexão
conexao.close()

# Arquivo: schema.sql
PRAGMA foreign_keys = ON; -- Ativa FK durante a criação (mas não é permanente)

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    senha TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

# Arquivo: app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

# Função para conectar ao banco (Ativando FK toda vez que conectar)
def obter_conexao():
    conexao = sqlite3.connect('banco.db')
    conexao.row_factory = sqlite3.Row  # Faz os resultados parecerem dicionários
    conexao.execute('PRAGMA foreign_keys = ON')  # Liga a verificação de Chave Estrangeira
    return conexao

# Iniciando o Flask
app = Flask(__name__)
app.secret_key = 'segredo-super-seguro'  # Necessário para Flash messages e sessão

# Configurando o Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Se o usuário não estiver logado, redireciona para login

# Classe User para o Flask-Login (obrigatória)
class User(UserMixin):
    def __init__(self, id, nome, email):
        self.id = id
        self.nome = nome
        self.email = email

# Função que carrega o usuário logado a partir do banco
@login_manager.user_loader
def load_user(user_id):
    conn = obter_conexao()
    usuario = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if usuario:
        return User(id=usuario['id'], nome=usuario['nome'], email=usuario['email'])
    return None

# Página Principal (só acessa logado) - Exibe os livros do usuário
@app.route('/')
@login_required
def index():
    conn = obter_conexao()
    livros = conn.execute('SELECT * FROM books WHERE user_id = ?', (current_user.id,)).fetchall()
    conn.close()
    return render_template('index.html', nome=current_user.nome, livros=livros)

# Rota de Cadastro de Usuário
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

# Rota para Adicionar Livro
@app.route('/adicionar-livro', methods=['GET', 'POST'])
@login_required
def adicionar_livro():
    if request.method == 'POST':
        titulo = request.form['titulo']
        conn = obter_conexao()
        conn.execute('INSERT INTO books (titulo, user_id) VALUES (?, ?)', (titulo, current_user.id))
        conn.commit()
        conn.close()

        flash('Livro adicionado com sucesso!')
        return redirect(url_for('index'))

    return render_template('adicionar_livro.html')

if __name__ == '__main__':
    app.run(debug=True)

# Arquivo: templates/index.html
<!doctype html>
<html>
  <head><title>Bem-vindo</title></head>
  <body>
    <h1>Olá, {{ nome }}!</h1>

    <h2>Seus Livros:</h2>
    <ul>
      {% for livro in livros %}
        <li>{{ livro['titulo'] }}</li>
      {% endfor %}
    </ul>

    <a href="{{ url_for('adicionar_livro') }}">Adicionar Livro</a> |
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

# Arquivo: templates/adicionar_livro.html
<!doctype html>
<html>
  <head><title>Adicionar Livro</title></head>
  <body>
    <h1>Adicionar Livro</h1>
    <form method="POST">
      <input type="text" name="titulo" placeholder="Título do Livro">
      <button type="submit">Adicionar</button>
    </form>

    <a href="{{ url_for('index') }}">Voltar</a>
  </body>
</html>
