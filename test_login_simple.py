import os
import base64
import json
import requests
from dotenv import load_dotenv

# Carregar .env
load_dotenv()

def test_login():
    account = os.getenv('SEMS_ACCOUNT')
    password = os.getenv('SEMS_PASSWORD')

    if not account or not password:
        print("Credenciais não encontradas no .env")
        return

    print(f"Tentando login com {account}")

    # Token inicial simples
    token_data = {
        "version": "v2.0.4",
        "client": "web",
        "language": "en",
        "uid": "",
        "token": "",
    }
    initial_token = base64.b64encode(json.dumps(token_data).encode()).decode()

    url = "https://us.semsportal.com/api/v2/Common/CrossLogin"

    headers = {
        "Token": initial_token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    payload = {
        "account": account,
        "pwd": password,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Resposta: {data}")

            if data.get("data"):
                token = base64.b64encode(json.dumps(data["data"]).encode()).decode()
                print("✅ Login bem-sucedido!")
                print(f"Token: {token[:20]}...")
            else:
                print("❌ Resposta sem campo 'data'")
        else:
            print(f"❌ Erro HTTP: {response.text}")

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    test_login()