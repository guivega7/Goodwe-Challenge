from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from models.usuario import usuarios, Usuario

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST','GET'])
def login():
    if request.method == "POST":
        nome = request.form['nome']
        senha = request.form['senha']
        usuario = usuarios.get(nome)

        if usuario and usuario.checar_senha(senha):
            session['usuario'] = usuario.nome
            return redirect(url_for('dash.dashboard'))
        flash('Credenciais inválidas')
    return render_template('login.html')

@auth_bp.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        nome = request.form['nome']
        senha = request.form["senha"]
        if nome in usuarios:
            flash('Usuario Já existe!')
            return redirect(url_for("auth.register"))
        
        novo_usuario = Usuario(nome, senha)
        usuarios[nome] = novo_usuario
        return redirect(url_for("auth.login"))
    return render_template("register.html")

@auth_bp.route('/logout')
def logout():
    session.pop('usuario',None)
    return redirect(url_for("auth.login"))

#@auth_bp.route('/esqueceu-senha')
#def esqueceusenha():
    