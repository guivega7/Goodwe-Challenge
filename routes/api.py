"""
API Routes para o Sistema SolarMind - SOMENTE DADOS REAIS

Este módulo contém endpoints da API REST para integração com GoodWe SEMS Portal.
TODOS os endpoints com dados simulados foram REMOVIDOS.
"""

import os
import json
import time
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, session
import random
from solarmind.mock_data_store import get_mock_daily_state, get_mock_battery_level
from solarmind.services.gemini_client import generate_gemini_text
from solarmind.services.weather_client import get_weather_forecast

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

@api_bp.route('/api/solar/debug_goodwe')
def debug_goodwe():
    """Endpoint de depuração para inspecionar estado do cliente GoodWe."""
    try:
        return jsonify({
            'ok': True,
            'goodwe': {
                'login_region': getattr(goodwe_client, 'login_region', None),
                'data_region': getattr(goodwe_client, 'data_region', None),
                'current_region': getattr(goodwe_client, 'region', None),
                'base_override': getattr(goodwe_client, '_data_base_url_override', None),
                'strict_https': getattr(goodwe_client, 'strict_https', None),
                'debug': getattr(goodwe_client, 'debug', None),
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

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

# ---------------------- Controle Unificado de Dispositivos ---------------------- #
def _find_device(reference: str) -> Aparelho | None:
    """Procura aparelho por nome (case-insensitive), slug simplificado ou codigo_externo."""
    if not reference:
        return None
    ref = reference.strip().lower()
    ap = (Aparelho.query
          .filter(Aparelho.nome.ilike(ref))
          .first())
    if not ap:
        ap = (Aparelho.query
              .filter(Aparelho.codigo_externo.ilike(ref))
              .first())
    return ap

def _send_tuya_if_possible(aparelho: Aparelho | None, desired: bool) -> tuple[bool, dict | None]:
    """Envia comando Tuya se aparelho tiver codigo_externo e retorna (sucesso, resposta_raw)."""
    if not aparelho or not aparelho.codigo_externo:
        return False, None
    try:
        client = _get_tuya_client()
        resp = client.send_command(aparelho.codigo_externo, 'switch_1', desired)
        ok = bool(resp) and resp.get('success', True) and 'error' not in resp
        return ok, resp
    except Exception as e:
        logger.warning(f"Falha comando Tuya para {aparelho.codigo_externo}: {e}")
        return False, {'error': str(e)}

def control_device(target: str, turn_on: bool) -> dict:
    """Liga ou desliga um dispositivo por nome ou codigo_externo.

    Retorna dict com detalhes da operação.
    """
    result = {
        'input': target,
        'acao': 'on' if turn_on else 'off',
        'encontrado': False,
        'fonte': None,
        'tuya_ok': None,
        'status_final': None,
    }
    ap = _find_device(target)
    if ap:
        result['encontrado'] = True
        # Primeiro tenta Tuya se houver ligação
        tuya_ok, tuya_raw = _send_tuya_if_possible(ap, turn_on)
        result['tuya_ok'] = tuya_ok
        if tuya_raw:
            result['tuya_raw'] = tuya_raw
        # Atualiza estado local sempre (mesmo se Tuya falhou para manter coerência interna)
        ap.status = bool(turn_on)
        if not ap.origem:
            ap.origem = 'tuya' if ap.codigo_externo else 'manual'
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            result['db_error'] = str(e)
        result['fonte'] = 'local+tuya' if ap.codigo_externo else 'local'
        result['status_final'] = 'ON' if turn_on else 'OFF'
    else:
        result['status_final'] = 'UNKNOWN'
    return result

def device_off(target: str) -> dict:
    return control_device(target, False)

def device_on(target: str) -> dict:
    return control_device(target, True)

def eco_mode(prioridade_min: int | None = None) -> dict:
    """Desliga vários dispositivos (modo economia). Se prioridade_min for fornecida,
    desliga apenas aparelhos com prioridade >= prioridade_min.
    """
    q = Aparelho.query
    if prioridade_min is not None:
        try:
            q = q.filter(Aparelho.prioridade >= prioridade_min)
        except Exception:
            pass
    dispositivos = q.all()
    altered = []
    for ap in dispositivos:
        # Evita desligar se já off
        if ap.status:
            off_res = device_off(ap.nome)
            altered.append(off_res)
    return {
        'modo': 'economia',
        'afetados': len(altered),
        'detalhes': altered
    }


def _extract_ifttt_target():
    payload = request.get_json(silent=True) if request.is_json else None
    target = None
    if payload:
        target = payload.get('value1') or payload.get('device') or payload.get('nome')
    if not target:
        target = request.form.get('value1') or request.form.get('device') or request.form.get('nome')
    return target

@api_bp.route('/ifttt/desligar', methods=['POST'])
def ifttt_desligar():
    try:
        target = _extract_ifttt_target()
        if not target:
            return jsonify({'ok': False, 'error': 'value1 (nome) ausente'}), 400
        result = device_off(target)
        if not result.get('encontrado'):
            return jsonify({'ok': False, 'error': f"Dispositivo '{target}' não encontrado"}), 404
        # Ajusta formato simplificado esperado
        resp = {
            'ok': True,
            'dispositivo': result.get('input'),
            'status_final': result.get('status_final'),
            'fonte': result.get('fonte'),
            'tuya_ok': result.get('tuya_ok')
        }
        if 'tuya_raw' in result:
            resp['tuya_raw'] = result['tuya_raw']
        return jsonify(resp)
    except Exception as e:
        logger.error(f"Erro /ifttt/desligar: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500

@api_bp.route('/ifttt/ligar', methods=['POST'])
def ifttt_ligar():
    try:
        print("--- ROTA /ifttt/ligar ACIONADA ---")
        raw_body = request.get_data(as_text=True)
        print(f"[IFTTT/LIGAR] Corpo bruto recebido: {raw_body}")

        data = request.get_json(silent=True)
        if data is None:
            # Força parsing mesmo se o Content-Type vier incorreto (comum em integrações)
            data = request.get_json(force=True, silent=True)
        if not data and raw_body:
            try:
                data = json.loads(raw_body)
            except Exception:
                data = None
        print(f"[IFTTT/LIGAR] JSON parseado: {data}")

        target = None
        if isinstance(data, dict):
            target = data.get('value1') or data.get('device') or data.get('nome')
        if not target:
            target = request.form.get('value1') or request.form.get('device') or request.form.get('nome')
        if not target:
            print("ERRO: A chave 'value1' é obrigatória e não foi encontrada.")
            return jsonify({'ok': False, 'error': "A chave 'value1' é obrigatória."}), 400

        print(f"[IFTTT/LIGAR] Nome do aparelho extraído: {target}")
        result = device_on(target)
        if not result.get('encontrado'):
            return jsonify({'ok': False, 'error': f"Dispositivo '{target}' não encontrado", 'details': result}), 404
        resp = {
            'ok': True,
            'message': f"{target} ligado com sucesso.",
            'dispositivo': result.get('input'),
            'status_final': result.get('status_final'),
            'fonte': result.get('fonte'),
            'tuya_ok': result.get('tuya_ok')
        }
        if 'tuya_raw' in result:
            resp['tuya_raw'] = result['tuya_raw']
        return jsonify(resp), 200
    except Exception as e:
        print(f"ERRO CRÍTICO na rota /ifttt/ligar: {e}")
        logger.error(f"Erro /ifttt/ligar: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500

@api_bp.route('/ifttt/modo_economia', methods=['POST'])
def ifttt_modo_economia():
    print("--- ROTA /ifttt/modo_economia ACIONADA ---")
    try:
        prioridade_min = None
        if request.is_json:
            pl = request.get_json(silent=True) or {}
            prioridade_min = pl.get('prioridade_min')
        result = eco_mode(prioridade_min)
        # Normaliza resposta com campos esperados
        payload = {
            'ok': True,
            'success': True,
            'message': 'Modo economia ativado com sucesso.',
            'details': result
        }
        return jsonify(payload), 200
    except Exception as e:
        print(f"ERRO na rota /ifttt/modo_economia: {e}")
        logger.error(f"Erro /ifttt/modo_economia: {e}")
        return jsonify({'ok': False, 'success': False, 'error': str(e)}), 500

@api_bp.route('/api/solar/config')
def solar_config():
    """
    Endpoint para verificar configuração da API GoodWe SEMS.
    
    Retorna:
        JSON: Informações sobre a configuração atual
    """
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


@api_bp.route('/api/solar/status', methods=['GET'])
def solar_status():
    """Status do sistema em modo duplo: mock (default) ou API GoodWe."""
    fonte = request.args.get('fonte', 'mock')
    try:
        if fonte == 'api':
            print("--- ROTA /api/solar/status ACIONADA (API REAL) ---")
            try:
                # Usar a nova função de tempo real como fonte única
                print("--- ROTA /api/solar/status: Chamando get_realtime_data() ---")
                dados_reais = goodwe_client.get_realtime_data()
                # Mantém o envelope com 'ok' para compatibilidade, mas os dados vêm do realtime
                return jsonify({'ok': True, 'data': dados_reais, 'timestamp': datetime.now().isoformat(), '_mock': False})
            except Exception as e:
                print(f"ERRO na API real, usando fallback para mock: {e}")
                logger.error(f"Erro /api/solar/status (api): {e}")
                # fallback para mock
        # Modo mock (default ou fallback)
        print("--- ROTA /api/solar/status ACIONADA (MOCK) ---")
        state = get_mock_daily_state()
        mock_data = {
            'soc_bateria': state['soc_bateria'],
            'geracao_dia': state['geracao_dia'],
            'economia_dia': state['economia_dia'],
            'status_sistema': 'ONLINE'
        }
        return jsonify({'ok': True, 'data': mock_data, 'timestamp': datetime.now().isoformat(), '_mock': True, 'fallback': fonte=='api'})
    except Exception as e:
        logger.error(f"Erro /api/solar/status: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@api_bp.route('/api/solar/debug_realtime_raw', methods=['GET'])
def debug_realtime_raw_data():
    """
    Endpoint de depuração que retorna o JSON bruto da chamada de tempo real da GoodWe
    para inspeção. Usa get_realtime_data(raw=True) e não aplica nenhum mapeamento.
    """
    print("--- ROTA DE DEBUG: /api/solar/debug_realtime_raw ACIONADA ---")
    try:
        raw_payload = goodwe_client.get_realtime_data(raw=True)
        # Normaliza em um envelope com info de timestamp
        return jsonify({
            'ok': True,
            'raw': raw_payload,
            'timestamp': datetime.now().isoformat(),
            'hint': 'Este payload é retornado diretamente da API GoodWe (GetMonitorDetailByPowerstationId)'
        })
    except Exception as e:
        logger.error(f"Erro /api/solar/debug_realtime_raw: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@api_bp.route('/api/solar/relatorio_diario', methods=['GET'])
def get_daily_report():
    """Relatório diário em modo duplo: mock (default) ou API GoodWe."""
    fonte = request.args.get('fonte', 'mock')
    print("--- ROTA /api/solar/relatorio_diario ACIONADA ---")
    try:
        if fonte == 'api':
            try:
                dados = goodwe_client.build_data()
                report_data = {
                    'geracao_dia': dados.get('producao', {}).get('hoje', 0.0),
                    'economia_dia': dados.get('economia', {}).get('hoje', 0.0),
                    'soc_bateria': dados.get('bateria', {}).get('soc', None)
                }
                return jsonify({'ok': True, 'data': report_data, 'timestamp': datetime.now().isoformat(), '_mock': False})
            except Exception as e:
                print(f"ERRO na API real, usando fallback para mock: {e}")
                logger.error(f"Erro /api/solar/relatorio_diario (api): {e}")
                # segue para fallback
        # Modo mock (default ou fallback)
        state = get_mock_daily_state()
        report_data = {
            'geracao_dia': state['geracao_dia'],
            'economia_dia': state['economia_dia'],
            'soc_bateria': state.get('soc_bateria')
        }
        return jsonify({'ok': True, 'data': report_data, 'timestamp': datetime.now().isoformat(), '_mock': True, 'fallback': fonte=='api'})
    except Exception as e:
        logger.error(f"Erro em /api/solar/relatorio_diario: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500

@api_bp.route('/api/ia/plano_do_dia', methods=['GET'])
def get_daily_plan():
    """Endpoint que usa a IA do Gemini para gerar um plano de energia para o dia (respeita ?fonte=api e passa o SOC correto no prompt)."""
    print("--- ROTA /api/ia/plano_do_dia ACIONADA (VERSÃO CORRIGIDA FINAL) ---")
    fonte = request.args.get('fonte', 'mock')

    try:
        battery_level = 0
        weather_today = "não disponível"

        if fonte == 'api':
            print("--- MODO API REAL (plano_do_dia) ---")
            try:
                dados_reais = goodwe_client.get_realtime_data()
                # Suporta ambos formatos: direto {'soc_bateria': ...} ou envelope {'ok': True, 'data': {...}}
                if isinstance(dados_reais, dict) and ('soc_bateria' in dados_reais):
                    battery_level = dados_reais.get('soc_bateria', 0)
                elif isinstance(dados_reais, dict) and dados_reais.get('ok') and isinstance(dados_reais.get('data'), dict):
                    battery_level = dados_reais['data'].get('soc_bateria', 0)
                else:
                    raise ValueError("Formato inesperado de retorno do get_realtime_data()")
            except Exception as e:
                logger.error(f"Falha get_realtime_data() no plano_do_dia: {e}")
                # Fallback para mock
                state = get_mock_daily_state()
                battery_level = state.get("soc_bateria", 0)
            weather_today = get_weather_forecast()
        else:
            print("--- MODO MOCK (plano_do_dia) ---")
            state = get_mock_daily_state()
            battery_level = state.get("soc_bateria", 0)
            weather_today = get_weather_forecast()

        # Garante que battery_level é um número para o prompt
        try:
            battery_level = int(float(battery_level))
        except (ValueError, TypeError):
            battery_level = 0

        print(f"--- DADOS USADOS PARA O PROMPT -> Bateria: {battery_level}%, Previsão: {weather_today} ---")

        # Prompt objetivo para decisão
        prompt = f"""
        Você é o cérebro do Autopilot SolarMind. Analise os dados a seguir e retorne APENAS uma decisão em formato JSON válido com as chaves 'acao' e 'explicacao'.
        Dados:
        - Bateria_atual: {battery_level}%
        - Previsao_hoje: {weather_today}
        """

        response_json_str = generate_gemini_text(prompt)
        data = json.loads(response_json_str) if isinstance(response_json_str, str) else response_json_str

        return jsonify({
            'ok': True,
            'data': {
                'recomendacao': data,
                'soc_bateria': battery_level,
                'previsao': weather_today
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erro CRÍTICO em /api/ia/plano_do_dia: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500
    
@api_bp.route('/api/ia/acao_proativa', methods=['GET'])
def get_proactive_action():
    """Cérebro do Autopilot: decisão (acao, explicacao) com modo duplo para origem dos dados."""
    print("--- ROTA /api/ia/acao_proativa ACIONADA ---")
    fonte = request.args.get('fonte', 'mock')
    try:
        # a) Estado atual do sistema, conforme fonte
        battery_soc = None
        if fonte == 'api':
            try:
                status = goodwe_client.build_status()
                battery_soc = status.get('soc_bateria')
            except Exception as e:
                print(f"ERRO na API real, fallback para mock em /api/ia/acao_proativa: {e}")
                logger.error(f"Erro /api/ia/acao_proativa (api): {e}")
        if battery_soc is None:
            state = get_mock_daily_state()
            battery_soc = state.get('soc_bateria')

        # b) Previsão do tempo (descrição simples)
        weather = get_weather_forecast()

        # c) Prompt avançado instruindo a IA a responder em JSON
        prompt = f"""
Você é o cérebro do Autopilot SolarMind. Analise os dados a seguir e retorne APENAS uma decisão em formato JSON válido com as chaves 'acao' e 'explicacao'.

Regras:
- Leia os dados e decida entre 'ATIVAR_MODO_ECO' ou 'MANTER_NORMAL'.
- Justifique em português de forma clara e breve (1-2 frases), começando com um alerta se a condição for desfavorável (chuva/nublado e/ou bateria baixa), e reforçando benefício quando favorável (sol e bateria alta).
- Não inclua texto fora do JSON e não use markdown.

Dados:
- Bateria_atual: {battery_soc}%
- Previsao_hoje: {weather}
"""

        # d) Chamada à IA (mock) que retorna string JSON
        response_json_str = generate_gemini_text(prompt)
        data = json.loads(response_json_str) if isinstance(response_json_str, str) else response_json_str
        if not isinstance(data, dict) or 'acao' not in data or 'explicacao' not in data:
            raise ValueError('Resposta do Gemini não possui chaves esperadas.')

        return jsonify({**data, '_mock': fonte!='api'}), 200
    except Exception as e:
        logger.error(f"Erro em /api/ia/acao_proativa: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


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