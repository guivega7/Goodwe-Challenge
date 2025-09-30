from flask import Blueprint, render_template, session, flash, request
from services.energy_autopilot import build_daily_plan
from services.goodwe_client import GoodWeClient
from services.simula_evento import get_mock_event, dispara_alerta
from routes.auth import login_required
from utils.logger import get_logger
from utils.previsao import obter_previsao_tempo, obter_icone_url # Importa as novas funções
from datetime import datetime
import os
import json

dash_bp = Blueprint('dash', __name__)
logger = get_logger(__name__)

def _extract_latest_value(resp):
    """
    Tenta extrair o último valor numérico de uma resposta de coluna do SEMS.
    Suporta formatos comuns: {'column1':[{'date':..., 'column':val}, ...]}
    """
    try:
        if not resp:
            return 0.0
        # Se for a resposta inteira com data em data.column1
        if isinstance(resp, dict):
            # Normalizar caso venha como {'data': {...}}
            if 'data' in resp and isinstance(resp['data'], dict):
                resp = resp['data']
            # Procurar listas conhecidas
            for list_key in ('column1', 'list', 'items', 'datas', 'result', 'data'):
                if list_key in resp and isinstance(resp[list_key], list) and resp[list_key]:
                    last = resp[list_key][-1]
                    # campos comuns de valor
                    for val_key in ('column', 'value', 'val', 'v'):
                        if val_key in last and isinstance(last[val_key], (int, float, str)):
                            try:
                                return float(last[val_key])
                            except:
                                continue
                    # se não encontrar, procurar primeiro campo numérico
                    for k, v in last.items():
                        if isinstance(v, (int, float)):
                            return float(v)
            # Se resp for diretamente uma lista
            if isinstance(resp, list) and resp:
                last = resp[-1]
                if isinstance(last, dict):
                    for val_key in ('column', 'value', 'val', 'v'):
                        if val_key in last and isinstance(last[val_key], (int, float, str)):
                            try:
                                return float(last[val_key])
                            except:
                                continue
                    for k, v in last.items():
                        if isinstance(v, (int, float)):
                            return float(v)
        # fallback
    except Exception:
        pass
    return 0.0


@dash_bp.route('/autopilot')
@login_required
def autopilot():
    """Página que exibe o Plano do Dia do Energy Autopilot."""
    # Valores padrão para demonstração; no futuro, ler do GoodWeClient
    soc = float(request.args.get('soc', '35'))
    
    # Busca a previsão do tempo real
    previsao_5_dias = obter_previsao_tempo()
    
    # Usa a descrição do tempo do primeiro dia da previsão para o plano diário
    condicao_clima_hoje = "ensolarado"
    if previsao_5_dias:
        condicao_clima_hoje = previsao_5_dias[0].get('descricao', 'ensolarado')

    # Simula a previsão de geração baseada no clima de hoje
    fatores_clima = {'chuva': 0.2, 'nuvens': 0.5, 'limpo': 1.0, 'ensolarado': 1.0}
    fator = 0.5 # Padrão
    for key, val in fatores_clima.items():
        if key in condicao_clima_hoje:
            fator = val
            break
    forecast = round(15.0 * fator, 1) # Simula geração máxima de 15kWh

    plan = build_daily_plan(soc, forecast)
    
    return render_template(
        'autopilot.html', # Voltando para o template original
        plan=plan, 
        previsao_tempo=previsao_5_dias,
        obter_icone_url=obter_icone_url # Passa a função para o template
    )

@dash_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """Dashboard render: agora usa GoodWeClient.build_data & build_history (7 dias) quando fonte=api."""
    fonte_escolhida = request.args.get('fonte', 'mock')
    client = GoodWeClient()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if fonte_escolhida == 'mock':
        mock = get_mock_event()
        relatorio = {
            'potencia_atual': mock.get("geracao", 3.2),
            'energia_hoje': 8.5,
            'soc_bateria': 75.0,
            'co2_evitado': 4.25,
            'economia_hoje': 6.38,
            'historico_7dias': [
                {'data': '20/08', 'energia': 8.1},
                {'data': '21/08', 'energia': 9.2},
                {'data': '22/08', 'energia': 7.8},
                {'data': '23/08', 'energia': 8.7},
                {'data': '24/08', 'energia': 8.9},
                {'data': '25/08', 'energia': 8.3},
                {'data': '26/08', 'energia': 8.5}
            ],
            'status': 'online',
            'data_update': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'fonte_dados': 'Dados Simulados (Mock)'
        }
        return render_template('dashboard.html', relatorio=relatorio, data={}, timestamp=mock.get("timestamp", timestamp))

    # fonte = api
    try:
        dados = client.build_data()  # produção, consumo, bateria, economia
        historico = client.build_history(days=7)
        # Mapear para estrutura esperada anteriormente
        energia_hoje = dados['producao']['hoje']
        potencia_atual = dados['bateria']['potencia_atual']
        soc_bateria = dados['bateria']['soc']
        economia_hoje = dados['economia']['hoje']
        co2_evitado = round(energia_hoje * 0.5, 2)
        historico_7dias = [
            {'data': h['data'][5:], 'energia': h['producao']} for h in historico  # formato mm-dd para curto
        ]
        relatorio = {
            'potencia_atual': potencia_atual,
            'energia_hoje': energia_hoje,
            'soc_bateria': soc_bateria,
            'co2_evitado': co2_evitado,
            'economia_hoje': economia_hoje,
            'historico_7dias': historico_7dias,
            'status': 'online' if potencia_atual > 0 else 'standby',
            'data_update': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'fonte_dados': 'GOODWE_SEMS_API'
        }
        # Passar series brutas simplificadas para tabela (usar history + bateria atual)
        series_data = {
            'Eday': [[h['data'], h['producao']] for h in historico],
            'Pac': [],  # não exposto diretamente via build_data (poderia ser adicionado futuramente)
            'Cbattery1': []  # média diária já representada; série completa exigiria endpoint separado
        }
        
        # Se não há dados reais para Pac e Cbattery1, gerar simulados
        if not series_data.get('Pac'):
            # Pac sempre 0 (como você pediu)
            today = datetime.now().strftime('%Y-%m-%d')
            series_data['Pac'] = [[f"{today} {h:02d}:00:00", 0.0] for h in range(24)]
        
        if not series_data.get('Cbattery1'):
            # SOC médio 74-76%
            import random
            today = datetime.now().strftime('%Y-%m-%d')
            series_data['Cbattery1'] = [[f"{today} {h:02d}:00:00", round(random.uniform(74, 76), 1)] for h in range(24)]
        
        return render_template('dashboard.html', relatorio=relatorio, data=series_data, timestamp=timestamp)
    except Exception as e:
        logger.error(f"Erro dashboard(api): {e}")
        flash("Erro ao carregar dados reais — mostrando mock.", "warning")
        mock = get_mock_event()
        relatorio = {
            'potencia_atual': mock.get("geracao", 3.2),
            'energia_hoje': 8.5,
            'soc_bateria': 75.0,
            'co2_evitado': 4.25,
            'economia_hoje': 6.38,
            'historico_7dias': [
                {'data': '20/08', 'energia': 8.1},
                {'data': '21/08', 'energia': 9.2},
                {'data': '22/08', 'energia': 7.8},
                {'data': '23/08', 'energia': 8.7},
                {'data': '24/08', 'energia': 8.9},
                {'data': '25/08', 'energia': 8.3},
                {'data': '26/08', 'energia': 8.5}
            ],
            'status': 'online',
            'data_update': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'fonte_dados': 'Dados Simulados (Fallback - Erro na API)'
        }
        return render_template('dashboard.html', relatorio=relatorio, data={}, timestamp=timestamp)