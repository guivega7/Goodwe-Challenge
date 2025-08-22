from flask import Blueprint, render_template, session
from services.automacao import AutomacaoEnergia
from utils.previsao import PrevisaoEnergia
from models.aparelho import Aparelho
from datetime import datetime, timedelta
import random

dash_bp = Blueprint('dash', __name__)

def simular_dados_energia():
    """Simula dados de geração e consumo de energia"""
    hora_atual = datetime.now().hour
    
    # Geração varia conforme hora do dia
    if 6 <= hora_atual <= 18:  # Dia
        geracao = round(random.uniform(2.0, 5.0), 1)
    else:  # Noite
        geracao = 0.0
    
    # Consumo varia conforme horário
    if 17 <= hora_atual <= 21:  # Horário de pico
        consumo = round(random.uniform(3.0, 6.0), 1)
    else:
        consumo = round(random.uniform(1.0, 3.0), 1)
    
    return geracao, consumo

def gerar_relatorio(consumo, geracao):
    """Gera relatório com dados de consumo e geração"""
    return {
        "consumo": consumo,
        "geracao": geracao,
        "saldo": round(geracao - consumo, 1),
        "custo": round(consumo * 0.95, 2)  # R$ 0,95 por kWh
    }

@dash_bp.route('/dashboard')
def dashboard():
    # Simula dados em tempo real
    geracao_atual, consumo_atual = simular_dados_energia()
    
    # Gera relatório
    relatorio = gerar_relatorio(consumo_atual, geracao_atual)
    
    # Simula outros dados
    historico = [
        {
            'data': (datetime.now() - timedelta(days=i)).strftime('%d/%m'),
            'geracao': round(random.uniform(20, 35), 1),
            'consumo': round(random.uniform(15, 30), 1)
        } for i in range(7)
    ]

    return render_template(
        'dashboard.html',
        relatorio=relatorio,
        historico=historico,
        potencia_instantanea=round(random.uniform(2, 5), 1),
        energia_hoje=round(random.uniform(15, 25), 1),
        co2_evitar=round(random.uniform(10, 20), 1)
    )