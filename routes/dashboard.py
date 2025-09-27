from flask import Blueprint, render_template, session, flash, request
from services.energy_autopilot import build_daily_plan
from services.goodwe_client import GoodWeClient
from services.simula_evento import get_mock_event, dispara_alerta
from routes.auth import login_required
from utils.logger import get_logger
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
    forecast = float(request.args.get('forecast', '8'))
    plan = build_daily_plan(soc, forecast)
    return render_template('autopilot.html', plan=plan)

@dash_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """Rota principal do dashboard com integração GoodWe SEMS API"""
    
    # Pegar preferencia do usuario entre API ou mock
    fonte_escolhida = request.args.get('fonte', 'mock')  # 'mock' ou 'api'
    
    # Force mock mode if user chose it
    if fonte_escolhida == 'mock':
        print("🔄 Usuário escolheu dados simulados")
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
        return render_template('dashboard.html', relatorio=relatorio, data={}, timestamp=mock.get("timestamp", datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    # API mode - tenta pegar dados reais
    try:
        # incializa GoodWe client
        client = GoodWeClient()
        
        # Tenta fazer login se tiver credenciais
        account = os.environ.get('SEMS_ACCOUNT')
        password = os.environ.get('SEMS_PASSWORD')
        login_region = os.environ.get('SEMS_LOGIN_REGION', 'us')    # Região para login
        data_region = os.environ.get('SEMS_DATA_REGION', 'eu')     # Região para dados
        
        token = None
        if account and password:
            print(f"🔐 Tentando login com conta: {account}")
            print(f"📍 Login region: {login_region.upper()}, Data region: {data_region.upper()}")
            
            # Faz login na região especificada
            token = client.crosslogin(account, password)
            if token:
                print(f"✅ Login bem-sucedido no servidor {login_region.upper()}!")
                print(f"📊 Buscando dados no servidor {data_region.upper()}...")
            else:
                print(f"❌ Falha no login no {login_region.upper()}. Usando token padrão.")
                token = os.environ.get('SEMS_TOKEN', 'BAC20C32-B5D2-4894-AECB-D9799987ADD9')
        else:
            print("⚠️ Sem credenciais SEMS_ACCOUNT/SEMS_PASSWORD. Usando token padrão.")
            token = os.environ.get('SEMS_TOKEN', 'BAC20C32-B5D2-4894-AECB-D9799987ADD9')
            data_region = os.environ.get('SEMS_DATA_REGION', 'eu')
        
        # Usar SN do .env SEMPRE
        inv_id = os.environ.get('SEMS_INV_ID', 'DEMO_INVERTER_123')
        print(f"🔍 Usando SN do .env: {inv_id}")
        
        date = datetime.now().strftime('%Y-%m-%d')
        
        # Buscar dados em tempo real para colunas chave (sem fallback mock para validação)
        columns = ['Pac', 'Eday', 'Cbattery1']
        series_data = client.get_multiple_columns_data(token, inv_id, columns, date, use_mock_data=False)
        
        # Se não encontrou dados, tentar descobrir inversores disponíveis
        if not any(series_data.get(col) for col in columns):
            logger.info("Não encontrou dados para o SN fornecido. Tentando descobrir inversores disponíveis...")
            return render_template('dashboard.html', relatorio=relatorio, data={}, timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Extrair valores atuais para KPIs
        potencia_atual = 0.0
        energia_hoje = 0.0
        soc_bateria = 0.0
        
        if series_data.get('Pac') and series_data['Pac']:
            potencia_atual = series_data['Pac'][-1][1]  # Último valor
            
        if series_data.get('Eday') and series_data['Eday']:
            energia_hoje = series_data['Eday'][-1][1]
            
        if series_data.get('Cbattery1') and series_data['Cbattery1']:
            soc_bateria = series_data['Cbattery1'][-1][1]
        
        # Calcular métricas derivadas
        co2_evitado = round(energia_hoje * 0.5, 2)  # ~0.5kg CO2 por kWh
        economia_hoje = round(energia_hoje * 0.75, 2)  # ~R$0.75 por kWh
        
        # Gerar dados dos gráficos (últimos 7 dias simulados por agora)
        historico_7dias = []
        for i in range(7):
            day_offset = 6 - i  # Voltar 6 dias de hoje
            date_point = datetime.now().replace(day=max(1, datetime.now().day - day_offset))
            historico_7dias.append({
                'data': date_point.strftime('%d/%m'),
                'energia': round(8.5 + (i * 0.3), 1)
            })
        
        # Preparar relatório para template
        fonte_texto = f'GoodWe SEMS API - Inversor: {inv_id}'
        relatorio = {
            'potencia_atual': potencia_atual,
            'energia_hoje': energia_hoje,
            'soc_bateria': soc_bateria,
            'co2_evitado': co2_evitado,
            'economia_hoje': economia_hoje,
            'historico_7dias': historico_7dias,
            'status': 'online' if potencia_atual > 0 else 'standby',
            'data_update': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'fonte_dados': fonte_texto
        }
        
        print(f"✅ Dados do dashboard: Pac={potencia_atual}kW, Eday={energia_hoje}kWh, SOC={soc_bateria}%")
        
        # Disparar alertas baseados nos dados
        if soc_bateria < 20:
            dispara_alerta("low_battery", f"Bateria baixa: {soc_bateria}%")
        
        if potencia_atual < 0.1 and 8 <= datetime.now().hour <= 17:  # Deveria estar gerando durante o dia
            dispara_alerta("falha_inversor", "Possível falha no inversor - baixa geração durante o dia")
        
        return render_template('dashboard.html', relatorio=relatorio, data=series_data, timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
    except Exception as e:
        print(f"❌ Erro no dashboard: {e}")
        flash("Erro ao carregar dados do inversor — usando dados simulados.", "warning")
        
        # Fallback para dados simulados
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
        
        return render_template('dashboard.html', relatorio=relatorio, data={}, timestamp=mock.get("timestamp", datetime.now().strftime('%Y-%m-%d %H:%M:%S')))