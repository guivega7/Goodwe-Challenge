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
        # Gerar séries mock para gráficos
        today = datetime.now().strftime('%Y-%m-%d')
        # Histórico 7 dias já está no relatorio, mas também produziremos Eday (dia atual ponto a ponto por hora)
        eday_series = []
        acumulado = 0.0
        for h in range(6, 19):  # geração das 06h às 18h
            import random
            incremento = round(random.uniform(0.3, 0.7), 2)
            acumulado = round(acumulado + incremento, 2)
            eday_series.append([f"{today} {h:02d}:00:00", acumulado])
        # Pac simulado (seno simplificado) + zeros fora do período
        pac_series = []
        for h in range(24):
            if 6 <= h <= 18:
                pac = round(2.5 * (1 - abs(12 - h)/6), 2)  # pico perto do meio dia
            else:
                pac = 0.0
            pac_series.append([f"{today} {h:02d}:00:00", pac])
        # SOC bateria (leve descarga noturna + carga diurna)
        soc_series = []
        soc_val = 63.0
        for h in range(24):
            if 6 <= h <= 14:
                soc_val = min(95.0, soc_val + 2.0)  # carregando
            elif 18 <= h <= 23:
                soc_val = max(40.0, soc_val - 1.5)  # descarregando
            soc_series.append([f"{today} {h:02d}:00:00", round(soc_val, 1)])
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
        series_data = {
            'Eday': eday_series,
            'Pac': pac_series,
            'Cbattery1': soc_series
        }
        battery_data = [v for _, v in soc_series]
        # Dados mensais simulados (kWh) e anuais (últimos 5 anos)
        import random
        monthly_data = [round(random.uniform(120, 210), 1) for _ in range(12)]
        current_year_total = round(sum(monthly_data), 1)
        annual_data = [round(current_year_total * f, 1) for f in (0.72, 0.81, 0.9, 0.95, 1.0)]
    return render_template('dashboard.html', relatorio=relatorio, data=series_data, battery_data=battery_data, monthly_data=monthly_data, annual_data=annual_data, timestamp=mock.get("timestamp", timestamp))

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
            'Cbattery1': []  # será preenchido com dados reais se disponíveis
        }
        
        # Tentar buscar dados reais de Cbattery1
        try:
            # Garantir que as credenciais estão carregadas
            client._load_env_credentials()
            # Obter token válido
            token = client._get_token()
            if token:
                today = datetime.now().strftime('%Y-%m-%d')
                battery_data = client.get_inverter_data_by_column(token, client.inverter_id, 'Cbattery1', today)
                if battery_data and isinstance(battery_data, dict) and 'data' in battery_data and 'column1' in battery_data['data']:
                    # Extrair dados da série temporal (formato: [['data', valor], ...])
                    column1_data = battery_data['data']['column1']
                    series_data['Cbattery1'] = [[point['date'], point['column']] for point in column1_data]
                    logger.info(f"Dados de Cbattery1 obtidos com sucesso: {len(column1_data)} pontos")
        except Exception as e:
            logger.warning(f"Erro ao buscar dados de Cbattery1: {e}")
        
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
        # Construir dados mensais e anuais básicos (aproximação) para preencher gráficos
        # Estratégia: fazer um loop de até 90 dias atrás para reduzir carga e distribuir em meses
        monthly_map: dict[str, float] = {}
        try:
            token_scan = client._get_token()
            if token_scan:
                from datetime import timedelta
                for i in range(0, 90):  # últimos ~3 meses
                    dcheck = datetime.now() - timedelta(days=i)
                    date_key = dcheck.strftime('%Y-%m-%d 00:00:00')
                    try:
                        daily_resp = client.get_inverter_data_by_column(token_scan, client.inverter_id, 'eday', date_key)
                        kwh = client._last_series_value(daily_resp)
                        ym = dcheck.strftime('%Y-%m')
                        monthly_map[ym] = monthly_map.get(ym, 0.0) + kwh
                    except Exception:
                        continue
        except Exception:
            pass
        # Montar lista de 12 meses (Jan..Dez) usando ano atual, preenchendo com 0 se não coletado
        from calendar import month_name
        current_year = datetime.now().year
        monthly_data = []
        for m in range(1, 13):
            ym_key = f"{current_year}-{m:02d}"
            monthly_data.append(round(monthly_map.get(ym_key, 0.0), 2))
        # Dados anuais: usar valor anual estimado (producao_mes*12) para ano atual e degradar anos anteriores
        ano_atual_estimado = dados['producao']['ano']
        annual_data = [round(ano_atual_estimado * f, 2) for f in (0.8, 0.85, 0.9, 0.95, 1.0)]
        return render_template('dashboard.html', relatorio=relatorio, data=series_data, monthly_data=monthly_data, annual_data=annual_data, timestamp=timestamp)
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