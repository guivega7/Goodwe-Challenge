from flask import Blueprint, render_template, request, redirect, url_for, session
from models.aparelho import Aparelho
from extensions import db

aparelhos_bp = Blueprint('aparelhos', __name__)

@aparelhos_bp.route('/aparelhos')
def listar():
    # Mock de aparelhos para demonstração quando não há usuário logado
    if 'usuario_id' not in session:
        aparelhos_mock = [
            {'id': 1, 'nome': 'Ar Condicionado Sala', 'consumo': 1.5, 'prioridade': 2, 'status': True},
            {'id': 2, 'nome': 'Geladeira', 'consumo': 0.3, 'prioridade': 1, 'status': True},
            {'id': 3, 'nome': 'TV Smart 55"', 'consumo': 0.15, 'prioridade': 4, 'status': False},
            {'id': 4, 'nome': 'Máquina de Lavar', 'consumo': 0.8, 'prioridade': 3, 'status': False},
        ]
        return render_template('aparelhos.html', aparelhos=aparelhos_mock)
    
    aparelhos = Aparelho.query.filter_by(usuario_id=session['usuario_id']).order_by(Aparelho.prioridade).all()
    return render_template('aparelhos.html', aparelhos=aparelhos)

@aparelhos_bp.route('/aparelhos/adicionar', methods=['POST'])
def adicionar():
    # Verificar se há usuário logado
    if 'usuario_id' not in session:
        return redirect(url_for('aparelhos.listar'))
    
    nome = request.form['nome']
    consumo = float(request.form['consumo'])
    prioridade = int(request.form['prioridade'])
    
    aparelho = Aparelho(
        nome=nome,
        consumo=consumo,
        prioridade=prioridade,
        usuario_id=session['usuario_id']
    )
    db.session.add(aparelho)
    db.session.commit()
    
    return redirect(url_for('aparelhos.listar'))