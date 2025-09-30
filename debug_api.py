from app import create_app
import json

# Criar a aplicação
app = create_app()

# Testar o endpoint internamente
with app.test_client() as client:
    response = client.get('/api/solar/status')
    data = response.get_json()

    print(f"Status Code: {response.status_code}")
    print("Dados retornados:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # Vamos também testar uma chamada direta para ver os dados brutos
    from services.goodwe_client import GoodWeClient
    import os
    from dotenv import load_dotenv

    load_dotenv()
    client = GoodWeClient()
    token = client.crosslogin(os.getenv('SEMS_ACCOUNT'), os.getenv('SEMS_PASSWORD'))

    if token:
        print("\nDados brutos da API GoodWe:")
        raw_data = client.get_inverter_data_by_column(token, os.getenv('SEMS_INV_ID'), 'Cbattery1', '2025-09-28 00:00:00')
        print(json.dumps(raw_data, indent=2, ensure_ascii=False))