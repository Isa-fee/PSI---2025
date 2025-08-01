# Estrutura do Projeto:
# - app.py (código principal)
# - iniciar.py (cria o banco)
# - schema.sql (script do banco)
# - templates/index.html (tela principal)
# - templates/login.html (tela de login)
# - templates/cadastro.html (tela de cadastro)
# - templates/adicionar_produto.html (adicionar produto)
# - templates/carrinho.html (visualizar carrinho)

# Arquivo: iniciar.py
import sqlite3

conexao = sqlite3.connect('banco.db')
conexao.execute('PRAGMA foreign_keys = ON')
with open('schema.sql') as f:
    conexao.executescript(f.read())
conexao.close()

# Arquivo: schema.sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    senha TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    preco REAL NOT NULL,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS carrinho (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    produto_id INTEGER,
    quantidade INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);

# Arquivo: app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'segredo-super-seguro'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def obter_conexao():
    conexao = sqlite3.connect('banco.db')
    conexao.row_factory = sqlite3.Row
    conexao.execute('PRAGMA foreign_keys = ON')
    return conexao

class User(UserMixin):
    def __init__(self, id, nome, email):
        self.id = id
        self.nome = nome
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = obter_conexao()
    usuario = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if usuario:
        return User(id=usuario['id'], nome=usuario['nome'], email=usuario['email'])
    return None

@app.route('/')
@login_required
def index():
    conn = obter_conexao()
    produtos = conn.execute('SELECT * FROM produtos').fetchall()
    conn.close()
    return render_template('index.html', nome=current_user.nome, produtos=produtos)

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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da conta.')
    return redirect(url_for('login'))

@app.route('/adicionar-produto', methods=['GET', 'POST'])
@login_required
def adicionar_produto():
    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        conn = obter_conexao()
        conn.execute('INSERT INTO produtos (nome, preco, user_id) VALUES (?, ?, ?)', (nome, preco, current_user.id))
        conn.commit()
        conn.close()
        flash('Produto adicionado com sucesso!')
        return redirect(url_for('index'))
    return render_template('adicionar_produto.html')

@app.route('/adicionar-carrinho/<int:produto_id>')
@login_required
def adicionar_carrinho(produto_id):
    conn = obter_conexao()
    item = conn.execute('SELECT * FROM carrinho WHERE user_id = ? AND produto_id = ?', (current_user.id, produto_id)).fetchone()
    if item:
        conn.execute('UPDATE carrinho SET quantidade = quantidade + 1 WHERE id = ?', (item['id'],))
    else:
        conn.execute('INSERT INTO carrinho (user_id, produto_id, quantidade) VALUES (?, ?, 1)', (current_user.id, produto_id))
    conn.commit()
    conn.close()
    flash('Produto adicionado ao carrinho!')
    return redirect(url_for('index'))

@app.route('/carrinho')
@login_required
def carrinho():
    conn = obter_conexao()
    itens = conn.execute('''SELECT c.id, p.nome, p.preco, c.quantidade FROM carrinho c
                            JOIN produtos p ON c.produto_id = p.id
                            WHERE c.user_id = ?''', (current_user.id,)).fetchall()
    conn.close()
    total = sum(item['preco'] * item['quantidade'] for item in itens)
    return render_template('carrinho.html', itens=itens, total=total)

if __name__ == '__main__':
    app.run(debug=True)

# Arquivo: templates/index.html
<!doctype html>
<html>
  <head><title>Loja</title></head>
  <body>
    <h1>Bem-vindo, {{ nome }}!</h1>
    <a href="{{ url_for('adicionar_produto') }}">Adicionar Produto</a> |
    <a href="{{ url_for('carrinho') }}">Ver Carrinho</a> |
    <a href="{{ url_for('logout') }}">Sair</a>

    <h2>Produtos:</h2>
    <ul>
      {% for produto in produtos %}
        <li>{{ produto['nome'] }} - R$ {{ produto['preco'] }} 
          <a href="{{ url_for('adicionar_carrinho', produto_id=produto['id']) }}">Adicionar ao Carrinho</a>
        </li>
      {% endfor %}
    </ul>
  </body>
</html>

# Arquivo: templates/adicionar_produto.html
<!doctype html>
<html>
  <head><title>Adicionar Produto</title></head>
  <body>
    <h1>Adicionar Produto</h1>
    <form method="POST">
      <input type="text" name="nome" placeholder="Nome do Produto">
      <input type="number" step="0.01" name="preco" placeholder="Preço">
      <button type="submit">Adicionar</button>
    </form>
    <a href="{{ url_for('index') }}">Voltar</a>
  </body>
</html>

# Arquivo: templates/carrinho.html
<!doctype html>
<html>
  <head><title>Seu Carrinho</title></head>
  <body>
    <h1>Seu Carrinho</h1>
    <ul>
      {% for item in itens %}
        <li>{{ item['nome'] }} - R$ {{ item['preco'] }} x {{ item['quantidade'] }}</li>
      {% endfor %}
    </ul>
    <h2>Total: R$ {{ total }}</h2>
    <a href="{{ url_for('index') }}">Voltar para Loja</a>
  </body>
</html>
