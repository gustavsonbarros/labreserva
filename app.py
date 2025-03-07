from flask import Flask, render_template, request, redirect, url_for, session, flash, render_template
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'sua_chave_secreta'  # Troque por uma chave forte e segura

# Conexão com o banco de dados
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Função para inicializar o banco de dados
def init_db():
    connection = get_db_connection()
    cursor = connection.cursor()

    # Tabela de reservas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_usuario TEXT NOT NULL,
            laboratorio TEXT NOT NULL,
            data TEXT NOT NULL,
            horario_inicio TEXT NOT NULL,
            horario_fim TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendente'  -- Nova coluna adicionada
        )
    ''')

    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            admin INTEGER NOT NULL DEFAULT 0
        )
    ''')

    connection.commit()
    connection.close()

# Rota para página inicial
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

# Rota para listar reservas
@app.route('/reservas')
def listar_reservas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    connection = get_db_connection()
    reservas = connection.execute('SELECT * FROM reservas').fetchall()
    laboratorios = connection.execute('SELECT DISTINCT laboratorio FROM reservas').fetchall()
    connection.close()
    return render_template('listar.html', reservas=reservas, laboratorios=[lab['laboratorio'] for lab in laboratorios])

# Rota para criar nova reserva (somente para usuários logados)
@app.route('/reservar', methods=('GET', 'POST'))
def reservar():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nome_usuario = session['username']
        laboratorio = request.form['laboratorio']
        data = request.form['data']
        horario_inicio = request.form['horario_inicio']
        horario_fim = request.form['horario_fim']

        connection = get_db_connection()

        # Verificar se há conflito de horário no mesmo laboratório
        conflito = connection.execute('''
            SELECT * FROM reservas 
            WHERE laboratorio = ? AND data = ? 
            AND ((horario_inicio < ? AND horario_fim > ?) 
                 OR (horario_inicio < ? AND horario_fim > ?) 
                 OR (horario_inicio >= ? AND horario_fim <= ?))
        ''', (laboratorio, data, horario_fim, horario_fim, horario_inicio, horario_inicio, horario_inicio, horario_fim)).fetchone()

        if conflito:
            flash('Erro: Já existe uma reserva para este laboratório nesse horário!')
            connection.close()
            return redirect(url_for('reservar'))

        # Se não houver conflito, inserir a nova reserva
        connection.execute(
            'INSERT INTO reservas (nome_usuario, laboratorio, data, horario_inicio, horario_fim) VALUES (?, ?, ?, ?, ?)',
            (nome_usuario, laboratorio, data, horario_inicio, horario_fim)
        )
        connection.commit()
        connection.close()

        flash('Reserva realizada com sucesso!')
        return redirect(url_for('listar_reservas'))

    # Quando o formulário for carregado, passamos a lista de horários ocupados
    connection = get_db_connection()
    horarios_ocupados = connection.execute('''
        SELECT horario_inicio, horario_fim FROM reservas WHERE laboratorio = ? AND data = ?
    ''', (request.args.get('laboratorio'), request.args.get('data'))).fetchall()
    connection.close()

    return render_template('reserva.html', horarios_ocupados=horarios_ocupados)

# Rota para editar reserva
@app.route('/editar_reserva/<int:id>', methods=['GET', 'POST'])
def editar_reserva(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = get_db_connection()
    reserva = connection.execute('SELECT * FROM reservas WHERE id = ?', (id,)).fetchone()

    if not reserva:
        flash('Reserva não encontrada!')
        connection.close()
        return redirect(url_for('listar_reservas'))

    # Verificar se o usuário tem permissão para editar a reserva
    if session['username'] != reserva['nome_usuario'] and not session.get('admin'):
        flash('Você não tem permissão para editar esta reserva!')
        connection.close()
        return redirect(url_for('listar_reservas'))

    if request.method == 'POST':
        laboratorio = request.form['laboratorio']
        data = request.form['data']
        horario_inicio = request.form['horario_inicio']
        horario_fim = request.form['horario_fim']

        # Verificar conflito de horário
        conflito = connection.execute('''
            SELECT * FROM reservas 
            WHERE laboratorio = ? AND data = ? 
            AND ((horario_inicio < ? AND horario_fim > ?) 
                 OR (horario_inicio < ? AND horario_fim > ?) 
                 OR (horario_inicio >= ? AND horario_fim <= ?))
            AND id != ?
        ''', (laboratorio, data, horario_fim, horario_fim, horario_inicio, horario_inicio, horario_inicio, horario_fim, id)).fetchone()

        if conflito:
            flash('Erro: Já existe uma reserva para este laboratório nesse horário!')
            connection.close()
            return redirect(url_for('editar_reserva', id=id))

        # Atualizar a reserva
        connection.execute('''
            UPDATE reservas 
            SET laboratorio = ?, data = ?, horario_inicio = ?, horario_fim = ? 
            WHERE id = ?
        ''', (laboratorio, data, horario_inicio, horario_fim, id))
        connection.commit()
        connection.close()

        flash('Reserva atualizada com sucesso!')
        return redirect(url_for('listar_reservas'))

    connection.close()
    return render_template('editar_reserva.html', reserva=reserva)

# Rota para excluir reserva
@app.route('/excluir_reserva/<int:id>', methods=['POST'])
def excluir_reserva(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = get_db_connection()
    reserva = connection.execute('SELECT * FROM reservas WHERE id = ?', (id,)).fetchone()

    if not reserva:
        flash('Reserva não encontrada!')
        connection.close()
        return redirect(url_for('listar_reservas'))

    # Apenas o administrador pode excluir reservas
    if not session.get('admin'):
        flash('Você não tem permissão para excluir esta reserva!')
        connection.close()
        return redirect(url_for('listar_reservas'))

    # Excluir a reserva
    connection.execute('DELETE FROM reservas WHERE id = ?', (id,))
    connection.commit()
    connection.close()

    flash('Reserva excluída com sucesso!')
    return redirect(url_for('listar_reservas'))

# Rota para cancelar reserva
@app.route('/cancelar_reserva/<int:id>', methods=['POST'])
def cancelar_reserva(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = get_db_connection()
    reserva = connection.execute('SELECT * FROM reservas WHERE id = ?', (id,)).fetchone()

    if not reserva:
        flash('Reserva não encontrada!')
        connection.close()
        return redirect(url_for('listar_reservas'))

    # Verificar se o usuário tem permissão para cancelar a reserva
    if session['username'] != reserva['nome_usuario'] and not session.get('admin'):
        flash('Você não tem permissão para cancelar esta reserva!')
        connection.close()
        return redirect(url_for('listar_reservas'))

    # Atualizar o status da reserva para "cancelada"
    connection.execute(
        'UPDATE reservas SET status = ? WHERE id = ?',
        ('cancelada', id)
    )
    connection.commit()
    connection.close()

    flash('Reserva cancelada com sucesso!')
    return redirect(url_for('listar_reservas'))

# Rota para login
@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']

        connection = get_db_connection()
        user = connection.execute(
            'SELECT * FROM usuarios WHERE username = ?', (username,)).fetchone()
        connection.close()

        if user and check_password_hash(user['senha'], senha):
            session['user_id'] = user['id']
            session['username'] = user['username']

            # Atribuir admin se a chave 'admin' existir
            session['admin'] = user['admin'] if 'admin' in user.keys() else 0

            return redirect(url_for('index'))
        else:
            flash('Credenciais inválidas!')

    return render_template('login.html')

# Rota para logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/recuperar-senha", methods=['GET', 'POST'])
def recuperar_senha():
    if request.method == 'POST':
        # Lógica para recuperar a senha (por exemplo, enviar um e-mail com um link de redefinição)
        email = request.form.get('email')
        # Aqui você pode adicionar a lógica para enviar um e-mail com um link de redefinição de senha
        flash('Um e-mail foi enviado com instruções para redefinir sua senha.')
        return redirect(url_for('login'))
    
    return render_template("recuperar_senha.html")

# Rota para registro de novos usuários
@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']
        hashed_password = generate_password_hash(senha)

        connection = get_db_connection()
        try:
            connection.execute(
                'INSERT INTO usuarios (username, senha) VALUES (?, ?)',
                (username, hashed_password)
            )
            connection.commit()
        except sqlite3.IntegrityError:
            flash('Usuário já existe!')
            return redirect(url_for('register'))
        finally:
            connection.close()

        flash('Usuário registrado com sucesso!')
        return redirect(url_for('login'))

    return render_template('register.html')

# Rota do painel do administrador
@app.route('/admin')
def admin_panel():
    if 'user_id' not in session or not session.get('admin'):
        return redirect(url_for('login'))  # Redireciona se não for admin

    connection = get_db_connection()

    # Pegando o número de reservas e de usuários
    total_reservas = connection.execute('SELECT COUNT(*) FROM reservas').fetchone()[0]
    total_usuarios = connection.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0]

    # Buscar reservas pendentes
    reservas_pendentes = connection.execute(
        'SELECT * FROM reservas WHERE status = ?', ('pendente',)
    ).fetchall()

    connection.close()

    return render_template(
        'admin.html',
        total_reservas=total_reservas,
        total_usuarios=total_usuarios,
        reservas_pendentes=reservas_pendentes  # Passar as reservas pendentes para o template
    )

# Rota para aprovar reserva
@app.route('/admin/aprovar/<int:id>', methods=['POST'])
def aprovar_reserva(id):
    if 'user_id' not in session or not session.get('admin'):
        return redirect(url_for('login'))

    connection = get_db_connection()
    connection.execute(
        'UPDATE reservas SET status = ? WHERE id = ?',
        ('aprovada', id)
    )
    connection.commit()
    connection.close()

    flash('Reserva aprovada com sucesso!')
    return redirect(url_for('admin_panel'))

# Rota para rejeitar reserva
@app.route('/admin/rejeitar/<int:id>', methods=['POST'])
def rejeitar_reserva(id):
    if 'user_id' not in session or not session.get('admin'):
        return redirect(url_for('login'))

    connection = get_db_connection()
    connection.execute(
        'UPDATE reservas SET status = ? WHERE id = ?',
        ('rejeitada', id)
    )
    connection.commit()
    connection.close()

    flash('Reserva rejeitada.')
    return redirect(url_for('admin_panel'))

# Adicionando exibição de mensagens de erro
@app.after_request
def after_request(response):
    if 'user_id' not in session:
        flash('Você precisa estar logado para acessar esta página!')
    return response

if __name__ == '__main__':
    init_db()  # Chama a função para garantir que o banco de dados esteja inicializado
    app.run(debug=True)