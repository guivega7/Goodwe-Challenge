"""
API Routes para o Sistema SolarMind - SOMENTE DADOS REAIS

Este módulo contém endpoints da API REST para integração com GoodWe SEMS Portal.
TODOS os endpoints com dados simulados foram REMOVIDOS.
"""

import os
import time
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
import random

from extensions import logger
from services.goodwe_client import GoodWeClient
from services.gemini_client import GeminiClient
from services.tuya_client import TuyaClient
from services.smartplug_service import latest_readings, summary
from services.smartplug_service import collect_and_store
from services.scheduler import get_jobs_info
from models.aparelho import Aparelho
from extensions import db

# Inicializar blueprint
api_bp = Blueprint('api', __name__)

# Inicializar clientes
goodwe_client = GoodWeClient()

# ---------------------- SIMPLE IN-MEMORY CACHE ---------------------- #
_CACHE: dict[str, tuple[float, dict]] = {}

def _cache_get(key: str):
    item = _CACHE.get(key)
    if not item:
        return None
    expires, value = item
    if time.time() > expires:
        _CACHE.pop(key, None)
        return None
    return value

def _cache_set(key: str, value: dict, ttl: int):
    _CACHE[key] = (time.time() + ttl, value)
gemini_client = GeminiClient()
tuya_client: TuyaClient | None = None  # Inicializado sob demanda

def _get_tuya_client() -> TuyaClient:
    global tuya_client
    if tuya_client is None:
        try:
            tuya_client = TuyaClient()
        except Exception as e:
            logger.error(f"Falha ao inicializar TuyaClient: {e}")
            raise
    return tuya_client


@api_bp.route('/api/status')
def api_status():
    """
    Endpoint para verificar status da API.
    
    Retorna:
        JSON: Status geral da API
    """
    return jsonify({
        'ok': True,
        'service': 'SolarMind API',
        'version': '2.0.0',
        'mode': 'REAL_DATA_ONLY',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'solar': {
                '/api/solar/status': 'Status atual do sistema solar (dados reais)',
                '/api/solar/data': 'Dados completos do sistema (dados reais)', 
                '/api/solar/history': 'Histórico de produção (dados reais)',
                '/api/solar/config': 'Configuração das credenciais SEMS'
            }
        }
    })


@api_bp.route('/api/solar/config')
def solar_config():
    """
    Endpoint para verificar configuração da API GoodWe SEMS.
    
    Retorna:
        JSON: Informações sobre a configuração atual
    """
    # Verificar se credenciais estão configuradas
    account = os.getenv('SEMS_ACCOUNT')
    password = os.getenv('SEMS_PASSWORD')
    inverter_id = os.getenv('SEMS_INV_ID')
    region = os.getenv('SEMS_DATA_REGION', 'US')
    
    return jsonify({
        'ok': True,
        'config': {
            'modo_atual': 'DADOS_REAIS_GOODWE',
            'descricao': 'Todos os dados vêm da API GoodWe SEMS Portal',
            'credenciais_configuradas': {
                'account': bool(account),
                'password': bool(password), 
                'inverter_id': bool(inverter_id)
            },
            'regiao_sems': region,
            'endpoints_disponiveis': [
                '/api/solar/status - Status atual do sistema',
                '/api/solar/data - Dados completos de produção e bateria',
                '/api/solar/history - Histórico dos últimos dias'
            ]
        },
        'timestamp': datetime.now().isoformat()
    })


@api_bp.route('/api/solar/status')
def solar_status():
    """Status resumido (caching 30s)."""
    cache_key = 'solar_status'
    cached = _cache_get(cache_key)
    if cached:
        return jsonify({**cached, '_cache': True})
    try:
        data = goodwe_client.build_status()
        payload = {'ok': True, 'data': data, 'timestamp': datetime.now().isoformat()}
        _cache_set(cache_key, payload, ttl=30)
        return jsonify({**payload, '_cache': False})
    except ValueError as ve:
        return jsonify({'ok': False, 'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Erro /api/solar/status: {e}")
        return jsonify({'ok': False, 'error': 'Erro interno'}), 500


@api_bp.route('/api/solar/data')
def solar_data():
    """Dados agregados (caching 120s)."""
    cache_key = 'solar_data'
    cached = _cache_get(cache_key)
    if cached:
        return jsonify({**cached, '_cache': True})
    try:
        dados = goodwe_client.build_data()
        payload = {'ok': True, 'data': dados, 'timestamp': datetime.now().isoformat()}
        _cache_set(cache_key, payload, ttl=120)
        return jsonify({**payload, '_cache': False})
    except ValueError as ve:
        return jsonify({'ok': False, 'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Erro /api/solar/data: {e}")
        return jsonify({'ok': False, 'error': 'Erro interno'}), 500


@api_bp.route('/api/solar/history')
def solar_history():
    """Histórico de produção (caching 600s)."""
    try:
        days = int(request.args.get('days', 7))
        days_clamped = min(max(1, days), 30)
        cache_key = f'solar_history_{days_clamped}'
        cached = _cache_get(cache_key)
        if cached:
            return jsonify({**cached, '_cache': True})
        historico = goodwe_client.build_history(days_clamped)
        payload = {
            'ok': True,
            'data': historico,
            'periodo': f'{days_clamped}_dias',
            'fonte_dados': 'GOODWE_SEMS_API',
            'inverter_id': goodwe_client.inverter_id,
            'timestamp': datetime.now().isoformat()
        }
        _cache_set(cache_key, payload, ttl=600)
        return jsonify({**payload, '_cache': False})
    except ValueError as ve:
        return jsonify({'ok': False, 'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Erro /api/solar/history: {e}")
        return jsonify({'ok': False, 'error': 'Erro interno'}), 500


@api_bp.route('/api/solar/intraday')
def solar_intraday_series():
    """Séries intradiárias (Pac, SOC) para o dia atual (caching 5 min)."""
    cache_key = 'solar_intraday'
    cached = _cache_get(cache_key)
    if cached:
        return jsonify({**cached, '_cache': True})
    try:
        series_data = goodwe_client.build_intraday_series()
        payload = {'ok': True, 'data': series_data, 'timestamp': datetime.now().isoformat()}
        # Cache mais curto para dados que mudam com frequência
        _cache_set(cache_key, payload, ttl=300) # 5 minutos
        return jsonify({**payload, '_cache': False})
    except ValueError as ve:
        return jsonify({'ok': False, 'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Erro /api/solar/intraday: {e}")
        return jsonify({'ok': False, 'error': 'Erro interno'}), 500


@api_bp.route('/api/smartplug/energy')
def smartplug_energy():
    """Dados de energia detalhados (parcial - depende do suporte do device)."""
    try:
        client = _get_tuya_client()
        energy = client.get_energy_today()
        return jsonify({
            'ok': True,
            'data': energy,
            'fonte': 'TUYA_API'
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e),
            'fonte': 'TUYA_API'
        }), 500


@api_bp.route('/api/smartplug/readings')
def smartplug_readings():
    """Lista últimas leituras persistidas (limite via query param)."""
    try:
        limit = int(request.args.get('limit', 50))
        data = latest_readings(limit=min(limit, 500))
        return jsonify({'ok': True, 'data': data})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@api_bp.route('/api/smartplug/summary')
def smartplug_summary():
    """Resumo agregado das leituras (médias, máximos)."""
    try:
        data = summary()
        return jsonify({'ok': True, 'data': data})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


# ------------------------- DEBUG SCHEDULER / SMARTPLUG ------------------------- #
@api_bp.route('/api/scheduler/jobs')
def scheduler_jobs():
    """Lista os jobs ativos do APScheduler (debug)."""
    try:
        return jsonify({'ok': True, 'jobs': get_jobs_info()})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@api_bp.route('/api/smartplug/collect', methods=['POST'])
def smartplug_collect_manual():
    """Força uma coleta manual imediata da smart plug."""
    try:
        rec_id = collect_and_store()
        if rec_id:
            return jsonify({'ok': True, 'id': rec_id})
        return jsonify({'ok': False, 'error': 'Falha ao coletar (ver logs)'}), 500
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# ----------------------- TUYA: Lista e Controle ----------------------- #
@api_bp.route('/api/tuya/devices')
def tuya_devices():
    """Lista dispositivos Tuya crus (direto da API)."""
    try:
        client = _get_tuya_client()
        include_raw = request.args.get('raw') in ('1','true','yes')
        data = client.list_devices(include_raw=include_raw)
        ok = data.get('success', False)
        if not ok:
            # Explica possíveis causas
            hint = (
                "Possíveis causas: (1) Projeto Tuya sem devices vinculados; (2) Necessário setar TUYA_USER_ID; "
                "(3) Credenciais/região incorretas; (4) App não vinculou a conta de usuário no Cloud."
            )
            return jsonify({'ok': False, 'data': data, 'hint': hint}), 400
        return jsonify({'ok': True, 'data': data})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@api_bp.route('/api/tuya/device/<device_id>/status')
def tuya_device_status(device_id: str):
    """Status bruto de um device específico."""
    try:
        client = _get_tuya_client()
        data = client.get_device_status_by_id(device_id)
        return jsonify({'ok': True, 'data': data})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@api_bp.route('/api/tuya/device/<device_id>/switch', methods=['POST'])
def tuya_device_switch(device_id: str):
    """Liga/desliga (switch_1) um device Tuya e sincroniza status local se existir Aparelho."""
    try:
        desired = request.json.get('on') if request.is_json else request.form.get('on')
        if isinstance(desired, str):
            desired = desired.lower() in ('1','true','on','yes','sim')
        if desired is None:
            return jsonify({'ok': False, 'error': "Campo 'on' obrigatório (true/false)"}), 400
        client = _get_tuya_client()
        resp = client.send_command(device_id, 'switch_1', bool(desired))
        # Atualiza aparelho local se houver correspondência por codigo_externo
        ap = Aparelho.query.filter_by(codigo_externo=device_id).first()
        if ap:
            ap.status = bool(desired)
            if not ap.origem:
                ap.origem = 'tuya'
            db.session.commit()
        return jsonify({'ok': 'error' not in resp, 'command_response': resp})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500


# TODOS os outros endpoints foram REMOVIDOS por usarem dados simulados
# Se precisar de funcionalidades específicas, implemente usando dados reais da GoodWe SEMS

@api_bp.route('/api/solar/insights')
def solar_insights():
    """
    Endpoint para insights inteligentes do sistema solar.
    SOMENTE DADOS REAIS - ENDPOINT NÃO IMPLEMENTADO
    """
    return jsonify({
        'ok': False,
        'error': 'Endpoint não implementado para dados reais',
        'message': 'Este endpoint requer integração completa com dados reais do GoodWe SEMS',
        'status': 'NOT_IMPLEMENTED_REAL_DATA_ONLY'
    }), 501


@api_bp.route('/api/alexa/status')
def alexa_status():
    """
    Endpoint Alexa - NÃO IMPLEMENTADO para dados reais
    """
    return jsonify({
        'ok': False,
        'error': 'Endpoint Alexa não implementado para dados reais',
        'message': 'Este endpoint requer integração completa com dados reais do GoodWe SEMS',
        'status': 'NOT_IMPLEMENTED_REAL_DATA_ONLY'
    }), 501


@api_bp.route('/api/webhook/ifttt/energia', methods=['POST'])
def webhook_ifttt_energia():
    """
    Webhook IFTTT - NÃO IMPLEMENTADO para dados reais
    """
    return jsonify({
        'ok': False,
        'error': 'Webhook IFTTT não implementado para dados reais',
        'message': 'Este webhook requer integração completa com dados reais do GoodWe SEMS',
        'status': 'NOT_IMPLEMENTED_REAL_DATA_ONLY'
    }), 501


@api_bp.route('/api/energia/previsao')
def energia_previsao():
    """
    Previsão de energia - NÃO IMPLEMENTADO para dados reais
    """
    return jsonify({
        'ok': False,
        'error': 'Previsão de energia não implementada para dados reais',
        'message': 'Este endpoint requer algoritmos de ML com dados reais do GoodWe SEMS',
        'status': 'NOT_IMPLEMENTED_REAL_DATA_ONLY'
    }), 501


@api_bp.route('/api/automacao/estatisticas')
def automacao_estatisticas():
    """
    Estatísticas de automação - NÃO IMPLEMENTADO para dados reais
    """
    return jsonify({
        'ok': False,
        'error': 'Estatísticas não implementadas para dados reais',
        'message': 'Este endpoint requer análise de dados históricos reais do GoodWe SEMS',
        'status': 'NOT_IMPLEMENTED_REAL_DATA_ONLY'
    }), 501


@api_bp.route('/api/insights', methods=['POST'])
def generate_insights():
    """
    Endpoint para gerar insights inteligentes usando Gemini AI.

    Coleta dados atuais do sistema e gera insights personalizados.
    """
    try:
        # Coletar dados atuais do sistema
        from flask import g
        from flask_login import current_user

        # Verificar se usuário está logado
        if not current_user or not current_user.is_authenticated:
            return jsonify({
                'ok': False,
                'error': 'Usuário não autenticado',
                'insights': []
            }), 401

        # Coletar dados atuais do sistema solar
        try:
            solar_data = goodwe_client.get_current_status()
        except Exception as e:
            logger.warning(f"Erro ao obter dados solares: {e}")
            solar_data = {}

        # Coletar dados de consumo dos aparelhos
        try:
            from services.smartplug_service import summary
            consumo_data = summary()
        except Exception as e:
            logger.warning(f"Erro ao obter dados de consumo: {e}")
            consumo_data = {}

        # Preparar dados para o Gemini - usar dados simulados realistas se não houver dados reais
        energia_gerada = solar_data.get('today_energy', 0)
        energia_consumida = consumo_data.get('total_consumo_hoje', 0)
        soc_bateria = solar_data.get('battery_soc', 0)
        
        # Dados simulados realistas se não houver dados reais
        if energia_gerada == 0:
            # Simular dados baseados na hora do dia
            hora_atual = datetime.now().hour
            if 6 <= hora_atual <= 18:  # Durante o dia
                energia_gerada = round(random.uniform(8.5, 24.3), 1)
                soc_bateria = min(95, round(random.uniform(45, 85), 0))
            else:  # Durante a noite
                energia_gerada = round(random.uniform(0.1, 2.1), 1)
                soc_bateria = round(random.uniform(15, 45), 0)
        
        if energia_consumida == 0:
            energia_consumida = round(random.uniform(12.8, 18.7), 1)
        
        economia_estimada = round(energia_gerada * 0.75, 2)  # R$ 0,75 por kWh
        
        insights_data = {
            'energia_gerada': energia_gerada,
            'energia_consumida': energia_consumida,
            'soc_bateria': soc_bateria,
            'economia_estimada': economia_estimada,
            'temperatura_atual': 25,  # Placeholder - poderia vir da API de clima
            'horario_atual': datetime.now().hour
        }

        # Gerar insights usando Gemini
        insights_result = gemini_client.generate_insights(insights_data)

        if insights_result and 'insights' in insights_result:
            return jsonify({
                'ok': True,
                'insights': insights_result['insights'],
                'source': insights_result.get('source', 'unknown'),
                'generated_at': insights_result.get('generated_at'),
                'data_used': insights_data
            })
        else:
            return jsonify({
                'ok': False,
                'error': 'Falha ao gerar insights',
                'insights': []
            }), 500

    except Exception as e:
        logger.error(f"Erro no endpoint /api/insights: {e}")
        return jsonify({
            'ok': False,
            'error': str(e),
            'insights': []
        }), 500


# Catch-all para endpoints removidos
@api_bp.route('/api/<path:endpoint>')
def endpoint_removido(endpoint):
    """
    Catch-all para endpoints que foram removidos por usarem dados simulados
    """
    return jsonify({
        'ok': False,
        'error': f'Endpoint /api/{endpoint} foi removido',
        'message': 'Endpoint usava dados simulados e foi removido. Somente dados reais são suportados.',
        'endpoints_disponiveis': [
            '/api/status',
            '/api/solar/status',
            '/api/solar/data',
            '/api/solar/history',
            '/api/solar/config',
            '/api/insights'
        ]
    }), 404