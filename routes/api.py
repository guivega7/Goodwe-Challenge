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
from datetime import datetime
from flask import Blueprint, jsonify, request

from extensions import db
from models.aparelho import Aparelho
from models.usuario import Usuario
from utils.energia import dispara_alerta, dispara_alerta_economia

api_bp = Blueprint('api', __name__)


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