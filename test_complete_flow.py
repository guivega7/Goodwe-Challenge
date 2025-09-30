import os
import base64
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def test_complete_flow():
    account = os.getenv('SEMS_ACCOUNT')
    password = os.getenv('SEMS_PASSWORD')
    inverter_id = os.getenv('SEMS_INV_ID')

    print(f"Testando fluxo completo com conta: {account}")
    print(f"Inversor ID: {inverter_id}")

    # Mesmo código que funciona no test_login_simple.py
    token_data = {
        "version": "v2.0.4",
        "client": "web",
        "language": "en",
        "uid": "",
        "token": "",
    }
    initial_token = base64.b64encode(json.dumps(token_data).encode()).decode()

    # Login - usar EU pois a resposta mostrou eu.semsportal.com
    url_login = "https://eu.semsportal.com/api/v2/Common/CrossLogin"
    headers_login = {
        "Token": initial_token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }
    payload_login = {
        "account": account,
        "pwd": password,
    }

    print("1. Fazendo login...")
    response_login = requests.post(url_login, json=payload_login, headers=headers_login, timeout=30)

    if response_login.status_code != 200:
        print(f"❌ Login falhou: HTTP {response_login.status_code}")
        return

    data_login = response_login.json()
    print(f"Resposta login: {data_login}")

    if not data_login.get("data"):
        print("❌ Login sem campo 'data'")
        return

    # Usar o campo 'data' codificado em Base64 conforme instruções do professor
    post_login_token = base64.b64encode(json.dumps(data_login["data"]).encode()).decode()
    print(f"Token pós-login codificado: {post_login_token[:30]}...")

    # Imediatamente tentar buscar dados
    print("2. Buscando dados do inversor...")
    # Imediatamente tentar buscar dados - voltar para HTTPS padrão
    url_data = "https://eu.semsportal.com/api/PowerStationMonitor/GetInverterDataByColumn"
    headers_data = {
        "Token": post_login_token,
        "Content-Type": "application/json",
    }
    payload_data = {
        "id": inverter_id,
        "date": "2025-09-28 00:00:00",
        "column": "Cbattery1",
    }

    response_data = requests.post(url_data, json=payload_data, headers=headers_data, timeout=30)
    print(f"Status da busca de dados: {response_data.status_code}")
    print(f"Resposta: {response_data.json()}")

if __name__ == "__main__":
    test_complete_flow()