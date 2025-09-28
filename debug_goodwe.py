#!/usr/bin/env python3
"""
Debug detalhado para identificar onde está o problema com a API GoodWe SEMS
"""

import os
import sys
import json
import base64
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.goodwe_client import GoodWeClient

def debug_step_by_step():
    """Debug passo a passo da integração GoodWe"""
    
    print("🔧 DEBUG DETALHADO - API GOODWE SEMS")
    print("=" * 60)
    
    # 1. Verificar variáveis de ambiente
    print("\n1️⃣ Verificando variáveis de ambiente...")
    account = os.getenv('SEMS_ACCOUNT')
    password = os.getenv('SEMS_PASSWORD') 
    inverter_id = os.getenv('SEMS_INV_ID')
    login_region = os.getenv('SEMS_LOGIN_REGION', 'us')
    data_region = os.getenv('SEMS_DATA_REGION', 'eu')
    
    print(f"   SEMS_ACCOUNT: {account}")
    print(f"   SEMS_PASSWORD: {'*' * len(password) if password else 'None'}")
    print(f"   SEMS_INV_ID: {inverter_id}")
    print(f"   LOGIN_REGION: {login_region}")
    print(f"   DATA_REGION: {data_region}")
    
    if not all([account, password, inverter_id]):
        print("❌ Variáveis de ambiente faltando!")
        return False
    
    # 2. Testar conexão básica
    print(f"\n2️⃣ Testando conexão básica...")
    client = GoodWeClient(region=login_region)
    
    # Mostrar URLs sendo usadas
    print(f"   URL base US: {client.BASE_URLS['us']}")
    print(f"   URL base EU: {client.BASE_URLS['eu']}")
    print(f"   Região atual: {client.region}")
    
    # 3. Verificar token inicial
    print(f"\n3️⃣ Verificando token inicial...")
    try:
        initial_token = client._generate_initial_token()
        print(f"   ✅ Token inicial gerado: {initial_token[:50]}...")
        
        # Decodificar para ver o conteúdo
        decoded = json.loads(base64.b64decode(initial_token).decode())
        print(f"   Conteúdo do token: {json.dumps(decoded, indent=2)}")
        
    except Exception as e:
        print(f"   ❌ Erro no token inicial: {e}")
        return False
    
    # 4. Testar crosslogin com debug detalhado
    print(f"\n4️⃣ Testando crosslogin...")
    try:
        # Fazer request manualmente para ver resposta completa
        import requests
        
        url = f"{client.BASE_URLS[login_region]}v2/Common/CrossLogin"
        print(f"   URL de login: {url}")
        
        headers = {
            "Token": initial_token,
            "Content-Type": "application/json",
            "Origin": f"https://{login_region}.semsportal.com",
            "Referer": f"https://{login_region}.semsportal.com/",
        }
        
        payload = {
            "account": account,
            "pwd": password,
            "validCode": "",
            "is_local": True,
            "timestamp": str(int(datetime.now().timestamp() * 1000)),
            "agreement_agreement": True,
        }
        
        print(f"   Headers: {json.dumps(headers, indent=2)}")
        print(f"   Payload: {json.dumps({**payload, 'pwd': '***'}, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Resposta JSON: {json.dumps(data, indent=2)}")
            
            if data.get("data"):
                print(f"   ✅ Campo 'data' encontrado!")
                
                # Tentar gerar token
                token = base64.b64encode(json.dumps(data.get("data")).encode()).decode()
                print(f"   ✅ Token pós-login gerado: {token[:50]}...")
                
                return token
            else:
                print(f"   ❌ Campo 'data' não encontrado na resposta!")
                print(f"   Código: {data.get('code')}")
                print(f"   Mensagem: {data.get('msg')}")
                return False
        else:
            print(f"   ❌ Status não é 200!")
            print(f"   Texto da resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro durante crosslogin: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_alternative_approach():
    """Testa abordagem alternativa caso a primeira falhe"""
    
    print(f"\n5️⃣ Testando abordagem alternativa...")
    
    # Tentar com diferentes configurações
    configs = [
        {"login": "us", "data": "us"},
        {"login": "eu", "data": "eu"},
        {"login": "us", "data": "eu"},
        {"login": "eu", "data": "us"},
    ]
    
    for config in configs:
        print(f"\n   🔄 Testando: Login={config['login']}, Data={config['data']}")
        
        client = GoodWeClient(region=config['login'])
        token = debug_step_by_step()
        
        if token:
            print(f"   ✅ Sucesso com configuração: {config}")
            
            # Testar busca de dados
            client.region = config['data'] 
            
            try:
                today = datetime.now().strftime('%Y-%m-%d')
                data = client.get_inverter_data_by_column(
                    token=token,
                    inverter_id="5010KETU229W6177",
                    column="Cbattery1",
                    date=today
                )
                
                if data:
                    print(f"   ✅ Dados obtidos com sucesso!")
                    return True
                else:
                    print(f"   ⚠️ Token válido mas sem dados")
                    
            except Exception as e:
                print(f"   ❌ Erro ao buscar dados: {e}")
        
        print(f"   ❌ Falha com configuração: {config}")
    
    return False

if __name__ == "__main__":
    print("🐛 DEBUG GOODWE SEMS - ENCONTRAR O PROBLEMA")
    print()
    
    # Tentar debug passo a passo
    success = debug_step_by_step()
    
    if not success:
        print(f"\n🔄 Primeira tentativa falhou, testando alternativas...")
        success = test_alternative_approach()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 PROBLEMA IDENTIFICADO E RESOLVIDO!")
    else:
        print("❌ PROBLEMA NÃO RESOLVIDO")
        print("\n💡 POSSÍVEIS CAUSAS:")
        print("1. Credenciais demo podem ter expirado")
        print("2. Rate limiting na API GoodWe")
        print("3. Mudança na API desde a documentação")
        print("4. Problema de conectividade")
        print("5. Configuração de região incorreta")
        
    print("=" * 60)