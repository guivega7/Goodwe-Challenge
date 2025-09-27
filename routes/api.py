"""
API Routes para o Sistema SolarMind

Este módulo contém todos os endpoints da API REST para:
- Integração com assistentes inteligentes (Alexa, Google Home)
- Webhooks IFTTT para automação
- Alertas inteligentes do sistema solar
- IA para análise e previsão de consumo
- Automação residencial
"""

import random
import os
from datetime import datetime
from flask import Blueprint, jsonify, request
import asyncio
import base64
import json
import requests

from extensions import db
from models.aparelho import Aparelho
from models.usuario import Usuario
from utils.energia import dispara_alerta, dispara_alerta_economia
from services.energy_autopilot import build_daily_plan
from utils.logger import get_logger
from routes.auth import login_required
from services.scheduler import get_jobs_info
from services.gemini_client import gemini_client
from services.goodwe_client import GoodWeClient

logger = get_logger(__name__)

api_bp = Blueprint('api', __name__)

BASE_SEMS = {
    "us": "https://us.semsportal.com",
    "eu": "https://eu.semsportal.com",
}

def _initial_token_prof():
    original = {"uid": "", "timestamp": 0, "token": "", "client": "web", "version": "", "language": "en"}
    b = json.dumps(original).encode("utf-8")
    return base64.b64encode(b).decode("utf-8")

@api_bp.route('/api/status')
def status():
    """
    Endpoint de status da API.
    
    Retorna:
        JSON: Status de funcionamento da API
    """
    return jsonify({
        'ok': True, 
        'msg': 'API SolarMind funcionando',
        'timestamp': datetime.now().isoformat()
    })


@api_bp.route('/api/scheduler/health')
def scheduler_health():
    try:
        jobs = get_jobs_info()
        return jsonify({
            'scheduler': 'ok' if jobs is not None else 'disabled',
            'jobs': jobs,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'scheduler': 'error', 'error': str(e)}), 500


@api_bp.route('/api/gemini/test')
def gemini_test():
    """Testa conexão com Gemini e retorna status."""
    try:
        result = gemini_client.test_connection()
        status_code = 200 if result['status'] == 'success' else 503
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': f'Erro interno: {str(e)}'
        }), 500


@api_bp.route('/api/insights', methods=['POST'])
@login_required
def gerar_insights():
    """
    Gera insights sobre o sistema solar usando Gemini.
    
    Corpo JSON esperado:
        energia_gerada: float (kWh)
        energia_consumida: float (kWh) 
        soc_bateria: float (0-100)
    """
    try:
        data = request.get_json() or {}
        
        energia_gerada = float(data.get('energia_gerada', 0))
        energia_consumida = float(data.get('energia_consumida', 0))
        soc_bateria = float(data.get('soc_bateria', 0))
        
        # Usa os dados para gerar insights
        insights_data = {
            'energia_gerada': energia_gerada,
            'energia_consumida': energia_consumida,
            'soc_bateria': soc_bateria
        }
        
        insights = gemini_client.generate_insights(insights_data)
        
        return jsonify({
            'status': 'sucesso',
            'insights': insights,
            'dados': insights_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except ValueError as e:
        return jsonify({
            'status': 'erro',
            'mensagem': 'Parâmetros inválidos'
        }), 400
    except Exception as e:
        logger.error(f"Erro ao gerar insights: {e}")
        return jsonify({
            'status': 'erro',
            'mensagem': f'Erro interno: {str(e)}'
        }), 500


# ========== INTEGRAÇÃO COM ASSISTENTES INTELIGENTES ==========
@api_bp.route('/ifttt/desligar', methods=['POST'])
def ifttt_desligar():
    """
    Desliga aparelho via IFTTT Webhooks.
    
    Parâmetros esperados:
        value1 (str): Nome do aparelho a ser desligado
        
    Retorna:
        JSON: Status da operação e mensagem
    """
    try:
        data = request.get_json() or {}
        nome = data.get('value1') or data.get('nome')
        
        if not nome:
            return jsonify({
                'status': 'erro', 
                'msg': 'Nome do aparelho não fornecido'
            }), 400

        usuario_id = 1
        aparelho = Aparelho.query.filter_by(nome=nome, usuario_id=usuario_id).first()
        
        if not aparelho:
            return jsonify({
                'status': 'erro', 
                'msg': f'Aparelho {nome} não encontrado'
            }), 404

        if not aparelho.status:
            return jsonify({
                'status': 'ok', 
                'msg': f'{nome} já estava desligado'
            })

        aparelho.status = False
        db.session.commit()
        
        return jsonify({
            'status': 'ok', 
            'msg': f'{nome} desligado com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'erro', 
            'msg': f'Erro interno: {str(e)}'
        }), 500

@api_bp.route('/api/assistente/alexa', methods=['POST'])
def aciona_alexa():
    """
    Endpoint para integração com assistentes inteligentes (Alexa/Google Home).
    
    Parâmetros esperados:
        evento (str): Tipo do evento a ser disparado
        mensagem (str): Mensagem a ser enviada
        
    Retorna:
        JSON: Status da operação e detalhes do evento
    """
    try:
        data = request.get_json()
        evento = data.get('evento')
        mensagem = data.get('mensagem', 'Evento Alexa disparado')
        
        # Simula resposta da Alexa
        resposta = {
            'status': 'sucesso',
            'evento': evento,
            'mensagem': mensagem,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Evento Alexa disparado: {evento} - {mensagem}")
        return jsonify(resposta)
        
    except Exception as e:
        logger.error(f"Erro no endpoint Alexa: {str(e)}")
        return jsonify({
            'status': 'erro',
            'mensagem': f'Erro interno: {str(e)}'
        }), 500


@api_bp.route('/api/test/low-battery', methods=['POST'])
def test_low_battery():
    """
    Endpoint de teste para simular evento de bateria baixa.
    
    Parâmetros esperados (opcionais):
        battery_level (int): Nível da bateria (default: 15%)
        location (str): Local do sistema (default: "Sistema SolarMind")
        
    Retorna:
        JSON: Status da operação e webhooks disparados
    """
    try:
        data = request.get_json() or {}
        battery_level = data.get('battery_level', 15)
        location = data.get('location', 'Sistema SolarMind')
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # Monta payload para IFTTT
        webhook_data = {
            'value1': location,
            'value2': f'{battery_level}%',
            'value3': timestamp
        }
        
        # Dispara webhook IFTTT de bateria baixa
        webhook_url = os.environ.get('WEBHOOK_LOW_BATTERY')
        if webhook_url:
            import requests
            response = requests.post(webhook_url, json=webhook_data)
            webhook_success = response.status_code == 200
        else:
            webhook_success = False
            
        # Log do evento
        logger.warning(f"🔋 BATERIA BAIXA: {location} - {battery_level}% às {timestamp}")
        
        return jsonify({
            'status': 'sucesso',
            'evento': 'low_battery',
            'dados': {
                'local': location,
                'nivel_bateria': f'{battery_level}%',
                'timestamp': timestamp,
                'webhook_enviado': webhook_success,
                'webhook_url': webhook_url is not None
            },
            'mensagem': f'Alerta de bateria baixa disparado: {location} com {battery_level}%'
        })
        
    except Exception as e:
        logger.error(f"Erro no teste de bateria baixa: {str(e)}")
        return jsonify({
            'status': 'erro',
            'mensagem': f'Erro interno: {str(e)}'
        }), 500


@api_bp.route('/api/test/alexa-battery', methods=['POST'])
def test_alexa_battery():
    """
    Endpoint específico para testar resposta da Alexa sobre bateria baixa.
    
    Dispara múltiplos webhooks para garantir que a Alexa responda.
    """
    try:
        data = request.get_json() or {}
        battery_level = data.get('battery_level', 10)
        location = data.get('location', 'Casa')
        
        # Timestamp atual
        now = datetime.now()
        timestamp = now.strftime("%H:%M")
        
        # Múltiplos webhooks para aumentar chance de resposta
        webhooks_disparados = []
        
        # 1. Low Battery webhook
        webhook_low = os.environ.get('WEBHOOK_LOW_BATTERY')
        if webhook_low:
            import requests
            payload = {
                'value1': f'ALERTA {location}',
                'value2': f'BATERIA {battery_level}%',
                'value3': f'AGORA {timestamp}'
            }
            try:
                response = requests.post(webhook_low, json=payload, timeout=10)
                webhooks_disparados.append({
                    'tipo': 'low_battery',
                    'sucesso': response.status_code == 200,
                    'resposta': response.text
                })
            except Exception as e:
                webhooks_disparados.append({
                    'tipo': 'low_battery',
                    'sucesso': False,
                    'erro': str(e)
                })
        
        # 2. Falha Inversor webhook (como backup)
        webhook_falha = os.environ.get('WEBHOOK_FALHA_INVERSOR')
        if webhook_falha:
            import requests
            payload = {
                'value1': f'BATERIA CRÍTICA',
                'value2': f'{location} - {battery_level}%',
                'value3': f'Emergência às {timestamp}'
            }
            try:
                response = requests.post(webhook_falha, json=payload, timeout=10)
                webhooks_disparados.append({
                    'tipo': 'falha_inversor',
                    'sucesso': response.status_code == 200,
                    'resposta': response.text
                })
            except Exception as e:
                webhooks_disparados.append({
                    'tipo': 'falha_inversor',
                    'sucesso': False,
                    'erro': str(e)
                })
        
        # Log detalhado
        logger.warning(f"🔊 ALEXA TEST: {location} - Bateria {battery_level}% - {len(webhooks_disparados)} webhooks disparados")
        
        return jsonify({
            'status': 'sucesso',
            'evento': 'alexa_battery_test',
            'dados': {
                'local': location,
                'nivel_bateria': f'{battery_level}%',
                'timestamp': timestamp,
                'webhooks_disparados': len(webhooks_disparados),
                'detalhes_webhooks': webhooks_disparados
            },
            'mensagem': f'Teste Alexa: {len(webhooks_disparados)} webhooks enviados para {location} com bateria {battery_level}%',
            'dica': 'Verifique se o IFTTT está conectado à Alexa e os applets estão ativos'
        })
        
    except Exception as e:
        logger.error(f"Erro no teste Alexa: {str(e)}")
        return jsonify({
            'status': 'erro',
            'mensagem': f'Erro interno: {str(e)}'
        }), 500


@api_bp.route('/api/debug/webhooks', methods=['GET'])
def debug_webhooks():
    """
    Endpoint de debug para verificar configuração dos webhooks.
    """
    try:
        webhooks_config = {
            'WEBHOOK_LOW_BATTERY': os.environ.get('WEBHOOK_LOW_BATTERY', 'NÃO CONFIGURADO'),
            'WEBHOOK_FALHA_INVERSOR': os.environ.get('WEBHOOK_FALHA_INVERSOR', 'NÃO CONFIGURADO'),
            'IFTTT_KEY': os.environ.get('IFTTT_KEY', 'NÃO CONFIGURADO'),
            'env_loaded': bool(os.environ.get('SEMS_ACCOUNT'))
        }
        
        return jsonify({
            'status': 'debug',
            'webhooks': webhooks_config,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'erro',
            'mensagem': f'Erro no debug: {str(e)}'
        }), 500
    try:
        data = request.get_json() or {}
        evento = data.get('evento', 'geral')
        mensagem = data.get('mensagem', 'Ação solicitada!')
        
        dispara_alerta(evento, mensagem)
        
        return jsonify({
            'status': 'sucesso', 
            'evento': evento,
            'mensagem': mensagem,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'erro', 
            'detalhes': str(e)
        }), 500

# ========== ENDPOINTS ESPECÍFICOS PARA EVENTOS IFTTT ==========

@api_bp.route('/api/alertas/manutencao', methods=['POST'])
def alerta_manutencao():
    """
    Dispara alerta de manutenção preventiva do sistema solar.
    
    Retorna:
        JSON: Confirmação do alerta enviado
    """
    try:
        mensagem = "Manutenção preventiva recomendada para o sistema solar!"
        dispara_alerta('manutencao', mensagem)
        
        return jsonify({
            'status': 'alerta_enviado', 
            'tipo': 'manutencao', 
            'mensagem': mensagem
        })
        
    except Exception as e:
        return jsonify({
            'status': 'erro', 
            'detalhes': str(e)
        }), 500

@api_bp.route('/api/alertas/high_energy', methods=['POST'])
def alerta_alto_consumo():
    """
    Dispara alerta de alto consumo de energia.
    
    Parâmetros esperados:
        consumo (float): Valor do consumo detectado em kWh
        
    Retorna:
        JSON: Confirmação do alerta e dados do consumo
    """
    try:
        data = request.get_json() or {}
        consumo = data.get('consumo', 25.0)
        
        mensagem = f"Atenção! Consumo elevado detectado: {consumo} kWh. " \
                  f"Considere desligar aparelhos não essenciais."
        
        dispara_alerta('high_energy', mensagem)
        
        return jsonify({
            'status': 'alerta_enviado', 
            'tipo': 'high_energy', 
            'consumo': consumo
        })
        
    except Exception as e:
        return jsonify({
            'status': 'erro', 
            'detalhes': str(e)
        }), 500

@api_bp.route('/api/alertas/resumo_diario', methods=['POST'])
def resumo_diario():
    """
    Envia resumo diário do sistema solar.
    
    Parâmetros esperados:
        energia_gerada (float): Energia gerada em kWh (opcional)
        economia (float): Valor economizado em R$ (opcional)
        
    Retorna:
        JSON: Resumo do dia com energia gerada e economia
    """
    try:
        data = request.get_json() or {}
        energia_gerada = data.get('energia_gerada', round(random.uniform(15.0, 35.0), 1))
        economia = data.get('economia', round(energia_gerada * 0.75, 2))
        
        mensagem = f"Resumo do dia: {energia_gerada} kWh gerados, " \
                  f"R$ {economia} economizados. Sistema funcionando normalmente!"
        
        dispara_alerta('Resumo_diario', mensagem)
        
        return jsonify({
            'status': 'resumo_enviado', 
            'energia_gerada': energia_gerada,
            'economia': economia,
            'mensagem': mensagem
        })
        
    except Exception as e:
        return jsonify({
            'status': 'erro', 
            'detalhes': str(e)
        }), 500

@api_bp.route('/api/alertas/inversor', methods=['POST'])
def alerta_inversor():
    """
    Dispara alerta relacionado ao inversor do sistema solar.
    
    Parâmetros esperados:
        status (str): Status do problema detectado no inversor
        
    Retorna:
        JSON: Confirmação do alerta e detalhes do status
    """
    try:
        data = request.get_json() or {}
        status_inversor = data.get('status', 'instabilidade')
        
        mensagem = f"Inversor: {status_inversor} detectada. Verificação recomendada."
        dispara_alerta('inversor', mensagem)
        
        return jsonify({
            'status': 'alerta_enviado', 
            'tipo': 'inversor', 
            'detalhes': status_inversor
        })
        
    except Exception as e:
        return jsonify({
            'status': 'erro', 
        }), 500

@api_bp.route('/api/alertas/low_battery', methods=['POST'])
def alerta_bateria_baixa():
    """
    Dispara alerta de bateria baixa do sistema.
    
    Parâmetros esperados:
        soc (int): Percentual de carga da bateria (State of Charge)
        
    Retorna:
        JSON: Confirmação do alerta e nível da bateria
    """
    try:
        data = request.get_json() or {}
        soc = data.get('soc', 15)
        
        mensagem = f"Atenção! Bateria do sistema está baixa: {soc}%. " \
                  f"Verifique o sistema."
        
        dispara_alerta('low_battery', mensagem)
        
        return jsonify({
            'status': 'alerta_enviado', 
            'tipo': 'low_battery', 
            'soc': soc
        })
        
    except Exception as e:
        return jsonify({
            'status': 'erro', 
            'detalhes': str(e)
        }), 500

# ========== IA PARA ANÁLISE E PREVISÃO DE CONSUMO ==========

@api_bp.route('/api/ia/previsao_consumo', methods=['GET'])
def previsao_consumo():
    """
    IA para prever consumo baseado em padrões históricos.
    
    Analisa a hora atual e retorna uma previsão de consumo
    com recomendações baseadas em padrões de uso.
    
    Retorna:
        JSON: Previsão de consumo, categoria e recomendações
    """
    try:
        hora_atual = datetime.now().hour
        
        # Padrões de consumo baseados na hora do dia
        if 6 <= hora_atual <= 8:  # Manhã
            base_consumo = random.uniform(12.0, 18.0)
        elif 11 <= hora_atual <= 14:  # Almoço
            base_consumo = random.uniform(20.0, 28.0)
        elif 18 <= hora_atual <= 22:  # Noite
            base_consumo = random.uniform(15.0, 25.0)
        else:  # Madrugada
            base_consumo = random.uniform(5.0, 12.0)
        
        # Adiciona variação aleatória para simular comportamento real
        previsao = round(base_consumo * random.uniform(0.85, 1.15), 2)
        
        # Análise inteligente baseada na previsão
        if previsao > 25:
            recomendacao = "Alto consumo previsto. Considere otimizar uso de aparelhos."
            categoria = "alto"
        elif previsao > 15:
            recomendacao = "Consumo moderado previsto. Sistema funcionando normalmente."
            categoria = "normal"
        else:
            recomendacao = "Baixo consumo previsto. Ótima eficiência energética!"
            categoria = "baixo"
        
        return jsonify({
            'previsao_consumo_kwh': previsao,
            'categoria': categoria,
            'recomendacao': recomendacao,
            'hora_analise': hora_atual,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'erro',
            'detalhes': str(e)
        }), 500

@api_bp.route('/api/ia/aprendizado_padrao', methods=['GET'])
def aprendizado_padrao():
    """
    Simula aprendizado de padrões de consumo baseado em dados históricos.
    
    Analisa comportamentos e gera sugestões de economia inteligentes
    baseadas em padrões identificados no sistema.
    
    Retorna:
        JSON: Padrões identificados e sugestões de otimização
    """
    try:
        # Simula dados de aprendizado baseados em histórico
        padroes = {
            'periodo_pico': '18:00-21:00',
            'consumo_medio_diario': round(random.uniform(18.0, 28.0), 1),
            'eficiencia_sistema': round(random.uniform(85.0, 95.0), 1),
            'economia_mensal_estimada': round(random.uniform(150.0, 300.0), 2),
            'aparelhos_mais_usados': [
                'Ar condicionado', 
                'Chuveiro elétrico', 
                'Geladeira'
            ],
            'sugestoes_economia': [
                'Usar ar condicionado em modo econômico entre 18h-21h',
                'Programar aquecimento de água para horários de pico solar',
                'Considerar timer para aparelhos em standby'
            ]
        }
        
        return jsonify({
            'status': 'analise_concluida',
            'padroes_identificados': padroes,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'erro',
            'detalhes': str(e)
        }), 500

# ========== AUTOMAÇÃO RESIDENCIAL ==========

@api_bp.route('/api/automacao/aparelhos/<int:aparelho_id>/toggle', methods=['POST'])
def toggle_aparelho(aparelho_id):
    """
    Controla dispositivos da automação residencial.
    
    Parâmetros da URL:
        aparelho_id (int): ID do aparelho a ser controlado
        
    Parâmetros do corpo:
        acao (str): Ação a ser realizada (toggle, ligar, desligar)
        
    Retorna:
        JSON: Status da operação e detalhes do aparelho controlado
    """
    try:
        data = request.get_json() or {}
        acao = data.get('acao', 'toggle')
        
        # Mapeamento de aparelhos disponíveis
        aparelhos_disponiveis = {
            1: 'Ar condicionado',
            2: 'Aquecedor solar',
            3: 'Iluminação externa',
            4: 'Tomada inteligente',
            5: 'Sistema de irrigação'
        }
        
        nome_aparelho = aparelhos_disponiveis.get(
            aparelho_id, 
            f'Aparelho {aparelho_id}'
        )
        novo_status = 'ligado' if acao in ['ligar', 'toggle'] else 'desligado'
        
        # Envia comando via IFTTT para automação real
        evento_automacao = f"controle_aparelho_{aparelho_id}"
        mensagem_automacao = f"{nome_aparelho} foi {novo_status}"
        dispara_alerta(evento_automacao, mensagem_automacao)
        
        return jsonify({
            'aparelho_id': aparelho_id,
            'nome': nome_aparelho,
            'acao_realizada': acao,
            'novo_status': novo_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'erro',
            'detalhes': str(e)
        }), 500

@api_bp.route('/api/automacao/economia_inteligente', methods=['POST'])
def economia_inteligente():
    """
    Sistema inteligente de economia de energia.
    
    Analisa o consumo atual e sugere ações automatizadas
    para otimizar o uso de energia quando necessário.
    
    Parâmetros esperados:
        limite_kwh (float): Limite de consumo em kWh
        consumo_atual (float): Consumo atual em kWh
        
    Retorna:
        JSON: Status do consumo e ações sugeridas se necessário
    """
    try:
        data = request.get_json() or {}
        limite_consumo = data.get('limite_kwh', 20.0)
        consumo_atual = data.get(
            'consumo_atual', 
            round(random.uniform(15.0, 30.0), 1)
        )
        
        if consumo_atual > limite_consumo:
            # Dispara alerta inteligente de economia
            dispara_alerta_economia('high_energy', consumo_atual, limite_consumo)
            
            # Sugere ações automáticas para redução do consumo
            acoes_sugeridas = [
                'Reduzir temperatura do ar condicionado em 2°C',
                'Desligar aparelhos em standby',
                'Ativar modo econômico do aquecedor'
            ]
            
            excesso_percentual = round(
                ((consumo_atual / limite_consumo) - 1) * 100, 1
            )
            
            return jsonify({
                'status': 'acao_requerida',
                'consumo_atual': consumo_atual,
                'limite': limite_consumo,
                'excesso_percentual': excesso_percentual,
                'acoes_sugeridas': acoes_sugeridas,
                'alerta_enviado': True
            })
        else:
            margem_disponivel = round(limite_consumo - consumo_atual, 1)
            
            return jsonify({
                'status': 'consumo_normal',
                'consumo_atual': consumo_atual,
                'limite': limite_consumo,
                'margem_disponivel': margem_disponivel
            })
            
    except Exception as e:
        return jsonify({
            'status': 'erro',
            'detalhes': str(e)
        }), 500


@api_bp.route('/api/planejamento/hoje', methods=['GET'])
def planejamento_hoje():
    """
    Gera o plano do dia a partir do SoC e previsão (parâmetros opcionais):
    - soc: float (0-100)
    - forecast: float (kWh previstos)
    """
    try:
        soc_raw = request.args.get('soc', '35')
        forecast_raw = request.args.get('forecast', '8')
        soc = float(soc_raw)
        forecast = float(forecast_raw)
    except ValueError:
        return jsonify({'error': 'Parâmetros inválidos'}), 400

    plan = build_daily_plan(soc, forecast)
    return jsonify(plan), 200


@api_bp.route('/api/autopilot/announce', methods=['POST'])
@login_required
def autopilot_announce():
    """
    Dispara um anúncio do Plano do Dia para a Alexa via IFTTT Webhook.

    Corpo opcional (JSON):
      - message: string (mensagem pronta para a Alexa). Se ausente, o plano será calculado.
      - soc: float (0-100) — opcional, usado para recalcular o plano se message não vier.
      - forecast: float (kWh) — opcional, usado para recalcular o plano se message não vier.

    Retorna JSON com status e detalhes do envio.
    """
    try:
        data = request.get_json(silent=True) or {}
        msg = data.get('message')
        soc_raw = data.get('soc') if 'soc' in data else request.args.get('soc')
        forecast_raw = data.get('forecast') if 'forecast' in data else request.args.get('forecast')

        # Se não vier mensagem, tenta montar a partir do plano
        if not msg:
            try:
                soc = float(soc_raw) if soc_raw is not None else 35.0
                forecast = float(forecast_raw) if forecast_raw is not None else 8.0
            except ValueError:
                return jsonify({'status': 'erro', 'mensagem': 'Parâmetros inválidos'}), 400
            plan = build_daily_plan(soc, forecast)
            msg = plan.get('alexa_message') or 'Plano do dia disponível.'

        # Remove acentos para evitar cortes na fala (observação prática com Alexa)
        def _strip_accents(text: str) -> str:
            import unicodedata
            return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

        final_msg = _strip_accents(str(msg))

        webhooks = [
            os.environ.get('WEBHOOK_ALEXA_ANNOUNCE'),  # preferencial, se configurado
            os.environ.get('WEBHOOK_LOW_BATTERY'),
            os.environ.get('WEBHOOK_FALHA_INVERSOR')
        ]
        webhooks = [w for w in webhooks if w]
        if not webhooks:
            return jsonify({'status': 'erro', 'mensagem': 'Nenhum webhook configurado (.env)'}), 500

        import requests
        payload = {
            'value1': final_msg,
            'value2': 'autopilot',
            'value3': datetime.now().strftime('%H:%M')
        }
        details = []
        any_ok = False
        for idx, wh in enumerate(webhooks):
            try:
                resp = requests.post(wh, json=payload, timeout=10)
                ok = (resp.status_code == 200)
                any_ok = any_ok or ok
                details.append({
                    'webhook_index': idx,
                    'url_present': True,
                    'http_status': resp.status_code,
                    'ok': ok,
                    'body': (resp.text or '')[:300]
                })
            except Exception as e:
                logger.error(f"Erro ao chamar webhook {idx}: {e}")
                details.append({
                    'webhook_index': idx,
                    'url_present': True,
                    'ok': False,
                    'erro': str(e)
                })

        return jsonify({
            'status': 'sucesso' if any_ok else 'erro',
            'mensagem_enviada': final_msg,
            'resultados': details
        }), (200 if any_ok else 502)

    except Exception as e:
        logger.error(f"Erro no announce do Autopilot: {e}")
        return jsonify({'status': 'erro', 'mensagem': f'Erro interno: {str(e)}'}), 500


@api_bp.route('/api/goodwe/local', methods=['GET'])
def goodwe_local():
    """
    Endpoint para buscar dados do inversor GoodWe via rede local usando a biblioteca goodwe.
    Parâmetros:
        ip (str): IP do inversor na rede local
    Retorna:
        JSON: Dados de sensores do inversor ou erro
    """
    ip = request.args.get('ip')
    if not ip:
        return jsonify({'ok': False, 'msg': 'Parâmetro ?ip= obrigatório'}), 400
    try:
        import goodwe
        async def get_data():
            inverter = await goodwe.connect(ip)
            runtime_data = await inverter.read_runtime_data()
            sensors = [
                {'id': s.id_, 'name': s.name, 'unit': s.unit, 'value': runtime_data.get(s.id_)}
                for s in inverter.sensors() if s.id_ in runtime_data
            ]
            return sensors
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        sensors = loop.run_until_complete(get_data())
        return jsonify({'ok': True, 'sensors': sensors})
    except Exception as e:
        logger.error(f'Erro ao acessar GoodWe local: {e}')
        return jsonify({'ok': False, 'msg': str(e)}), 500


@api_bp.route('/api/goodwe/demo/login', methods=['GET'])
def goodwe_demo_login():
    """
    Testa login no SEMS Portal usando variáveis do .env (conta demo ou real).
    Retorna token se sucesso, erro caso contrário.
    """
    account = os.environ.get('SEMS_ACCOUNT')
    password = os.environ.get('SEMS_PASSWORD')
    region = os.environ.get('SEMS_LOGIN_REGION', 'us')
    if not account or not region:
        return jsonify({'ok': False, 'msg': 'Configure SEMS_ACCOUNT e SEMS_LOGIN_REGION no .env'}), 400
    try:
        client = GoodWeClient(region=region)
        token = client.crosslogin(account, password)
        if token:
            return jsonify({'ok': True, 'token': token})
        else:
            return jsonify({'ok': False, 'msg': 'Falha no login SEMS'}), 401
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500


@api_bp.route('/api/goodwe/demo/inverters', methods=['GET'])
def goodwe_demo_inverters():
    """
    Lista estações e inversores disponíveis na conta SEMS demo/configurada.
    """
    account = os.environ.get('SEMS_ACCOUNT')
    password = os.environ.get('SEMS_PASSWORD')
    region = os.environ.get('SEMS_LOGIN_REGION', 'us')
    if not account or not region:
        return jsonify({'ok': False, 'msg': 'Configure SEMS_ACCOUNT e SEMS_LOGIN_REGION no .env'}), 400
    try:
        client = GoodWeClient(region=region)
        token = client.crosslogin(account, password)
        if not token:
            return jsonify({'ok': False, 'msg': 'Falha no login SEMS'}), 401
        result = client.get_user_stations_and_inverters(token)
        return jsonify({'ok': True, 'result': result})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500


@api_bp.route('/api/goodwe/demo/inverter_data', methods=['GET'])
def goodwe_demo_inverter_data():
    """
    Retorna dados simulados ou reais do inversor demo/configurado (coluna Pac, Eday, Cbattery1).
    Parâmetros opcionais: column (default: Pac), date (YYYY-MM-DD, default: hoje)
    """
    account = os.environ.get('SEMS_ACCOUNT')
    password = os.environ.get('SEMS_PASSWORD')
    region = os.environ.get('SEMS_LOGIN_REGION', 'us')
    inverter_id = os.environ.get('SEMS_INV_ID')
    column = request.args.get('column', 'Pac')
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    if not account or not region or not inverter_id:
        return jsonify({'ok': False, 'msg': 'Configure SEMS_ACCOUNT, SEMS_LOGIN_REGION e SEMS_INV_ID no .env'}), 400
    try:
        client = GoodWeClient(region=region)
        token = client.crosslogin(account, password)
        if not token:
            return jsonify({'ok': False, 'msg': 'Falha no login SEMS'}), 401
        data = client.get_inverter_data_by_column(token, inverter_id, column, date)
        return jsonify({'ok': True, 'data': data})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500


@api_bp.route('/api/sems/login', methods=['POST'])
def sems_login():
    """
    Faz login no SEMS Portal e retorna o token pós-login (exemplo do professor).
    Espera JSON: {"account": ..., "password": ..., "region": "us" ou "eu"}
    Se não enviar, usa variáveis do .env.
    """
    data = request.get_json(silent=True) or {}
    account = data.get('account') or os.environ.get('SEMS_ACCOUNT')
    password = data.get('password') or os.environ.get('SEMS_PASSWORD')
    region = data.get('region') or os.environ.get('SEMS_LOGIN_REGION', 'us')
    if not account or not password:
        return jsonify({'ok': False, 'msg': 'Informe account e password (ou preencha no .env)'}), 400
    try:
        url = f"{BASE_SEMS[region]}/api/v2/common/crosslogin"
        headers = {"Token": _initial_token_prof(), "Content-Type": "application/json", "Accept": "*/*"}
        payload = {
            "account": account,
            "pwd": password,
            "agreement_agreement": 0,
            "is_local": False
        }
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        r.raise_for_status()
        js = r.json()
        if "data" not in js or js.get("code") not in (0, 1, 200):
            return jsonify({'ok': False, 'msg': f'Login falhou: {js}'}), 401
        data_to_string = json.dumps(js["data"])
        token = base64.b64encode(data_to_string.encode("utf-8")).decode("utf-8")
        return jsonify({'ok': True, 'token': token, 'raw': js["data"]})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500

@api_bp.route('/api/sems/inverter_data', methods=['POST'])
def sems_inverter_data():
    """
    Busca dados do inversor via SEMS (exemplo do professor).
    Espera JSON: {"token": ..., "inv_id": ..., "column": ..., "date": ..., "region": ...}
    Se não enviar, usa variáveis do .env e data atual.
    """
    data = request.get_json(silent=True) or {}
    token = data.get('token')
    inv_id = data.get('inv_id') or os.environ.get('SEMS_INV_ID')
    column = data.get('column', 'Pac')
    date = data.get('date', datetime.now().strftime('%Y-%m-%d 00:00:00'))
    region = data.get('region') or os.environ.get('SEMS_DATA_REGION', 'eu')
    if not token:
        # tenta login automático
        account = os.environ.get('SEMS_ACCOUNT')
        password = os.environ.get('SEMS_PASSWORD')
        login_region = os.environ.get('SEMS_LOGIN_REGION', 'us')
        if not account or not password:
            return jsonify({'ok': False, 'msg': 'Informe token ou preencha SEMS_ACCOUNT/SEMS_PASSWORD no .env'}), 400
        try:
            url_login = f"{BASE_SEMS[login_region]}/api/v2/common/crosslogin"
            headers_login = {"Token": _initial_token_prof(), "Content-Type": "application/json", "Accept": "*/*"}
            payload_login = {"account": account, "pwd": password, "agreement_agreement": 0, "is_local": False}
            r_login = requests.post(url_login, json=payload_login, headers=headers_login, timeout=20)
            r_login.raise_for_status()
            js_login = r_login.json()
            if "data" not in js_login or js_login.get("code") not in (0, 1, 200):
                return jsonify({'ok': False, 'msg': f'Login falhou: {js_login}'}), 401
            data_to_string = json.dumps(js_login["data"])
            token = base64.b64encode(data_to_string.encode("utf-8")).decode("utf-8")
        except Exception as e:
            return jsonify({'ok': False, 'msg': f'Login automático falhou: {e}'}), 500
    if not inv_id:
        return jsonify({'ok': False, 'msg': 'Informe inv_id (serial do inversor) ou preencha SEMS_INV_ID no .env'}), 400
    try:
        url = f"{BASE_SEMS[region]}/api/PowerStationMonitor/GetInverterDataByColumn"
        headers = {"Token": token, "Content-Type": "application/json", "Accept": "*/*"}
        payload = {"date": date, "column": column, "id": inv_id}
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        r.raise_for_status()
        return jsonify({'ok': True, 'data': r.json()})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)}), 500