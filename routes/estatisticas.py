from flask import Blueprint, render_template, redirect, url_for, request, session 
from models.usuario import Usuario
from extensions import db

estatisticas_bp = Blueprint('estatisticas', __name__)

@estatisticas_bp.route('/estatisticas', methods=['GET','POST'])
def estatisticas():
    '''
    Função de Estatísticas.
    Verifica se o usuário está logado, caso contrário, redireciona para a página de login.
    '''
    if 'usuario_id' not in session:
        return redirect(url_for("auth.login"))
    return render_template('estatisticas.html')