# 🚨 PROBLEMA COM LOGIN API GOODWE SEMS - RELATÓRIO PARA O PROFESSOR

## 📋 RESUMO DO PROBLEMA

Estamos implementando a integração com GoodWe SEMS Portal conforme sua documentação, mas o login está falhando com erro **"system error (Code: 100000)"**.

## 🔧 CONFIGURAÇÃO ATUAL (CONFORME SUA DOC)

### Credenciais Demo:
```
SEMS_ACCOUNT=demo@goodwe.com
SEMS_PASSWORD=GoodweSems123!@#
SEMS_INV_ID=5010KETU229W6177
SEMS_LOGIN_REGION=us
SEMS_DATA_REGION=eu
```

### Implementação do crosslogin:
```python
# Endpoint: https://us.semsportal.com/api/v2/Common/CrossLogin
# Método: POST

# Token inicial (Base64):
{
  "version": "v2.0.4",
  "client": "web", 
  "language": "en",
  "timestamp": "timestamp_atual",
  "uid": "",
  "token": ""
}

# Payload do login:
{
  "account": "demo@goodwe.com",
  "pwd": "GoodweSems123!@#",
  "validCode": "",
  "is_local": true,
  "timestamp": "timestamp_atual",
  "agreement_agreement": true
}

# Headers:
{
  "Token": "token_inicial_base64",
  "Content-Type": "application/json",
  "Origin": "https://us.semsportal.com",
  "Referer": "https://us.semsportal.com/"
}
```

## ❌ RESPOSTA DE ERRO

**Status Code:** 200  
**Response Body:**
```json
{
  "language": "en",
  "function": null,
  "hasError": true,
  "msg": "system error",
  "code": "100000",
  "data": "",
  "components": {
    "para": "{\"data\":null}",
    "langVer": 286,
    "timeSpan": 0,
    "api": "http://us.semsportal.com:82/api/v2/Common/CrossLogin",
    "msgSocketAdr": null
  }
}
```

## 🔍 ANÁLISE TÉCNICA

1. **Request está sendo enviado corretamente** - Status 200
2. **Endpoint está correto** - `/api/v2/Common/CrossLogin`
3. **Formato do payload está correto** - Conforme sua documentação
4. **Token inicial sendo gerado corretamente** - Base64 do JSON
5. **Headers corretos** - Origin, Referer, Content-Type

## 🤔 POSSÍVEIS CAUSAS

1. **Credenciais demo expiraram?** - As credenciais `demo@goodwe.com / GoodweSems123!@#` ainda são válidas?

2. **Mudança na API?** - Houve alguma mudança no endpoint ou formato desde sua documentação?

3. **Rate limiting?** - Existe limite de tentativas de login?

4. **Configuração específica?** - Falta algum parâmetro no payload ou header?

## 📝 PERGUNTAS ESPECÍFICAS

1. **As credenciais demo ainda funcionam?**
2. **O endpoint `/api/v2/Common/CrossLogin` é o correto?**
3. **Há alguma configuração específica que estamos perdendo?**
4. **O formato do token inicial está correto?**
5. **Existe algum pré-requisito para usar a conta demo?**

## 🧪 TESTES REALIZADOS

✅ Testamos com todas as combinações de região (US/EU)  
✅ Verificamos formato do token inicial  
✅ Confirmamos payload e headers  
✅ Testamos em horários diferentes  
❌ Sempre retorna erro "100000"

## 💻 CÓDIGO DE TESTE

O erro pode ser reproduzido executando:
```bash
cd "projeto"
python debug_goodwe.py
```

Isso mostra exatamente o request/response sendo enviado.

---

**IMPLEMENTAÇÃO ESTÁ 100% CONFORME SUA DOCUMENTAÇÃO**  
**Problema parece ser com as credenciais demo ou mudança na API**

Professor, poderia nos ajudar a identificar o que pode estar causando este erro?