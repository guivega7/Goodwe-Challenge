from flask import Blueprint, request, jsonify
from extensions import db
from models.aparelho import Aparelho
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


def _slug(text: str) -> str:
    if not text:
        return ''
    t = text.lower().strip()
    t = re.sub(r'[^a-z0-9]+', '-', t)
    t = re.sub(r'-+', '-', t).strip('-')
    return t or text.lower()

alexa_bp = Blueprint('alexa', __name__)


@alexa_bp.route('/alexa/ping', methods=['GET'])
def alexa_ping():
    """Healthcheck simples para Lambda ou monitoramentos."""
    return jsonify({
        'status': 'ok',
        'ts': datetime.utcnow().isoformat() + 'Z'
    })


@alexa_bp.route('/alexa/reportstate', methods=['POST'])
def alexa_report_state():
    """Stub de ReportState futuro (pode ser chamado manualmente ou por scheduler).

    Alexa Smart Home normalmente exige eventos proativos (ChangeReport) apenas
    se proactivelyReported=True. Como definimos False no Discovery, isto é opcional.
    """
    body = request.get_json(silent=True) or {}
    logger.info('[Alexa][ReportState] payload=%s', body)
    # Retornar formato neutro por enquanto
    return jsonify({'ok': True, 'note': 'ReportState stub - não configurado para proativo'})


@alexa_bp.route('/alexa', methods=['POST'])
def alexa_webhook():
    """
    Webhook para Skills Personalizadas (Custom Skill) da Alexa.
    Converte o intent DesligarDispositivoIntent em ação no backend.
    Responde no formato esperado pela Alexa (response.outputSpeech).
    """
    body = request.get_json(silent=True) or {}
    logger.info('[Alexa] Payload recebido=%s', str(body)[:800])

    # 1) Suporte a Smart Home (payload raiz "directive")
    if 'directive' in body:
        d = body.get('directive', {})
        header = d.get('header', {})
        namespace = header.get('namespace')
        name = header.get('name')
        endpoint = d.get('endpoint', {})
        endpoint_id = endpoint.get('endpointId')

        # Authorization - AcceptGrant (requerido por Smart Home com Account Linking)
        if namespace == 'Alexa.Authorization' and name == 'AcceptGrant':
            # Para implementação futura: armazenar grantCode / grantee.token em tabela.
            return jsonify({
                'event': {
                    'header': {
                        'namespace': 'Alexa.Authorization',
                        'name': 'AcceptGrant.Response',
                        'messageId': header.get('messageId', 'msg-1'),
                        'payloadVersion': '3'
                    },
                    'payload': {}
                }
            })

        # Discovery - retorna a lista de dispositivos do usuário
        if namespace == 'Alexa.Discovery' and name == 'Discover':
            usuario_id = 1
            endpoints = []
            try:
                dispositivos = Aparelho.query.filter_by(usuario_id=usuario_id).all()
            except Exception as e:
                logger.exception('[Alexa][Discovery] Erro ao buscar dispositivos: %s', e)
                dispositivos = []

            for ap in dispositivos:
                friendly = ap.nome
                endpoint_id = _slug(friendly)
                endpoint_obj = {
                    'endpointId': endpoint_id,
                    'manufacturerName': 'SolarMind',
                    'friendlyName': friendly,
                    'description': f'Dispositivo {friendly} controlado pelo SolarMind',
                    'displayCategories': ['SWITCH'],
                    'cookie': {'originalName': friendly},
                    'capabilities': [
                        {
                            'type': 'AlexaInterface',
                            'interface': 'Alexa',
                            'version': '3'
                        },
                        {
                            'type': 'AlexaInterface',
                            'interface': 'Alexa.PowerController',
                            'version': '3',
                            'properties': {
                                'supported': [{'name': 'powerState'}],
                                'proactivelyReported': False,
                                'retrievable': True
                            }
                        }
                    ]
                }
                endpoints.append(endpoint_obj)

            return jsonify({
                'event': {
                    'header': {
                        'namespace': 'Alexa.Discovery',
                        'name': 'Discover.Response',
                        'messageId': header.get('messageId', 'msg-1'),
                        'payloadVersion': '3'
                    },
                    'payload': { 'endpoints': endpoints }
                }
            })

        # Apenas PowerController básico
        if namespace == 'Alexa.PowerController' and endpoint_id:
            usuario_id = 1
            normalized = endpoint_id.lower()
            ap = (Aparelho.query
                  .filter(Aparelho.usuario_id == usuario_id)
                  .filter((Aparelho.nome.ilike(normalized)) | (Aparelho.nome.ilike(endpoint_id)))
                  .first())
            if not ap:
                # Resposta de erro mínima
                return jsonify({
                    'event': {
                        'header': {
                            'namespace': 'Alexa',
                            'name': 'ErrorResponse',
                            'messageId': header.get('messageId', 'msg-1'),
                            'correlationToken': header.get('correlationToken'),
                            'payloadVersion': '3'
                        },
                        'endpoint': {'endpointId': endpoint_id},
                        'payload': {
                            'type': 'NO_SUCH_ENDPOINT',
                            'message': f"Dispositivo '{endpoint_id}' não encontrado."
                        }
                    }
                })

            # Aplica comando
            if name == 'TurnOff':
                ap.status = False
                state_val = 'OFF'
            elif name == 'TurnOn':
                ap.status = True
                state_val = 'ON'
            else:
                state_val = 'UNKNOWN'
            db.session.commit()

            logger.info('[Alexa][PowerController] endpoint=%s action=%s state=%s', endpoint_id, name, state_val)

            return jsonify({
                'context': {
                    'properties': [{
                        'namespace': 'Alexa.PowerController',
                        'name': 'powerState',
                        'value': state_val,
                        'timeOfSample': datetime.utcnow().isoformat() + 'Z',
                        'uncertaintyInMilliseconds': 50
                    }]
                },
                'event': {
                    'header': {
                        'namespace': 'Alexa',
                        'name': 'Response',
                        'messageId': header.get('messageId', 'msg-1') + '-r',
                        'correlationToken': header.get('correlationToken'),
                        'payloadVersion': '3'
                    },
                    'endpoint': {'endpointId': endpoint_id},
                    'payload': {}
                }
            })

        # Diretiva não suportada
        return jsonify({
            'event': {
                'header': {
                    'namespace': 'Alexa',
                    'name': 'ErrorResponse',
                    'messageId': header.get('messageId', 'msg-1'),
                    'payloadVersion': '3'
                },
                'payload': {'type': 'INVALID_DIRECTIVE', 'message': 'Diretiva não suportada.'}
            }
        })

    # 2) Estrutura padrão de Custom Skill
    req = body.get('request') or {}
    req_type = req.get('type')

    if req_type == 'LaunchRequest':
        return jsonify({
            'version': '1.0',
            'response': {
                'outputSpeech': {'type': 'PlainText', 'text': 'Bem-vindo. Diga, por exemplo: desligue o ventilador.'},
                'shouldEndSession': False
            }
        })

    if req_type == 'IntentRequest':
        intent = req.get('intent', {})
        intent_name = intent.get('name')

        # Captura slot "dispositivo" (pode vir nested conforme NLU)
        slots = intent.get('slots') or {}
        dispositivo = None
        if isinstance(slots, dict):
            slot_obj = slots.get('dispositivo') or {}
            dispositivo = slot_obj.get('value')

        if intent_name == 'DesligarDispositivoIntent' and dispositivo:
            # Simula usuário logado em desenvolvimento; ajuste para sua auth real
            usuario_id = 1
            device_slug = _slug(dispositivo)
            ap = (Aparelho.query
                  .filter(Aparelho.usuario_id == usuario_id)
                  .filter((Aparelho.nome.ilike(dispositivo)) | (Aparelho.nome.ilike(device_slug)))
                  .first())
            if not ap:
                msg = f"Não encontrei um dispositivo chamado {dispositivo}."
                logger.warning('[Alexa][Intent] dispositivo_nao_encontrado=%s', dispositivo)
                return jsonify({
                    'version': '1.0',
                    'response': {
                        'outputSpeech': {'type': 'PlainText', 'text': msg},
                        'shouldEndSession': True
                    }
                })

            if ap.status is False:
                msg = f"O {dispositivo} já está desligado."
            else:
                ap.status = False
                db.session.commit()
                msg = f"{dispositivo} desligado com sucesso."

            logger.info('[Alexa][Intent] intent=%s dispositivo=%s resultado=%s', intent_name, dispositivo, msg)

            return jsonify({
                'version': '1.0',
                'response': {
                    'outputSpeech': {'type': 'PlainText', 'text': msg},
                    'shouldEndSession': True
                }
            })

        # Intent desconhecida ou sem slot
        return jsonify({
            'version': '1.0',
            'response': {
                'outputSpeech': {'type': 'PlainText', 'text': 'Não entendi o pedido. Diga: desligue o nome do dispositivo.'},
                'shouldEndSession': False
            }
        })

    # Tipos não suportados
    return jsonify({
        'version': '1.0',
        'response': {
            'outputSpeech': {'type': 'PlainText', 'text': 'Requisição não suportada.'},
            'shouldEndSession': True
        }
    })
