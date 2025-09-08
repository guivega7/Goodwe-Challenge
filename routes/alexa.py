from flask import Blueprint, request, jsonify
from extensions import db
from models.aparelho import Aparelho
from datetime import datetime

alexa_bp = Blueprint('alexa', __name__)


@alexa_bp.route('/alexa', methods=['POST'])
def alexa_webhook():
    """
    Webhook para Skills Personalizadas (Custom Skill) da Alexa.
    Converte o intent DesligarDispositivoIntent em ação no backend.
    Responde no formato esperado pela Alexa (response.outputSpeech).
    """
    body = request.get_json(silent=True) or {}
    print('[Alexa] Payload recebido:', body)

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
            # Normalmente você armazena o grant code e grantee token. Para teste, apenas responda sucesso.
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
                print('[Alexa][Discovery] Erro ao buscar dispositivos:', e)
                dispositivos = []

            for ap in dispositivos:
                friendly = ap.nome
                endpoint_obj = {
                    'endpointId': ap.nome,
                    'manufacturerName': 'SolarMind',
                    'friendlyName': friendly,
                    'description': f'Dispositivo {friendly} controlado pelo SolarMind',
                    'displayCategories': ['SWITCH'],
                    'cookie': {},
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
            ap = Aparelho.query.filter_by(nome=endpoint_id, usuario_id=usuario_id).first()
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

            ap = Aparelho.query.filter_by(nome=dispositivo, usuario_id=usuario_id).first()
            if not ap:
                msg = f"Não encontrei um dispositivo chamado {dispositivo}."
                print('[Alexa] ', msg)
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
