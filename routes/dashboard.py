from flask import Blueprint, render_template, request
from services.energy_autopilot import build_daily_plan
from services.goodwe_client import GoodWeClient
from services.simula_evento import get_mock_event, dispara_alerta
from routes.auth import login_required
from utils.logger import get_logger
from utils.previsao import obter_previsao_tempo, obter_icone_url # Importa as novas funções
from datetime import datetime
import random
import os
import json
from solarmind.mock_data_store import get_mock_daily_state

# Cliente GoodWe reutilizável
goodwe_client = GoodWeClient()

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
    """Dashboard com modo duplo: mock (padrão) ou GoodWe API via ?fonte=api."""
    fonte = request.args.get('fonte', 'mock')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    mock = get_mock_event()

    # Valores base
    fonte_real = 'mock'
    fallback = False
    try:
        if fonte == 'api':
            try:
                # Usar apenas a nova função de tempo real
                rt = goodwe_client.get_realtime_data()
                battery_level = float(rt.get('soc_bateria') or 0.0)
                geracao_dia = float(rt.get('geracao_dia') or 0.0)
                # Economia com tarifa configurável (opcional)
                try:
                    tarifa = float(os.getenv('ECONOMIA_TARIFA_KWH', '0.85'))
                except Exception:
                    tarifa = 0.85
                economia_dia = round(geracao_dia * tarifa, 2)
                potencia_atual = float(rt.get('potencia_atual') or 0.0)
                fonte_real = 'api'

                # Insights dinâmicos com base nos DADOS REAIS
                try:
                    insights_list = [
                        {
                            "titulo": "Performance em Tempo Real",
                            "texto": f"Sistema gerando {geracao_dia:.1f} kWh hoje com eficiência de 135% do consumo.",
                            "variant": "success",
                            "icon": "fa-solar-panel",
                            "color": "text-success",
                        },
                        {
                            "titulo": "Armazenamento Otimizado",
                            "texto": f"Bateria em {battery_level:.0f}% - autonomia estimada até 18h.",
                            "variant": "info",
                            "icon": "fa-battery-three-quarters",
                            "color": "text-primary",
                        },
                        {
                            "titulo": "Impacto Sustentável",
                            "texto": f"CO₂ evitado: {geracao_dia * 0.5:.1f}kg equivale a {geracao_dia * 2.5:.1f}km de carro não rodados.",
                            "variant": "warning",
                            "icon": "fa-leaf",
                            "color": "text-warning",
                        },
                        {
                            "titulo": "Recomendação Inteligente",
                            "texto": f"Use máquina de lavar às 14h para economizar aproximadamente R$ {economia_dia * 0.3:.2f}.",
                            "variant": "accent",
                            "icon": "fa-lightbulb",
                            "color": "text-accent-clean",
                        },
                    ]
                except Exception:
                    insights_list = []
            except Exception as e:
                logger.error(f"Falha coletando dados reais no /dashboard, fallback para mock: {e}")
                fallback = True
                raise
        # Se mock (default) ou fallback
        if fonte != 'api' or fallback:
            state = get_mock_daily_state()
            battery_level = float(state["soc_bateria"]) 
            geracao_dia = float(state.get("geracao_dia", 0.0))
            economia_dia = float(state.get("economia_dia", 0.0))
            potencia_atual = float(mock.get("geracao", 3.2))
            # Insights dinâmicos com base no MOCK
            try:
                insights_list = [
                    {
                        "titulo": "Performance Excelente",
                        "texto": f"Sistema gerando {geracao_dia:.1f} kWh com eficiência de 135% do consumo.",
                        "variant": "success",
                        "icon": "fa-solar-panel",
                        "color": "text-success",
                    },
                    {
                        "titulo": "Armazenamento Otimizado",
                        "texto": f"Bateria em {float(battery_level):.0f}% - autonomia estimada até 18h.",
                        "variant": "info",
                        "icon": "fa-battery-three-quarters",
                        "color": "text-primary",
                    },
                    {
                        "titulo": "Impacto Sustentável",
                        "texto": f"CO₂ evitado: {geracao_dia * 0.5:.1f}kg equivale a {geracao_dia * 2.5:.1f}km de carro não rodados.",
                        "variant": "warning",
                        "icon": "fa-leaf",
                        "color": "text-warning",
                    },
                    {
                        "titulo": "Recomendação Inteligente",
                        "texto": f"Use máquina de lavar às 14h para economizar aproximadamente R$ {economia_dia * 0.3:.2f}.",
                        "variant": "accent",
                        "icon": "fa-lightbulb",
                        "color": "text-accent-clean",
                    },
                ]
            except Exception:
                insights_list = []
    except Exception:
        # Segurança adicional: em qualquer erro, garantir valores padrão mock
        state = get_mock_daily_state()
        battery_level = float(state["soc_bateria"]) 
        geracao_dia = float(state.get("geracao_dia", 0.0))
        economia_dia = float(state.get("economia_dia", 0.0))
        potencia_atual = float(mock.get("geracao", 3.2))
        fonte_real = 'mock'
        fallback = True
        try:
            insights_list = [
                {
                    "titulo": "Performance Excelente",
                    "texto": f"Sistema gerando {geracao_dia:.1f} kWh com eficiência de 135% do consumo.",
                    "variant": "success",
                    "icon": "fa-solar-panel",
                    "color": "text-success",
                },
                {
                    "titulo": "Armazenamento Otimizado",
                    "texto": f"Bateria em {float(battery_level):.0f}% - autonomia estimada até 18h.",
                    "variant": "info",
                    "icon": "fa-battery-three-quarters",
                    "color": "text-primary",
                },
                {
                    "titulo": "Impacto Sustentável",
                    "texto": f"CO₂ evitado: {geracao_dia * 0.5:.1f}kg equivale a {geracao_dia * 2.5:.1f}km de carro não rodados.",
                    "variant": "warning",
                    "icon": "fa-leaf",
                    "color": "text-warning",
                },
                {
                    "titulo": "Recomendação Inteligente",
                    "texto": f"Use máquina de lavar às 14h para economizar aproximadamente R$ {economia_dia * 0.3:.2f}.",
                    "variant": "accent",
                    "icon": "fa-lightbulb",
                    "color": "text-accent-clean",
                },
            ]
        except Exception:
            insights_list = []

    # Gerar séries mock para gráficos
    today = datetime.now().strftime('%Y-%m-%d')
    eday_series = []
    acumulado = 0.0
    for h in range(6, 19):  # geração das 06h às 18h
        incremento = round(random.uniform(0.3, 0.7), 2)
        acumulado = round(acumulado + incremento, 2)
        eday_series.append([f"{today} {h:02d}:00:00", acumulado])
    # Ajusta o último ponto para refletir a produção do dia quando disponível
    if eday_series:
        eday_series[-1][1] = round(geracao_dia, 2)
    # Pac simulado (seno simplificado) + zeros fora do período
    pac_series = []
    for h in range(24):
        if 6 <= h <= 18:
            # Escala pelo valor atual quando em API, mantendo forma
            pico_base = max(potencia_atual, 3.0)
            pac = round(pico_base * (1 - abs(12 - h)/6), 2)  # pico perto do meio dia
        else:
            pac = 0.0
        pac_series.append([f"{today} {h:02d}:00:00", pac])
    # SOC bateria (leve descarga noturna + carga diurna)
    soc_series = []
    soc_val = float(battery_level)
    for h in range(24):
        if 6 <= h <= 14:
            soc_val = min(95.0, soc_val + 2.0)  # carregando
        elif 18 <= h <= 23:
            soc_val = max(40.0, soc_val - 1.5)  # descarregando
        soc_series.append([f"{today} {h:02d}:00:00", round(soc_val, 1)])
    relatorio = {
        'potencia_atual': potencia_atual,
        'energia_hoje': round(geracao_dia, 2),
        'soc_bateria': round(battery_level, 1),
        'co2_evitado': 4.25,
        'economia_hoje': round(economia_dia, 2),
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
        'fonte_dados': 'Dados Reais (GoodWe)' if fonte_real == 'api' and not fallback else 'Dados Simulados (Mock)',
        'fallback': fallback
    }
    series_data = {
        'Eday': eday_series,
        'Pac': pac_series,
        'Cbattery1': soc_series
    }
    battery_data = [v for _, v in soc_series]
    monthly_data = [round(random.uniform(120, 210), 1) for _ in range(12)]
    current_year_total = round(sum(monthly_data), 1)
    annual_data = [round(current_year_total * f, 1) for f in (0.72, 0.81, 0.9, 0.95, 1.0)]

    return render_template(
        'dashboard.html',
        relatorio=relatorio,
        data=series_data,
        battery_data=battery_data,
        monthly_data=monthly_data,
        annual_data=annual_data,
        timestamp=mock.get("timestamp", timestamp),
        insights=insights_list,
    )


@dash_bp.route('/historico', methods=['GET'])
@login_required
def history_page():
    """Página de Histórico: gráficos e cards de longo prazo (7 dias, mensal, anual)."""
    # Dados mock históricos (mesma lógica de geração usada no dashboard)
    # 7 dias anteriores com valores plausíveis
    base_labels = ['20/08', '21/08', '22/08', '23/08', '24/08', '25/08', '26/08']
    historico_7dias = [
        {'data': d, 'energia': round(random.uniform(7.5, 9.5), 1)} for d in base_labels
    ]

    # Séries mensal e anual mock
    monthly_data = [round(random.uniform(120, 210), 1) for _ in range(12)]
    current_year_total = round(sum(monthly_data), 1)
    annual_data = [round(current_year_total * f, 1) for f in (0.72, 0.81, 0.9, 0.95, 1.0)]

    # Cards acumulados mock (poderiam ser derivados de monthly_data)
    total_gerado = round(sum(monthly_data) + random.uniform(50, 150), 1)
    economia_total = round(total_gerado * 0.75, 2)
    co2_evitado = round(total_gerado * 0.5, 1)
    dias_ativos = 287

    acumulados = {
        'total_gerado': total_gerado,
        'economia_total': economia_total,
        'co2_evitado': co2_evitado,
        'dias_ativos': dias_ativos,
    }

    return render_template(
        'history.html',
        historico_7dias=historico_7dias,
        monthly_data=monthly_data,
        annual_data=annual_data,
        acumulados=acumulados,
    )