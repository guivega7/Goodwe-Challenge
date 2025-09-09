from flask import Blueprint, redirect, url_for

estatisticas_bp = Blueprint('estatisticas', __name__)

@estatisticas_bp.route('/estatisticas')
def estatisticas():
    """
    Redireciona para o dashboard unificado.
    A página de estatísticas foi consolidada no dashboard principal.
    """
    return redirect(url_for('dash.dashboard'))