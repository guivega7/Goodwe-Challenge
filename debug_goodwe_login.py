"""Debug aprofundado do fluxo de login GoodWe SEMS.

Executa passos:
1. Carrega .env
2. Mostra credenciais (apenas email / regiões)
3. Gera token inicial (pré-login)
4. Tenta login na(s) região(ões) configurada(s)
5. Exibe região de dados detectada
6. Opcional: testa uma coluna (Pac) do dia

Uso:
    python debug_goodwe_login.py [--col Pac] [--date 2025-09-28] [--no-column]
"""
from __future__ import annotations
import os
import base64
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
from services.goodwe_client import GoodWeClient
from utils.logger import get_logger

logger = get_logger(__name__)

def build_initial_token() -> str:
    payload = {
        "version": "v2.0.4",
        "client": "web",
        "language": "en",
        "uid": "",
        "token": "",
    }
    return base64.b64encode(json.dumps(payload).encode()).decode()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--col', default='Pac', help='Coluna para teste de dados (Pac, Eday, Cbattery1)')
    parser.add_argument('--date', default=datetime.now().strftime('%Y-%m-%d 00:00:00'), help='Data (YYYY-MM-DD 00:00:00)')
    parser.add_argument('--no-column', action='store_true', help='Não testar endpoint de coluna, apenas login')
    args = parser.parse_args()

    load_dotenv()
    account = os.getenv('SEMS_ACCOUNT')
    password = os.getenv('SEMS_PASSWORD')
    login_region = os.getenv('SEMS_LOGIN_REGION', 'us')
    data_region = os.getenv('SEMS_DATA_REGION', 'eu')
    inv_id = os.getenv('SEMS_INV_ID', '')

    print('\n=== GOODWE SEMS DEBUG LOGIN ===')
    print(f"Account: {account}")
    print(f"Login region (env): {login_region}")
    print(f"Data region (env):  {data_region}")
    print(f"Inverter SN: {inv_id}")
    if not account or not password:
        print('ERRO: SEMS_ACCOUNT/SEMS_PASSWORD ausentes no ambiente/.env')
        return

    init_token = build_initial_token()
    print(f"Token inicial (prefix): {init_token[:25]}...")

    client = GoodWeClient(region=login_region)
    token = client.crosslogin(account, password)

    if not token:
        print('❌ Login falhou em todas as tentativas.')
        return

    print(f"✅ Token pós-login (prefix): {token[:25]}...")
    print(f"Região de dados detectada pelo cliente: {client.data_region}")

    if args.no_column:
        return

    if not inv_id:
        print('⚠️ SEMS_INV_ID não definido; pulando teste de coluna.')
        return

    print('\nTestando coluna...')
    # Tentar usar a data em formato aceito (caso usuario tenha passado só YYYY-MM-DD normalizar)
    date_arg = args.date
    if len(date_arg) == 10:
        date_arg = date_arg + ' 00:00:00'

    resp = client.get_inverter_data_by_column(token, inv_id, args.col, date_arg)
    if resp:
        # Mostrar chaves principais / tamanho
        keys = list(resp.keys())
        print(f"Chaves nível 1: {keys}")
        data_part = resp.get('data') or {}
        if isinstance(data_part, dict):
            for k, v in data_part.items():
                if isinstance(v, list):
                    print(f" - data.{k}: lista com {len(v)} pontos")
                    if v:
                        first = v[0]
                        print(f"   Primeiro ponto: {first}")
                        if len(v) > 1:
                            print(f"   Último ponto: {v[-1]}")
                    break
        else:
            print('Formato inesperado em data')
    else:
        print('❌ Falha ao obter dados da coluna.')

if __name__ == '__main__':
    main()
