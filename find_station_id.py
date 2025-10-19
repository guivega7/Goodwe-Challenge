"""
Script para descobrir o SEMS_STATION_ID correto.

O Station ID é diferente do Inverter ID (Serial Number).
Ele geralmente é um UUID encontrado:
1. Na URL do portal SEMS quando você navega para sua estação
2. Ou pode ser obtido listando as estações da sua conta
"""

from services.goodwe_client import GoodWeClient
import json

def find_station_id():
    print("=" * 60)
    print("BUSCANDO SEMS_STATION_ID")
    print("=" * 60)
    
    gc = GoodWeClient()
    
    # Fazer login
    print("\n[1] Fazendo login na GoodWe API...")
    token = gc._get_token()
    if not token:
        print("❌ Falha ao fazer login. Verifique suas credenciais no .env")
        return
    print(f"✅ Login OK - Token: {token[:30]}...")
    
    # Tentar listar estações
    print("\n[2] Tentando listar Power Stations da sua conta...")
    base = gc._get_base_url()
    
    # Endpoint para listar estações
    url = f"{base}v2/PowerStation/GetPowerStationListByUserId"
    headers = {"Token": token, "Content-Type": "application/json"}
    
    try:
        response = gc.session.post(url, json={}, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            print(f"Body: {response.text[:500]}")
            return
        
        data = response.json()
        print("\n✅ Resposta recebida:")
        print(json.dumps(data, indent=2))
        
        # Tentar extrair station IDs
        if isinstance(data, dict) and data.get('code') == 0:
            stations = data.get('data', {}).get('list', []) or data.get('data', [])
            
            if stations:
                print("\n" + "=" * 60)
                print("🎯 POWER STATIONS ENCONTRADAS:")
                print("=" * 60)
                
                for idx, station in enumerate(stations, 1):
                    station_id = station.get('powerStationId') or station.get('id') or station.get('station_id')
                    station_name = station.get('powerStationName') or station.get('name') or 'N/A'
                    
                    print(f"\n[{idx}] Nome: {station_name}")
                    print(f"    Station ID: {station_id}")
                    print(f"    Dados completos: {station}")
                
                print("\n" + "=" * 60)
                print("📝 PRÓXIMO PASSO:")
                print("=" * 60)
                print("Copie o 'Station ID' acima e cole no arquivo .env:")
                print("SEMS_STATION_ID=<cole_aqui>")
                print("=" * 60)
            else:
                print("\n⚠️ Nenhuma estação encontrada na resposta")
                print("Verifique se sua conta tem acesso a alguma Power Station no portal SEMS")
        else:
            print(f"\n⚠️ Code: {data.get('code')} - {data.get('msg')}")
            
    except Exception as e:
        print(f"\n❌ Erro ao buscar estações: {e}")
        print("\nTENTATIVA ALTERNATIVA:")
        print("Acesse o portal SEMS: https://www.semsportal.com")
        print("Navegue até sua Power Station")
        print("Copie o UUID da URL (algo como: abc12345-6789-...")


if __name__ == "__main__":
    find_station_id()
