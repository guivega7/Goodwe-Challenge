from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.usuario import Usuario
from extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Função de Login do usuário.
    Verifica se o usuário já está logado, caso sim, redireciona para o dashboard.
    Se não estiver logado, renderiza o template de login.
    '''
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(nome=nome).first()
        if usuario and usuario.checar_senha(senha):
            session['usuario_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            return redirect(url_for('dash.dashboard'))
        else:
            flash('Nome ou senha inválidos.')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    '''
    Função de Registro do usuário.
    Verifica se o usuário já está logado, caso sim, redireciona para o dashboard.
    Se não estiver logado, renderiza o template de registro.
    '''
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        confirmar = request.form['confirmar_senha']

        if senha != confirmar:
            flash('As senhas não coincidem.')
            return render_template('register.html')

        if Usuario.query.filter_by(nome=nome).first():
            flash('Nome de usuário já existe.')
            return render_template('register.html')

        if Usuario.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.')
            return render_template('register.html')

        novo_usuario = Usuario(nome=nome, email=email)
        novo_usuario.set_senha(senha)
        db.session.add(novo_usuario)
        db.session.commit()
        flash('Cadastro realizado com sucesso! Faça login.')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    '''
    Função de Logout do usuário.
    Limpa a sessão do usuário e redireciona para a página inicial.
    '''
    session.clear()
    return redirect(url_for('main.home'))