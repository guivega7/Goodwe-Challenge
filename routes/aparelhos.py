from flask import Blueprint, render_template, request, redirect, url_for, session
from models.aparelho import Aparelho
from extensions import db

aparelhos_bp = Blueprint('aparelhos', __name__)

@aparelhos_bp.route('/aparelhos')
def listar():
    aparelhos = Aparelho.query.filter_by(usuario_id=session['usuario_id']).order_by(Aparelho.prioridade).all()
    return render_template('aparelhos.html', aparelhos=aparelhos)

@aparelhos_bp.route('/aparelhos/adicionar', methods=['POST'])
def adicionar():
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