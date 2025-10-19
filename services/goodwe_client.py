"""
GoodWe SEMS Portal API Client - Versão Funcional

Este módulo implementa o cliente para a API GoodWe SEMS,
testado e funcionando com a conta demo.
"""

import base64
import json
import os
from datetime import datetime, timedelta
import requests
from utils.logger import get_logger
from urllib.parse import urlparse

logger = get_logger(__name__)


class GoodWeClient:
    """
    Cliente para GoodWe SEMS Portal API.
    """

    BASE_URLS = {
        "us": "https://us.semsportal.com/api/",
        "eu": "https://eu.semsportal.com/api/",
    }

    def __init__(self, region: str = "us"):
        self.region = region
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        })
        # Cache simples de token (renova a cada 5 minutos)
        self._token_cache: dict | None = None
        # Credenciais carregadas opcionalmente do ambiente
        self.account: str | None = None
        self.password: str | None = None
        self.inverter_id: str | None = None
        self.login_region: str = region
        self.data_region: str = region
        # Base URL de dados retornada pelo login (pode incluir porta 82)
        self._data_base_url_override: str | None = None
        # Flags de depuração e restrição de endpoint
        self.debug: bool = os.getenv('GOODWE_DEBUG', 'false').lower() == 'true'
        self.strict_https: bool = os.getenv('GOODWE_STRICT_HTTPS', 'true').lower() == 'true'
        # Parâmetros configuráveis
        try:
            self.request_timeout: float = float(os.getenv('GOODWE_TIMEOUT', '30'))
        except Exception:
            self.request_timeout = 30.0
        try:
            self.max_token_cycles: int = int(os.getenv('GOODWE_MAX_TOKEN_CYCLES', '2'))
        except Exception:
            self.max_token_cycles = 2

    def _dbg(self, *args, **kwargs):
        """Imprime somente quando GOODWE_DEBUG=true."""
        if self.debug:
            try:
                print(*args, **kwargs)
            except Exception:
                pass

    def _get_base_url(self) -> str:
        return self.BASE_URLS.get(self.region, self.BASE_URLS["us"])

    def _generate_initial_token(self) -> str:
        """Gera token inicial no formato minimalista (compatível com exemplo professor)."""
        token_data = {
            "uid": "",
            "timestamp": 0,
            "token": "",
            "client": "web",
            "version": "",
            "language": "en",
        }
        return base64.b64encode(json.dumps(token_data).encode('utf-8')).decode('utf-8')

    def crosslogin(self, account: str, password: str) -> str | None:
        """
        Faz login na API GoodWe SEMS.

        Args:
            account: Email da conta
            password: Senha da conta

        Returns:
            Token pós-login ou None se falhar
        """
        # Persistir credenciais (necessário para retries automáticos depois)
        self.account = account
        self.password = password

        url = f"{self._get_base_url()}v2/common/crosslogin"

        headers = {
            "Token": self._generate_initial_token(),
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Origin": "https://semsportal.com",
            "Referer": "https://semsportal.com/",
        }

        payload = {
            "account": account,
            "pwd": password,
            "agreement_agreement": 0,
            "is_local": False,
        }

        tried_regions = []
        regions_to_try = [self.region]
        alt = 'eu' if self.region.lower() == 'us' else 'us'
        if alt not in regions_to_try:
            regions_to_try.append(alt)

        for attempt, region in enumerate(regions_to_try, start=1):
            self.region = region
            url = f"{self._get_base_url()}v2/common/crosslogin"
            tried_regions.append(region)
            try:
                logger.info(
                    f"[GoodWeLogin] Tentativa {attempt}/{len(regions_to_try)} | account={account} | region={region} | url={url}"
                )
                logger.debug(f"[GoodWeLogin] Headers iniciais: Token(Base64-json)={headers['Token'][:25]}...")
                self._dbg("--- GOODWE LOGIN ---")
                self._dbg(f"[LOGIN] Tentativa={attempt} region={region} url={url}")
                self._dbg(f"[LOGIN] account={account} (senha não exibida)")
                try:
                    self._dbg(f"[LOGIN] headers(Token prefix)={headers['Token'][:25]}... content-type={headers.get('Content-Type')}")
                    self._dbg(f"[LOGIN] payload={{'account': '{account}', 'pwd': '***', 'agreement_agreement': 0, 'is_local': False}}")
                except Exception:
                    pass
                response = self.session.post(url, json=payload, headers=headers, timeout=self.request_timeout)

                logger.info(f"[GoodWeLogin] HTTP {response.status_code} (region={region})")
                body_text = ''
                try:
                    body_text = response.text[:600]
                except Exception:
                    pass
                logger.debug(f"[GoodWeLogin] Raw body (truncado 600 chars) region={region}: {body_text}")
                try:
                    self._dbg(f"[LOGIN] HTTP {response.status_code} region={region}")
                    # Resposta bruta COMPLETA
                    self._dbg(f"[LOGIN] RAW RESPONSE: {response.text}")
                except Exception:
                    pass

                if response.status_code == 200:
                    try:
                        data = response.json()
                    except Exception as je:
                        logger.error(f"[GoodWeLogin] Falha ao parsear JSON: {je}")
                        continue
                    login_data = data.get("data")
                    if login_data:
                        # 1) Detectar e honrar base API retornada pelo login (nível raiz ou components)
                        try:
                            suggested_api = None
                            # Ex.: data nível raiz: { ..., "api": "https://us.semsportal.com/api/" }
                            if isinstance(data.get('api'), str):
                                suggested_api = data.get('api')
                            # Ex.: às vezes vem em components.api como URL completa para um endpoint; extrair host
                            elif isinstance(data.get('components', {}).get('api'), str):
                                suggested_api = data.get('components', {}).get('api')
                            if suggested_api:
                                try:
                                    u = urlparse(suggested_api)
                                    host = (u.netloc or '').split(':')[0]
                                    if 'eu.semsportal.com' in host:
                                        self.data_region = 'eu'
                                    elif 'us.semsportal.com' in host:
                                        self.data_region = 'us'
                                    # Força base https limpa
                                    if host:
                                        self._data_base_url_override = f"https://{host}/api/"
                                        logger.info(f"[GoodWeLogin] Base de dados definida via login: {self._data_base_url_override}")
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        # 2) Heurística secundária: checar campos dentro de login_data (menos comum)
                        for key in ('api', 'apiDomain', 'server'):
                            if key in login_data and isinstance(login_data[key], str):
                                host_str = login_data[key].lower()
                                if 'eu' in host_str:
                                    self.data_region = 'eu'
                                elif 'us' in host_str:
                                    self.data_region = 'us'
                                api_val = login_data[key]
                                if 'PowerStationMonitor' in api_val:
                                    base_part = api_val.split('PowerStationMonitor/')[0]
                                    if not base_part.endswith('/'):
                                        base_part += '/'
                                    # Normaliza para https e remove porta
                                    try:
                                        u2 = urlparse(base_part)
                                        host2 = (u2.netloc or '').split(':')[0]
                                        if host2:
                                            self._data_base_url_override = f"https://{host2}/api/"
                                        else:
                                            self._data_base_url_override = base_part
                                    except Exception:
                                        self._data_base_url_override = base_part
                                    logger.info(f"[GoodWeLogin] Override base dados detectado: {self._data_base_url_override}")
                        token = base64.b64encode(json.dumps(login_data).encode()).decode()
                        logger.info(
                            f"✅ Login bem-sucedido | login_region={region} | data_region={self.data_region} | token_prefix={token[:20]}..."
                        )
                        return token
                    else:
                        logger.error(f"[GoodWeLogin] Resposta sem campo 'data' (region={region}): {data}")
                else:
                    logger.error(
                        f"[GoodWeLogin] Falha HTTP {response.status_code} (region={region}) | body_trunc={body_text}"
                    )
            except requests.Timeout:
                logger.error(f"[GoodWeLogin] Timeout (region={region})")
                self._dbg(f"[LOGIN] Timeout na região {region}")
            except Exception as e:
                logger.error(f"❌ Erro no login (region={region}): {e}")
                self._dbg(f"[LOGIN] ERRO EXCEÇÃO region={region}: {e}")

        if tried_regions:
            self.region = tried_regions[0]
        logger.error(f"[GoodWeLogin] Todas as tentativas de login falharam. Tentado: {tried_regions}")

        return None

    def get_inverter_data_by_column(self, token: str, inv_id: str, column: str, date: str) -> dict | None:
        """
        Busca dados de uma coluna específica do inversor.

        Args:
            token: Token de autenticação
            inv_id: Serial Number do inversor
            column: Nome da coluna (ex: 'Pac', 'Cbattery1')
            date: Data no formato YYYY-MM-DD 00:00:00

        Returns:
            Dados da API ou None se falhar
        """
        base_primary = self._data_base_url_override or self._get_base_url()
        # Sanitização e restrição de candidatos
        allowed_hosts = {"eu.semsportal.com", "us.semsportal.com"}
        def sanitize_base(b: str):
            try:
                u = urlparse(b)
                scheme = u.scheme if u.scheme else ('https' if b.startswith('https') else 'https')
                netloc = u.netloc or b.replace('https://', '').replace('http://', '')
                host = netloc.split(':')[0]
                if self.strict_https:
                    if scheme != 'https' or host not in allowed_hosts:
                        return None
                return f"https://{host}/api/"
            except Exception:
                return None

        candidates = []
        if self.strict_https:
            # Preferir a base definida pelo login (override) sanitizada; se ausente, usar região de dados
            primary_host = sanitize_base(base_primary)
            if primary_host:
                candidates.append(primary_host)
            elif self.data_region in ("eu", "us"):
                candidates.append(f"https://{self.data_region}.semsportal.com/api/")
        else:
            sanitized = sanitize_base(base_primary) or base_primary
            candidates.append(sanitized)
            if self.data_region == 'eu':
                eu_base = 'https://eu.semsportal.com/api/'
                if eu_base not in candidates:
                    candidates.insert(0, eu_base)
                candidates = [c for c in candidates if c and 'us.semsportal.com' not in c] or [eu_base]
            else:
                if 'us.semsportal.com' in base_primary and 'eu.semsportal.com' not in base_primary:
                    eu_base = 'https://eu.semsportal.com/api/'
                    if eu_base not in candidates:
                        candidates.append(eu_base)

        # Aplicar atraso de 5 minutos para depuração nas chamadas que usam 'date'
        try:
            from datetime import datetime, timedelta
            # Se 'date' já vier como apenas data (YYYY-MM-DD), preservamos o formato;
            # se vier com hora, atrasamos em 5 minutos e mantemos o formato completo.
            if ' ' in date:
                base_dt = datetime.strptime(date, '%Y-%m-%d %H:%M:%S') if len(date) == 19 else datetime.now()
                delayed_dt = base_dt - timedelta(minutes=5)
                delayed_str = delayed_dt.strftime('%Y-%m-%d %H:%M:%S')
                print(f"DEBUG MODE: Usando timestamp com atraso de 5 minutos: {delayed_str}")
                date_for_request = delayed_str
            else:
                # apenas data (dia) — GoodWe geralmente aceita só a data; mantemos igual
                date_for_request = date
        except Exception:
            date_for_request = date

        # Fallback de formato de data: se vier com hora vamos tentar sem hora em retries
        date_variants = [date_for_request]
        if ' ' in date_for_request:
            just_date = date_for_request.split(' ')[0]
            if just_date not in date_variants:
                date_variants.append(just_date)

        headers_base = {"Content-Type": "application/json"}
        max_token_cycles = self.max_token_cycles
        token_cycle = 0
        current_token = token
        while token_cycle < max_token_cycles:
            for date_var in date_variants:
                for base in list(candidates):
                    url = f"{base}PowerStationMonitor/GetInverterDataByColumn"
                    headers = {**headers_base, "Token": current_token}
                    payload = {"id": inv_id, "date": date_var, "column": column}
                    try:
                        logger.info(f"[GoodWe] Fetch col={column} date={date_var} base={base} tokenCycle={token_cycle}")
                        self._dbg("--- GOODWE FETCH COLUMN ---")
                        self._dbg(f"[FETCH] base={base} column={column} date={date_var} tokenCycle={token_cycle}")
                        try:
                            self._dbg(f"[FETCH] headers(Token prefix)={headers.get('Token','')[:25]}... content-type={headers.get('Content-Type')}")
                            self._dbg(f"[FETCH] payload={payload}")
                        except Exception:
                            pass
                        response = self.session.post(url, json=payload, headers=headers, timeout=self.request_timeout)
                    except Exception as re:
                        logger.error(f"[GoodWe] Exceção request base={base}: {re}")
                        self._dbg(f"[FETCH] EXCEÇÃO na requisição base={base}: {re}")
                        continue
                    if response.status_code != 200:
                        logger.warning(f"[GoodWe] HTTP {response.status_code} base={base} body={response.text[:200]}")
                        self._dbg(f"[FETCH] HTTP {response.status_code} base={base}")
                        self._dbg(f"[FETCH] RAW RESPONSE: {response.text}")
                        continue
                    try:
                        data = response.json()
                    except Exception as je:
                        logger.error(f"[GoodWe] Falha parse JSON base={base}: {je}")
                        self._dbg(f"[FETCH] Falha parse JSON: {je}")
                        self._dbg(f"[FETCH] RAW RESPONSE: {response.text}")
                        continue
                    code = data.get('code') if isinstance(data, dict) else None
                    if code == 100002:
                        comp_api = data.get('components', {}).get('api') if isinstance(data, dict) else None
                        if comp_api and 'PowerStationMonitor' in comp_api:
                            base_part = comp_api.split('PowerStationMonitor/')[0]
                            if not base_part.endswith('/'):
                                base_part += '/'
                            sanitized = sanitize_base(base_part)
                            if self.strict_https:
                                if sanitized and sanitized not in candidates:
                                    candidates.append(sanitized)
                                    logger.info(f"[GoodWe] Adicionando base sugerida components.api={sanitized}")
                            else:
                                if base_part not in candidates:
                                    candidates.append(base_part)
                                    logger.info(f"[GoodWe] Adicionando base sugerida components.api={base_part}")
                        logger.warning(f"[GoodWe] code=100002 em base={base} date={date_var}")
                        self._dbg(f"[FETCH] code=100002 base={base} date={date_var} - adicionando fallback se disponível")
                        continue
                    logger.debug(f"[GoodWe] Sucesso base={base} date={date_var} code={code} keys={list(data.keys()) if isinstance(data, dict) else type(data)}")
                    self._dbg(f"[FETCH] SUCESSO base={base} date={date_var} code={code}")
                    self._dbg(f"[FETCH] RAW JSON: {data}")
                    try:
                        if 'eu.semsportal.com' in base and self.data_region != 'eu':
                            self.data_region = 'eu'
                            logger.info('[GoodWe] Ajustando data_region -> eu (auto-switch)')
                        elif 'us.semsportal.com' in base and self.data_region != 'us':
                            self.data_region = 'us'
                    except Exception:
                        pass
                    return data
            token_cycle += 1
            if self.account and self.password:
                logger.info(f"[GoodWe] Renovando token ciclo={token_cycle} devido a falhas/100002")
                self._dbg(f"[FETCH] Renovando token ciclo={token_cycle}")
                new_token = self.crosslogin(self.account, self.password)
                if not new_token:
                    logger.error("[GoodWe] Falha ao renovar token - abortando")
                    self._dbg("[FETCH] Falha ao renovar token - abortando")
                    break
                current_token = new_token
                if self._data_base_url_override and self._data_base_url_override not in candidates:
                    candidates.insert(0, self._data_base_url_override)
            else:
                logger.error("[GoodWe] Não há credenciais salvas para renovar token")
                self._dbg("[FETCH] Sem credenciais para renovar token")
                break
        logger.error("[GoodWe] Todas as tentativas esgotadas sem sucesso")
        self._dbg("[FETCH] Todas as tentativas esgotadas sem sucesso")
        return {"error": True, "msg": "Falha ao obter dados depois de retries", "code": 100002}

    def debug_raw_column_fetch(self, account: str, password: str, inv_id: str, column: str, date: str, region: str = 'us') -> dict:
        """Método de depuração que replica abordagem 'mínima' do professor.
        Não usa caches ou overrides, para comparar comportamento.
        """
        try:
            raw_token = self.crosslogin(account, password)
            if not raw_token:
                return {"error": True, "stage": "login", "details": "login falhou"}
            region_sanitized = region if region in ("eu", "us") else "eu"
            url = f"https://{region_sanitized}.semsportal.com/api/PowerStationMonitor/GetInverterDataByColumn"
            headers = {"Token": raw_token, "Content-Type": "application/json", "Accept": "*/*"}
            # Aplicar atraso de 5 minutos para depuração, se vier data/hora completa
            try:
                from datetime import datetime, timedelta
                if ' ' in date:
                    base_dt = datetime.strptime(date, '%Y-%m-%d %H:%M:%S') if len(date) == 19 else datetime.now()
                    delayed_dt = base_dt - timedelta(minutes=5)
                    date = delayed_dt.strftime('%Y-%m-%d %H:%M:%S')
                    print(f"DEBUG MODE: Usando timestamp com atraso de 5 minutos: {date}")
            except Exception:
                pass
            payload = {"date": date, "column": column, "id": inv_id}
            r = self.session.post(url, json=payload, headers=headers, timeout=30)
            return {"status": r.status_code, "body": r.text[:800]}
        except Exception as e:
            return {"error": True, "exception": str(e)}

    def get_realtime_data(self, powerstation_id: str | None = None, raw: bool = False) -> dict:
        """
        Busca dados em tempo real usando o endpoint GetMonitorDetailByPowerstationId.
        Este endpoint retorna o status instantâneo do inversor, não histórico.
        
        Args:
            powerstation_id: UUID da Power Station (opcional, usa env se não fornecido)
            
        Returns:
            Dict com dados em tempo real: potencia_atual, soc_bateria, geracao_dia, etc.
        """
        self._dbg("--- GOODWE GET_REALTIME_DATA ---")
        
        # Obter credenciais e IDs
        token = self._get_token()
        if not token:
            raise ValueError('Credenciais GoodWe ausentes ou login falhou')
        
        # Station ID pode vir como parâmetro ou do ambiente
        station_id = powerstation_id or os.getenv('SEMS_STATION_ID')
        if not station_id or station_id.strip() == '':
            logger.warning("SEMS_STATION_ID não configurado, usando fallback para inverter_id")
            # Fallback: tentar usar inverter_id (pode não funcionar com este endpoint)
            station_id = self.inverter_id
            if not station_id:
                raise ValueError('SEMS_STATION_ID e SEMS_INV_ID ausentes')
        
        # Determinar base URL
        base = self._data_base_url_override or self._get_base_url()
        # Endpoint de tempo real (v2)
        url = f"{base}v2/PowerStation/GetMonitorDetailByPowerstationId"
        
        headers = {"Token": token, "Content-Type": "application/json"}
        payload = {"powerstationId": station_id}
        
        logger.info(f"[GoodWe] Buscando dados em tempo real station_id={station_id}")
        self._dbg(f"[REALTIME] url={url} station_id={station_id}")
        
        try:
            response = self.session.post(url, json=payload, headers=headers, timeout=self.request_timeout)
        except Exception as req_err:
            logger.error(f"[GoodWe] Erro ao buscar dados em tempo real: {req_err}")
            self._dbg(f"[REALTIME] ERRO na requisição: {req_err}")
            raise
        
        if response.status_code != 200:
            logger.error(f"[GoodWe] HTTP {response.status_code} ao buscar tempo real")
            self._dbg(f"[REALTIME] HTTP {response.status_code} body={response.text[:300]}")
            raise ValueError(f"Erro HTTP {response.status_code} ao buscar dados em tempo real")
        
        try:
            data = response.json()
        except Exception as json_err:
            logger.error(f"[GoodWe] Falha parse JSON tempo real: {json_err}")
            self._dbg(f"[REALTIME] Falha parse JSON: {json_err}")
            raise
        
        # Se solicitado, retorna o JSON bruto da API sem qualquer processamento
        if raw:
            return data if isinstance(data, dict) else {'raw': data}
        
        # Log da resposta para análise
        self._dbg(f"[REALTIME] Resposta raw: {data}")
        logger.debug(f"[GoodWe] Tempo real code={data.get('code')} keys={list(data.keys()) if isinstance(data, dict) else type(data)}")
        
        # ✅ Extract real-time data from response (mapeamento definitivo via inverter[0].invert_full)
        # Estrutura: data -> inverter (lista) -> [0] -> invert_full -> { pac, eday, soc, pv_power, status }
        result_data = {}
        if isinstance(data, dict) and 'data' in data:
            api_data = data.get('data', {}) or {}
            inverters = api_data.get('inverter', []) if isinstance(api_data, dict) else []
            inv0 = inverters[0] if isinstance(inverters, list) and inverters else {}
            inv_full = inv0.get('invert_full', {}) if isinstance(inv0, dict) else {}

            # Valores finais segundo a especificação do SEMS (já em unidades corretas)
            pac = inv_full.get('pac', 0.0)  # Watts
            eday = inv_full.get('eday', 0.0)  # kWh
            soc = inv_full.get('soc', 0.0)   # %
            pv_power = inv_full.get('pv_power', 0.0)  # Watts (se disponível)

            # Status do sistema online/offline
            status_val = inv0.get('status', inv_full.get('status', -1))
            sistema_online = True if status_val == 1 else False

            # Sanitização robusta
            def fnum(v, default=0.0):
                try:
                    return float(v)
                except Exception:
                    return default

            pac = fnum(pac)
            eday = fnum(eday)
            soc = fnum(soc)
            pv_power = fnum(pv_power)

            result_data = {
                'potencia_atual': pac,
                'potencia_pv': pv_power,
                'soc_bateria': soc,
                'geracao_dia': eday,
                'sistema_online': sistema_online,
                'fonte_dados': 'GOODWE_REALTIME_API'
            }

            logger.info(f"[GoodWe] Tempo real (invert_full): pac={pac}W pv_power={pv_power}W soc={soc}% eday={eday}kWh online={sistema_online}")
        else:
            logger.warning(f"[GoodWe] Estrutura de resposta inesperada: keys={list(data.keys()) if isinstance(data, dict) else type(data)}")
            result_data = {
                'potencia_atual': 0.0,
                'potencia_pv': 0.0,
                'soc_bateria': 0.0,
                'geracao_dia': 0.0,
                'sistema_online': False,
                'fonte_dados': 'GOODWE_REALTIME_API',
                'error': 'Estrutura de resposta inesperada'
            }
        
        return result_data

    # ------------------------- Funções utilitárias internas ------------------------- #
    def _load_env_credentials(self):
        """Carrega credenciais do ambiente apenas uma vez."""
        if self.account and self.password and self.inverter_id:
            return
        self.account = os.getenv('SEMS_ACCOUNT')
        self.password = os.getenv('SEMS_PASSWORD')
        self.inverter_id = os.getenv('SEMS_INV_ID')
        self.login_region = os.getenv('SEMS_LOGIN_REGION', self.region or 'us').lower()
        self.data_region = os.getenv('SEMS_DATA_REGION', self.login_region).lower()
        self._dbg("--- GOODWE ENV CREDS ---")
        self._dbg(f"[CREDS] account set? {bool(self.account)} | inverter_id set? {bool(self.inverter_id)}")
        self._dbg(f"[CREDS] login_region={self.login_region} data_region={self.data_region}")

    def _get_token(self, force: bool = False) -> str | None:
        """Obtém (ou renova) token usando credenciais do ambiente.

        Args:
            force: força renovação
        """
        self._load_env_credentials()
        if not all([self.account, self.password]):
            logger.warning("Credenciais GoodWe não configuradas.")
            self._dbg("[TOKEN] Credenciais GoodWe não configuradas (account/password ausentes)")
            return None
        # Uso de cache (5 minutos)
        if not force and self._token_cache:
            ts = self._token_cache.get('ts')
            if ts and datetime.utcnow() - ts < timedelta(minutes=5):
                self._dbg("[TOKEN] Usando token em cache")
                return self._token_cache.get('token')
        # Fazer login na região de login
        prev_region = self.region
        try:
            self.region = self.login_region
            self._dbg(f"[TOKEN] Efetuando login na região {self.region}")
            token = self.crosslogin(self.account, self.password)
            if token:
                self._token_cache = {'token': token, 'ts': datetime.utcnow()}
                self._dbg("[TOKEN] Login OK, token obtido")
            else:
                self._dbg("[TOKEN] Falha ao obter token")
            return token
        finally:
            # Restaurar a região (evitar efeitos colaterais)
            self.region = prev_region

    @staticmethod
    def _extract_last_numeric(data_resp) -> float:
        """Extrai último valor numérico válido (> 0) de uma resposta variada da API.
        Para SOC e outros valores atuais, retorna o último valor não-zero da série."""
        try:
            if not data_resp:
                return 0.0
            # Algumas respostas vêm como dict com chave 'data'
            if isinstance(data_resp, dict):
                if 'data' in data_resp and isinstance(data_resp['data'], dict):
                    data_resp = data_resp['data']
                # Procura listas plausíveis
                for list_key in ('column1', 'list', 'items', 'datas', 'result', 'data'):
                    if list_key in data_resp and isinstance(data_resp[list_key], list) and data_resp[list_key]:
                        items = data_resp[list_key]
                        # Para valores atuais (SOC, potência), pegar último valor válido (> 0)
                        for item in reversed(items):
                            if isinstance(item, dict):
                                for val_key in ('column', 'value', 'val', 'v'):
                                    if val_key in item:
                                        try:
                                            val = float(item[val_key])
                                            if val > 0:  # Só retorna valores positivos
                                                return val
                                        except Exception:
                                            continue
                                for v in item.values():
                                    if isinstance(v, (int, float)) and v > 0:
                                        return float(v)
                            elif isinstance(item, (int, float)) and item > 0:
                                return float(item)
            # Se não achou, tentar se for lista direta
            if isinstance(data_resp, list) and data_resp:
                for item in reversed(data_resp):
                    if isinstance(item, (int, float)) and item > 0:
                        return float(item)
                    if isinstance(item, dict):
                        for val_key in ('column', 'value', 'val', 'v'):
                            if val_key in item:
                                try:
                                    val = float(item[val_key])
                                    if val > 0:
                                        return val
                                except Exception:
                                    continue
                        for v in item.values():
                            if isinstance(v, (int, float)) and v > 0:
                                return float(v)
        except Exception:
            pass
        return 0.0

    @staticmethod
    def _sum_series(data_resp) -> float:
        """Soma valores de uma série (usada para 'Eday')."""
        total = 0.0
        try:
            if not data_resp:
                return 0.0
            # Procurar arrays de pontos
            series_candidates = []
            if isinstance(data_resp, dict):
                d = data_resp.get('data', data_resp)
                if isinstance(d, dict):
                    for _, v in d.items():
                        if isinstance(v, list) and v:
                            series_candidates.append(v)
            elif isinstance(data_resp, list):
                series_candidates.append(data_resp)
            for serie in series_candidates:
                for point in serie:
                    if isinstance(point, (list, tuple)) and len(point) >= 2:
                        try:
                            total += float(point[1])
                        except Exception:
                            continue
                    elif isinstance(point, dict):
                        for val_key in ('value', 'val', 'v', 'column'):
                            if val_key in point:
                                try:
                                    total += float(point[val_key])
                                    break
                                except Exception:
                                    continue
            return total
        except Exception:
            return total

    @staticmethod
    def _last_series_value(data_resp) -> float:
        """Retorna o último valor de uma série tipo 'eday' (acumulado do dia)."""
        try:
            if not data_resp or not isinstance(data_resp, dict):
                return 0.0
            data_part = data_resp.get('data')
            if not isinstance(data_part, dict):
                return 0.0
            serie = data_part.get('column1')
            if not isinstance(serie, list) or not serie:
                return 0.0
            last = serie[-1]
            if isinstance(last, dict):
                v = last.get('column') or last.get('value') or last.get('val')
                if isinstance(v, (int, float)):
                    return float(v)
            return 0.0
        except Exception:
            return 0.0

    @staticmethod
    def _average_series(data_resp) -> float:
        """Calcula a média dos valores de uma série (ex.: SOC em 'Cbattery1')."""
        try:
            if not data_resp or not isinstance(data_resp, dict):
                return 0.0
            data_part = data_resp.get('data')
            if not isinstance(data_part, dict):
                return 0.0
            serie = data_part.get('column1')
            if not isinstance(serie, list) or not serie:
                return 0.0
            vals = []
            for p in serie:
                if isinstance(p, dict):
                    v = p.get('column') or p.get('value') or p.get('val')
                    if isinstance(v, (int, float)):
                        vals.append(float(v))
            if not vals:
                return 0.0
            return sum(vals) / len(vals)
        except Exception:
            return 0.0

    # ------------------------- Camada de Serviço / Agregação ------------------------- #
    def build_status(self) -> dict:
        """Retorna status consolidado do sistema (potência, SOC, etc)."""
        # Tentar usar endpoint de tempo real primeiro
        try:
            realtime_data = self.get_realtime_data()
            if realtime_data.get('sistema_online'):
                # Normalizar unidades (API pode retornar em W ou kW)
                pac = realtime_data.get('potencia_atual', 0.0)
                ppv = realtime_data.get('potencia_pv', 0.0)
                
                unit_cfg = os.getenv('GOODWE_PAC_UNIT', 'auto').lower()
                def to_watts(val: float) -> float:
                    if unit_cfg == 'kw':
                        return val * 1000.0
                    if unit_cfg == 'w':
                        return val
                    # auto: heurística — valores entre 0 e 50 provavelmente estão em kW
                    if 0 < val < 50:
                        return val * 1000.0
                    return val
                
                pac_w = to_watts(pac)
                ppv_w = to_watts(ppv)
                
                return {
                    'sistema_online': True,
                    'potencia_pv': round(ppv_w, 1),
                    'potencia_atual': round(pac_w, 1),
                    'soc_bateria': round(realtime_data.get('soc_bateria', 0.0), 1),
                    'temperatura': 0,
                    'status_inversor': 'Operando' if pac_w > 0 else 'Standby',
                    'ultima_atualizacao': datetime.utcnow().isoformat() + 'Z',
                    'fonte_dados': 'GOODWE_REALTIME_API',
                    'inverter_id': self.inverter_id
                }
        except Exception as rt_err:
            logger.warning(f"Falha ao buscar dados em tempo real, usando fallback histórico: {rt_err}")
            self._dbg(f"[STATUS] Erro tempo real, fallback para histórico: {rt_err}")
        
        # Fallback: usar endpoint histórico (GetInverterDataByColumn)
        token = self._get_token()
        if not token:
            raise ValueError('Credenciais GoodWe ausentes ou login falhou')
        if not self.inverter_id:
            raise ValueError('SEMS_INV_ID não configurado')
        date_today = datetime.now().strftime('%Y-%m-%d')
        prev_region = self.region
        # Forçar uso da data_region se já detectada (auto-switch)
        self.region = self.data_region
        self._dbg("--- GOODWE BUILD_STATUS (FALLBACK HISTÓRICO) ---")
        self._dbg(f"[STATUS] date_today={date_today} data_region={self.data_region}")
        try:
            results = {}
            for col in ('ppv', 'pac', 'Cbattery1'):
                try:
                    resp = self.get_inverter_data_by_column(token, self.inverter_id, col, date_today)
                    results[col] = resp
                    self._dbg(f"[STATUS] col={col} resp_raw={resp}")
                except Exception as e:
                    logger.warning(f"Falha ao buscar coluna {col}: {e}")
                    self._dbg(f"[STATUS] Erro ao buscar col {col}: {e}")
        finally:
            self.region = prev_region
        # Extração e normalização de unidades
        ppv = self._extract_last_numeric(results.get('ppv'))
        pac = self._extract_last_numeric(results.get('pac'))
        self._dbg(f"[STATUS] ppv_raw={ppv} pac_raw={pac}")
        soc = self._extract_last_numeric(results.get('Cbattery1'))
        unit_cfg = os.getenv('GOODWE_PAC_UNIT', 'auto').lower()  # 'w' | 'kw' | 'auto'
        def to_watts(val: float) -> float:
            if unit_cfg == 'kw':
                return val * 1000.0
            if unit_cfg == 'w':
                return val
            # auto: heurística simples — valores entre 0 e 50 provavelmente estão em kW
            if 0 < val < 50:
                print(f"DEBUG MODE: Detectado pac em kW ({val}), convertendo para W")
                return val * 1000.0
            return val
        pac_w = to_watts(pac)
        ppv_w = to_watts(ppv)
        self._dbg(f"[STATUS] ppv_w={ppv_w} pac_w={pac_w} soc={soc}")
        return {
            'sistema_online': True,
            'potencia_pv': round(ppv_w, 1),
            'potencia_atual': round(pac_w, 1),  # AC instantânea
            'soc_bateria': round(soc, 1) if isinstance(soc, (int, float)) else 0.0,
            'temperatura': 0,
            'status_inversor': 'Operando' if pac_w > 0 else 'Standby',
            'ultima_atualizacao': datetime.utcnow().isoformat() + 'Z',
            'fonte_dados': 'GOODWE_SEMS_API',
            'inverter_id': self.inverter_id
        }

    def build_data(self) -> dict:
        """Retorna dados agregados (produção, consumo estimado, bateria, economia).

        Preferir dados em tempo real quando disponíveis; caso contrário, cair para o histórico.
        Estrutura de retorno preserva chaves esperadas pela rota/dashboard atuais.
        """
        # 1) Tentar realtime primeiro
        try:
            realtime = self.get_realtime_data()
            if realtime and isinstance(realtime, dict) and realtime.get('sistema_online') is not None:
                # Tarifa configurável
                try:
                    tarifa = float(os.getenv('ECONOMIA_TARIFA_KWH', '0.85'))
                except Exception:
                    tarifa = 0.85
                producao_hoje = round(float(realtime.get('geracao_dia', 0.0)), 2)
                potencia_atual_w = round(float(realtime.get('potencia_atual', 0.0)), 1)
                soc_atual = round(float(realtime.get('soc_bateria', 0.0)), 1)
                return {
                    'producao': {
                        'hoje': producao_hoje,
                        'mes': None,
                        'ano': None
                    },
                    'consumo': {
                        'hoje': round(producao_hoje * 0.75, 2),
                        'mes': None,
                        'ano': None
                    },
                    'bateria': {
                        'soc': soc_atual,
                        'capacidade_total': 10.0,
                        'status': 'Carregando' if potencia_atual_w > 0 else 'Standby',
                        'potencia_atual': potencia_atual_w
                    },
                    'economia': {
                        'hoje': round(producao_hoje * tarifa, 2),
                        'mes': None,
                        'ano': None
                    },
                    'meta_dados': {
                        'fonte_dados': 'GOODWE_REALTIME_API',
                        'inverter_id': self.inverter_id,
                        'ultima_sincronizacao': datetime.utcnow().isoformat() + 'Z'
                    }
                }
        except Exception as rt_err:
            logger.warning(f"[DATA] Tempo real indisponível, fallback histórico: {rt_err}")
            self._dbg(f"[DATA] Fallback histórico por erro realtime: {rt_err}")

        # 2) Fallback: histórico (implementação anterior)
        token = self._get_token()
        if not token:
            raise ValueError('Credenciais GoodWe ausentes ou login falhou')
        if not self.inverter_id:
            raise ValueError('SEMS_INV_ID não configurado')
        today = datetime.now().strftime('%Y-%m-%d')
        prev_region = self.region
        self.region = self.data_region
        self._dbg("--- GOODWE BUILD_DATA (FALLBACK HIST) ---")
        self._dbg(f"[DATA] today={today} data_region={self.data_region}")
        try:
            eday_resp = self.get_inverter_data_by_column(token, self.inverter_id, 'eday', today)
            battery_series_resp = self.get_inverter_data_by_column(token, self.inverter_id, 'Cbattery1', today)
            pac_resp = self.get_inverter_data_by_column(token, self.inverter_id, 'pac', today)
            self._dbg(f"[DATA] eday_raw={eday_resp}")
            self._dbg(f"[DATA] Cbattery1_raw={battery_series_resp}")
            self._dbg(f"[DATA] pac_raw={pac_resp}")
        finally:
            self.region = prev_region
        producao_hoje = round(self._last_series_value(eday_resp), 2)
        soc_atual = 0.0
        if isinstance(battery_series_resp, dict):
            soc_atual = round(self._extract_last_numeric(battery_series_resp), 1)
        pac_val = self._extract_last_numeric(pac_resp)
        unit_cfg = os.getenv('GOODWE_PAC_UNIT', 'auto').lower()
        if unit_cfg == 'kw':
            potencia_atual = round(pac_val * 1000.0, 1)
        elif unit_cfg == 'w':
            potencia_atual = round(pac_val, 1)
        else:
            potencia_atual = round(pac_val * 1000.0, 1) if 0 < pac_val < 50 else round(pac_val, 1)
        # Mensal (opcional)
        producao_mes = 0.0
        prev_region_loop = self.region
        self.region = self.data_region
        try:
            for i in range(30):
                date_check = datetime.now() - timedelta(days=i)
                date_str = date_check.strftime('%Y-%m-%d')
                try:
                    daily_resp = self.get_inverter_data_by_column(token, self.inverter_id, 'eday', date_str)
                    producao_mes += self._last_series_value(daily_resp)
                except Exception:
                    continue
        finally:
            self.region = prev_region_loop
        try:
            taxa_kwh = float(os.getenv('ECONOMIA_TARIFA_KWH', '0.85'))
        except Exception:
            taxa_kwh = 0.85
        return {
            'producao': {
                'hoje': producao_hoje,
                'mes': round(producao_mes, 2),
                'ano': round(producao_mes * 12, 2)
            },
            'consumo': {
                'hoje': round(producao_hoje * 0.75, 2),
                'mes': round(producao_mes * 0.75, 2),
                'ano': round(producao_mes * 12 * 0.75, 2)
            },
            'bateria': {
                'soc': soc_atual,
                'capacidade_total': 10.0,
                'status': 'Carregando' if potencia_atual > 0 else 'Standby',
                'potencia_atual': potencia_atual
            },
            'economia': {
                'hoje': round(producao_hoje * taxa_kwh, 2),
                'mes': round(producao_mes * taxa_kwh, 2),
                'ano': round(producao_mes * 12 * taxa_kwh, 2)
            },
            'meta_dados': {
                'fonte_dados': 'GOODWE_SEMS_API',
                'inverter_id': self.inverter_id,
                'ultima_sincronizacao': datetime.utcnow().isoformat() + 'Z'
            }
        }

    def build_history(self, days: int = 7) -> list:
        """Retorna histórico (lista) de produção dos últimos N dias."""
        token = self._get_token()
        if not token:
            raise ValueError('Credenciais GoodWe ausentes ou login falhou')
        if not self.inverter_id:
            raise ValueError('SEMS_INV_ID não configurado')
        days = min(max(1, days), 30)
        taxa_kwh = 0.85
        historico = []
        prev_region_hist = self.region
        self.region = self.data_region
        try:
            for i in range(days):
                date_obj = datetime.now() - timedelta(days=i)
                date_str = date_obj.strftime('%Y-%m-%d')
                try:
                    prod_resp = self.get_inverter_data_by_column(token, self.inverter_id, 'eday', date_str)
                    battery_series_resp = self.get_inverter_data_by_column(token, self.inverter_id, 'Cbattery1', date_str)
                    self._dbg(f"[HISTORY] date={date_str} eday_raw={prod_resp}")
                    self._dbg(f"[HISTORY] date={date_str} Cbattery1_raw={battery_series_resp}")
                except Exception:
                    prod_resp = None
                    battery_series_resp = None
                producao_dia = round(self._last_series_value(prod_resp), 2)
                soc_avg = round(self._average_series(battery_series_resp), 1) if battery_series_resp else None
                consumo_estimado = round(producao_dia * 0.75, 2)
                economia = round(producao_dia * taxa_kwh, 2)
                historico.append({
                    'data': date_str,
                    'producao': producao_dia,
                    'consumo': consumo_estimado,
                    'economia': economia,
                    'soc_medio': soc_avg if soc_avg and soc_avg > 0 else None,
                    'dia_semana': date_obj.strftime('%A')
                })
        finally:
            self.region = prev_region_hist
        historico.reverse()
        self._dbg(f"[HISTORY] dias={len(historico)} -> {historico}")
        return historico

    def build_intraday_series(self) -> dict:
        """Busca séries intradiárias (Pac e SOC) para o dia atual."""
        self._dbg("--- GOODWE BUILD_INTRADAY ---")
        # Observação: Este método depende de fluxo alternativo. Use get_inverter_data_by_column diretamente.
        token = self._get_token()
        if not token:
            raise ValueError("Credenciais GoodWe ausentes ou login falhou")
        today_str = datetime.now().strftime('%Y-%m-%d')
        logger.info(f"Buscando dados intradiários para {today_str}...")

        try:
            # Não há endpoint batch no cliente atual; chamadas individuais são necessárias
            pac_resp = self.get_inverter_data_by_column(token, self.inverter_id, 'pac', today_str)
            soc_resp = self.get_inverter_data_by_column(token, self.inverter_id, 'Cbattery1', today_str)
            # Padroniza a saída para garantir que as chaves sempre existam
            pac_series = pac_resp.get('data', {}).get('column1', []) if isinstance(pac_resp, dict) else []
            soc_series = soc_resp.get('data', {}).get('column1', []) if isinstance(soc_resp, dict) else []
            self._dbg(f"[INTRADAY] pac_raw={pac_resp}")
            self._dbg(f"[INTRADAY] Cbattery1_raw={soc_resp}")

            return {
                'date': today_str,
                'series': {
                    'pac': pac_series,
                    'soc': soc_series,
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Falha ao buscar dados intradiários: {e}")
            self._dbg(f"[INTRADAY] ERRO: {e}")
            # Retorna uma estrutura vazia em caso de erro para não quebrar o frontend
            return {
                'date': today_str,
                'series': {'pac': [], 'soc': []},
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }