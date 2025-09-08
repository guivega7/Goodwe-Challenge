from flask import Blueprint, render_template, redirect, url_for, request, session 
from models.usuario import Usuario
from extensions import db
from datetime import datetime, timedelta
import calendar
from .auth import login_required

estatisticas_bp = Blueprint('estatisticas', __name__)

@estatisticas_bp.route('/estatisticas', methods=['GET','POST'])
@login_required
def estatisticas():
    '''
    Função de Estatísticas.
    Mostra dados mock quando não há usuário logado.
    '''
    # Se não há usuário logado, usar dados mock
    if 'usuario_id' not in session:
        # Dados mock para demonstração
        dados_estatisticas = {
            'total_gerado': '3,245.8',
            'economia': '2,434.35',
            'co2_total': '1,623.0',
            'dias_ativos': '287',
            'meses_data': {
                'labels': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
                'values': [245, 278, 312, 289, 267, 234, 201, 256, 289, 298, 276, 312]
            },
            'anos_data': {
                'labels': ['2021', '2022', '2023', '2024', '2025'],
                'values': [2800, 3000, 3200, 3100, 3245]
            }
        }
        return render_template('estatisticas.html', **dados_estatisticas)
    
    # Dados mock para estatísticas
    current_date = datetime.now()
    
    # Dados mensais (últimos 12 meses)
    meses_labels = []
    dados_mensais = []
    for i in range(12):
        date = current_date - timedelta(days=30*i)
        meses_labels.insert(0, calendar.month_abbr[date.month])
        # Simular dados mensais (mais baixo no inverno, mais alto no verão)
        base_generation = 250 + (50 * (0.5 + 0.5 * abs(6 - date.month) / 6))
        dados_mensais.insert(0, round(base_generation + (i * 5), 1))
    
    # Dados anuais (últimos 5 anos)
    anos_labels = []
    dados_anuais = []
    for i in range(5):
        year = current_date.year - i
        anos_labels.insert(0, str(year))
        # Simular crescimento anual
        annual_total = 2800 + (i * 200)
        dados_anuais.insert(0, annual_total)
    
    # Totais acumulados
    total_gerado = sum(dados_mensais) * 12  # Aproximação
    economia = round(total_gerado * 0.75, 2)  # R$0.75 por kWh
    co2_total = round(total_gerado * 0.5, 2)   # 0.5kg CO2 por kWh
    
    dados_estatisticas = {
        'meses': meses_labels,
        'dados_mensais': dados_mensais,
        'anos': anos_labels,
        'dados_anuais': dados_anuais,
        'total_gerado': total_gerado,
        'economia': economia,
        'co2_total': co2_total
    }
    
    return render_template('estatisticas.html', **dados_estatisticas)