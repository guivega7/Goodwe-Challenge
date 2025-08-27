import requests
import base64
import json
import time
from datetime import datetime


class GoodWeClient:
    """Cliente para comunicação com a API do GoodWe SEMS Portal"""
    
    BASE = {
        "us": "https://us.semsportal.com/api/",
        "eu": "https://eu.semsportal.com/api/",
    }

    def __init__(self):
        self.session = requests.Session()
        # Manter verificação SSL ativa por segurança
        self.session.verify = True

    def _get_initial_token(self):
        """Gera token inicial para primeira requisição"""
        timestamp = str(int(time.time() * 1000))

        token_data = {
            "version": "v2.0.4",
            "client": "web",
            "language": "en",
            "timestamp": timestamp,
            "uid": "",
            "token": "",
        }
        return base64.b64encode(json.dumps(token_data).encode()).decode()

    def crosslogin(self, account, pwd, region="us"):
        """Faz login na API e retorna token (token pós-login é base64(data))"""
        url = f"{self.BASE.get(region, self.BASE['us'])}v2/Common/CrossLogin"

        timestamp = str(int(time.time() * 1000))

        headers = {
            "Token": self._get_initial_token(),
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": f"https://{region}.semsportal.com",
            "Referer": f"https://{region}.semsportal.com/",
        }

        payload = {
            "account": account,
            "pwd": pwd,
            "validCode": "",
            "is_local": True,
            "timestamp": timestamp,
            "agreement_agreement": True,
        }

        try:
            print("\n=== Requisição de Login ===")
            print(f"URL: {url}")
            print(f"Headers: {json.dumps(headers, indent=2)}")
            print(f"Payload: {json.dumps(payload, indent=2)}")

            response = self.session.post(url, json=payload, headers=headers, timeout=30)
            print("\n=== Resposta ===")
            print(f"Status: {response.status_code}")
            print(f"Body: {response.text}")

            if response.status_code == 200:
                data = response.json()
                # Se a resposta contém 'data', codifica como Base64 e define como Token
                if data.get("data"):
                    try:
                        token_post = base64.b64encode(json.dumps(data.get("data")).encode()).decode()
                        self.session.headers.update({"Token": token_post})
                        print("\n✅ Login bem-sucedido (token_post definido).")
                        return token_post
                    except Exception as e:
                        print("Não foi possível codificar token pós-login:", str(e))
                        return None

                # fallback: estrutura antiga com data.token
                if data.get("code") == 10000 and isinstance(data.get("data"), dict):
                    token_data = data.get("data", {})
                    if token_data.get("token"):
                        token_fallback = token_data.get("token")
                        self.session.headers.update({"Token": token_fallback})
                        print("\n✅ Login bem-sucedido (token fallback).")
                        return token_fallback

                print(f"\n❌ Login falhou ou formato inesperado: {data.get('msg')} (Código: {data.get('code')})")
            return None

        except Exception as e:
            print(f"\n❌ Erro: {str(e)}")
            return None

    def get_inverter_data_by_column(self, token, inv_id, column, date, region="eu"):
        """Busca dados do inversor para uma coluna específica"""
        base = self.BASE.get(region, self.BASE["eu"])
        url = f"{base}PowerStationMonitor/GetInverterDataByColumn"

        headers = {
            "Token": token,
            "Content-Type": "application/json",
        }

        payload = {"id": inv_id, "date": date, "column": column}

        try:
            response = self.session.post(url, json=payload, headers=headers, timeout=30)
            print(f"POST {url} payload={payload} status={response.status_code}")
            text = response.text
            if len(text) > 2000:
                print(text[:2000] + "...")
            else:
                print(text)
            if response.status_code == 200:
                try:
                    return response.json()
                except Exception:
                    return response.text
            return None
        except Exception as e:
            print(f"❌ Erro nos dados: {str(e)}")
            return None

    def _parse_series_from_column_response(self, resp):
        """Extrai uma lista de pares (datetime, valor) das respostas comuns do SEMS."""
        if not resp:
            return None

        data = resp if not isinstance(resp, dict) else (resp.get("data") or resp)

        candidate_list = None
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, list):
                    candidate_list = v
                    break
        elif isinstance(data, list):
            candidate_list = data

        if not candidate_list:
            return None

        series = []
        for item in candidate_list:
            if not isinstance(item, dict):
                continue

            # find time
            t = None
            for tk in ("date", "time", "collectTime", "timestamp"):
                if tk in item:
                    t = item.get(tk)
                    break
            if t is None:
                for k in item.keys():
                    if "time" in k.lower() or "date" in k.lower():
                        t = item.get(k)
                        break

            # find value
            v = None
            for vk in ("column", "value", "val", "v"):
                if vk in item:
                    v = item.get(vk)
                    break
            if v is None:
                for k, val in item.items():
                    if k in ("date", "time", "collectTime", "timestamp"):
                        continue
                    if isinstance(val, (int, float)):
                        v = val
                        break

            # parse time
            dt = None
            if isinstance(t, (int, float)):
                try:
                    dt = datetime.fromtimestamp(float(t))
                except Exception:
                    dt = None
            elif isinstance(t, str):
                for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
                    try:
                        dt = datetime.strptime(t, fmt)
                        break
                    except Exception:
                        continue

            series.append((dt, v))

        return series

    def get_columns_series(self, token, inv_id, columns, date, region="eu", allow_mock=True):
        """Busca múltiplas colunas e retorna um dict coluna->series(datetime,valor)"""
        out = {}
        has_real_data = False
        error_details = {}
        
        for col in columns:
            resp = self.get_inverter_data_by_column(token, inv_id, col, date, region=region)
            ser = self._parse_series_from_column_response(resp)
            
            # Verifica que tipo de erro obtivemos
            if isinstance(resp, dict) and resp.get('msg'):
                error_details[col] = resp.get('msg', 'Erro desconhecido')
            
            # Verifica se obtivemos dados reais
            if ser and not (isinstance(resp, dict) and resp.get('hasError')):
                has_real_data = True
                out[col] = ser
            else:
                # Se allow_mock é False, não gera dados fictícios
                if not allow_mock:
                    print(f"❌ Nenhum dado real encontrado para {col} no inversor {inv_id}")
                    if isinstance(resp, dict) and resp.get('msg'):
                        print(f"   Erro: {resp.get('msg')}")
                    out[col] = []
                else:
                    print(f"⚠️  Chamada SEMS real falhou para {col}, gerando dados fictícios para desenvolvimento...")
                    ser = self._generate_mock_series(col, date)
                    out[col] = ser
        
        # Armazena detalhes do erro na saída para melhor tratamento
        if error_details and not allow_mock:
            out['_error_details'] = error_details
            
        # Se nenhum dado real foi encontrado e não permitimos fictícios, retorna dict vazio
        if not has_real_data and not allow_mock:
            print(f"❌ Nenhum dado válido encontrado para o inversor {inv_id}")
            return out  # Retorna com detalhes do erro
            
        return out
    
    def _generate_mock_series(self, column, date_str):
        """Gera séries temporais fictícias realistas para desenvolvimento/teste"""
        from datetime import datetime, timedelta
        import random
        
        try:
            base_date = datetime.strptime(date_str, '%Y-%m-%d')
        except:
            base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        series = []
        
        if column == 'Pac':  # Potência (kW) - padrão de geração solar
            for hour in range(24):
                dt = base_date + timedelta(hours=hour)
                if 6 <= hour <= 18:  # Horas de luz do dia
                    # Simula curva solar: baixa no nascer/pôr do sol, pico ao meio-dia
                    solar_factor = abs(12 - hour) / 6.0  # 0 ao meio-dia, 1 às 6h/18h
                    power = round(max(0, 5.5 - (solar_factor * 4.5) + random.uniform(-0.5, 0.5)), 2)
                else:
                    power = 0.0
                series.append((dt, power))
                
        elif column == 'Eday':  # Energia hoje (kWh) - cumulativo
            energy = 0.0
            for hour in range(24):
                dt = base_date + timedelta(hours=hour)
                if 6 <= hour <= 18:
                    energy += random.uniform(0.3, 1.2)  # Adiciona energia durante o dia
                series.append((dt, round(energy, 2)))
                
        elif column == 'Cbattery1':  # SOC da bateria (%) - padrão de carga/descarga
            soc = 80.0  # Inicia em 80%
            for hour in range(24):
                dt = base_date + timedelta(hours=hour)
                if 8 <= hour <= 16:  # Carregamento durante horas solares
                    soc = min(100.0, soc + random.uniform(0.5, 2.0))
                elif 18 <= hour <= 23:  # Descarregamento à noite
                    soc = max(20.0, soc - random.uniform(1.0, 3.0))
                series.append((dt, round(soc, 1)))
                
        else:  # Coluna genérica - valores aleatórios pequenos
            for hour in range(24):
                dt = base_date + timedelta(hours=hour)
                value = round(random.uniform(10, 50), 2)
                series.append((dt, value))
        
        return series