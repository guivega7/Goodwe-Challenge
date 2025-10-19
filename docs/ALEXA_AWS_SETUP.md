# Guia de Migração: IFTTT -> Alexa + AWS (Lambda Proxy)

Este guia mostra como integrar sua Skill Alexa diretamente com sua aplicação Flask (`/alexa`) usando AWS Lambda como proxy, eliminando dependência do IFTTT.

## 🎯 Objetivo
Manter toda a lógica no backend atual (rota `/alexa`) e apenas criar uma ponte segura Alexa -> Lambda -> Flask.

## ✅ Cenários Suportados Pelo Seu Código Atual
| Tipo | Suporte | Observação |
|------|---------|------------|
| Custom Skill (conversa) | ✅ | Usa `request.type` = `LaunchRequest` / `IntentRequest` |
| Smart Home Skill (controle) | ✅ | Usa `directive.header.namespace` (Discovery, PowerController) |

## 🗺️ Arquiteturas Possíveis
| Modelo | Descrição | Prós | Contras |
|--------|-----------|------|--------|
| 1. Lambda Proxy (RECOMENDADO) | Lambda apenas repassa JSON para seu Flask público | Simples, reutiliza código | Requer URL pública estável |
| 2. Lógica dentro da Lambda | Move `alexa_webhook()` para o Lambda | Sem dependência externa | Duplica lógica / manutenção |
| 3. Alexa chama Flask direto (HTTPS) | Configura endpoint público com certificado | Zero AWS extra | Exige domínio + TLS + alta disponibilidade |

## 🛠️ Passo a Passo (Lambda Proxy)

### 1. Expor sua Aplicação Flask
Opção Dev rápida (ngrok):
```bash
ngrok http 5000
```
Pegue a URL HTTPS gerada (ex: `https://abcd-1234.ngrok.io`).

Opção Produção: Deploy em VPS / Render / Railway / ECS / Elastic Beanstalk.

### 2. Criar Função Lambda
1. AWS Console -> Lambda -> Create Function
2. Runtime: Python 3.11 (ou 3.10+)
3. Nome: `alexa_solarmind_proxy`
4. Create

### 3. Código da Função Lambda (Proxy)
Cole no editor da Lambda (arquivo `lambda_function.py`):
```python
import json, urllib.request, os

FLASK_APP_URL = os.getenv('FLASK_ALEXA_ENDPOINT', 'https://SUA_URL_PUBLICA/alexa')
TIMEOUT = int(os.getenv('ALEXA_PROXY_TIMEOUT', '6'))

def lambda_handler(event, context):
    print('[Lambda] Recebido da Alexa:', json.dumps(event)[:800])
    try:
        data_bytes = json.dumps(event).encode('utf-8')
        req = urllib.request.Request(
            FLASK_APP_URL,
            data=data_bytes,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode('utf-8')
            print('[Lambda] Resposta Flask:', body[:800])
            # Retorna exatamente o JSON que o Flask devolveu
            return json.loads(body)
    except Exception as e:
        print('[Lambda] Erro proxy:', e)
        # Fallback genérico para Custom Skill
        return {
            'version': '1.0',
            'response': {
                'outputSpeech': {'type': 'PlainText', 'text': 'Desculpe, não consegui falar com o servidor agora.'},
                'shouldEndSession': True
            }
        }
```
Variáveis de ambiente recomendadas na Lambda:
```
FLASK_ALEXA_ENDPOINT=https://sua-url/alexa
ALEXA_PROXY_TIMEOUT=6
```

### 4. Criar a Skill (Custom)
1. Alexa Developer Console -> Create Skill
2. Tipo: Custom
3. Modelo de linguagem: Português (Brasil) (ou outro)
4. Endpoint: escolha **AWS Lambda ARN** e cole o ARN da função criada
5. Interaction Model -> Intents:
   - Crie `DesligarDispositivoIntent`
   - Adicione slot `dispositivo` (tipo `AMAZON.SearchQuery` ou custom ex: `DISPOSITIVO_TYPE`)
   - Frases exemplo:
     - "desligue o ventilador"
     - "desligar a lâmpada do quarto"

### 5. Criar a Skill (Smart Home) (Opcional)
1. Nova Skill -> Smart Home
2. Endpoint -> Lambda ARN (a mesma pode servir)
3. Habilite Account Linking (OAuth 2.0) para múltiplos usuários (fase futura)
4. Teste Discovery: Alexa fará POST com `Alexa.Discovery -> Discover` e seu backend deve responder endpoints (já preparado no código).

### 6. Testar (Dev Console)
- Aba **Test** -> Ative a skill -> Digite: "Alexa, abra SolarMind" ou equivalente
- Envie JSON manual simulando diretiva (Smart Home):
```json
{
  "directive": {
    "header": {"namespace": "Alexa.Discovery", "name": "Discover", "messageId": "abc-123", "payloadVersion": "3"},
    "payload": {"scope": {"type": "BearerToken", "token": "dummy"}}
  }
}
```

### 7. Testes Locais (Script)
Crie `test_alexa_payloads.py`:
```python
import requests, json
BASE = 'http://localhost:5000/alexa'

def post(payload):
    r = requests.post(BASE, json=payload, timeout=5)
    print('Status', r.status_code)
    print(r.text[:500])

# LaunchRequest
post({"session": {}, "request": {"type": "LaunchRequest"}})

# IntentRequest
post({
  "request": {
    "type": "IntentRequest",
    "intent": {"name": "DesligarDispositivoIntent", "slots": {"dispositivo": {"value": "ventilador"}}}
  }
})

# Discovery
post({
  "directive": {
    "header": {"namespace": "Alexa.Discovery", "name": "Discover", "messageId": "m1", "payloadVersion": "3"},
    "payload": {"scope": {"type": "BearerToken", "token": "dummy"}}
  }
})
```

### 8. Checklist de Erros Comuns
| Sintoma | Causa | Correção |
|---------|-------|----------|
| Alexa responde "Endpoint unresponsive" | Timeout no Lambda proxy | Reduzir latência / aumentar TIMEOUT / checar URL |
| Discovery vazio | Sem dispositivos no banco | Popular tabela `aparelho` |
| Intent não reconhecida | Modelo não atualizado | Salvar + Build na Developer Console |
| Erro 500 no Flask | Exceção na rota | Ver logs do servidor / ativar DEBUG local |

### 9. Próximos Passos (Evolução)
- Implementar Account Linking (OAuth) para multiusuário
- Diferenciar usuários via token -> mapear `usuario_id` dinamicamente
- Adicionar suporte a `ReportState` para Smart Home
- Expandir capabilities: BrightnessController, ColorController (se tiver devices) 

---

## 🔍 Referências
- Alexa Skills Kit: https://developer.amazon.com/en-US/docs/alexa
- Smart Home API: https://developer.amazon.com/en-US/docs/alexa/device-apis/alexa-discovery.html
- AWS Lambda Python: https://docs.aws.amazon.com/lambda/latest/dg/python.html

Se quiser a versão migrando totalmente a lógica para Lambda em vez de proxy, posso gerar também.
