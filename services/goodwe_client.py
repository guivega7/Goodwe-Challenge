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
                response = self.session.post(url, json=payload, headers=headers, timeout=30)

                logger.info(f"[GoodWeLogin] HTTP {response.status_code} (region={region})")
                body_text = ''
                try:
                    body_text = response.text[:600]
                except Exception:
                    pass
                logger.debug(f"[GoodWeLogin] Raw body (truncado 600 chars) region={region}: {body_text}")

                if response.status_code == 200:
                    try:
                        data = response.json()
                    except Exception as je:
                        logger.error(f"[GoodWeLogin] Falha ao parsear JSON: {je}")
                        continue
                    login_data = data.get("data")
                    if login_data:
                        for key in ('api', 'apiDomain', 'server'):
                            if key in login_data and isinstance(login_data[key], str):
                                host = login_data[key].lower()
                                if 'eu' in host:
                                    self.data_region = 'eu'
                                elif 'us' in host:
                                    self.data_region = 'us'
                                api_val = login_data[key]
                                if 'PowerStationMonitor' in api_val:
                                    base_part = api_val.split('PowerStationMonitor/')[0]
                                    if not base_part.endswith('/'):
                                        base_part += '/'
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
            except Exception as e:
                logger.error(f"❌ Erro no login (region={region}): {e}")

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
        candidates = [base_primary]
        # Estratégia de otimização: se já confirmamos que data_region é EU, priorizar (ou forçar) EU
        if self.data_region == 'eu':
            eu_base = 'https://eu.semsportal.com/api/'
            if eu_base not in candidates:
                candidates.insert(0, eu_base)
            # Se base primária ainda for US, podemos remover para não gerar logs/code=100002 desnecessários
            candidates = [c for c in candidates if 'us.semsportal.com' not in c] or [eu_base]
        else:
            # Caso ainda não confirmado EU e base seja US, incluir EU cedo para fallback rápido
            if 'us.semsportal.com' in base_primary and 'eu.semsportal.com' not in base_primary:
                eu_base = 'https://eu.semsportal.com/api/'
                if eu_base not in candidates:
                    candidates.append(eu_base)

        # Fallback de formato de data: se vier com hora vamos tentar sem hora em retries
        date_variants = [date]
        if ' ' in date:
            just_date = date.split(' ')[0]
            if just_date not in date_variants:
                date_variants.append(just_date)
        headers_base = {"Content-Type": "application/json"}
        max_token_cycles = 2
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
                        response = self.session.post(url, json=payload, headers=headers, timeout=30)
                    except Exception as re:
                        logger.error(f"[GoodWe] Exceção request base={base}: {re}")
                        continue
                    if response.status_code != 200:
                        logger.warning(f"[GoodWe] HTTP {response.status_code} base={base} body={response.text[:200]}")
                        continue
                    try:
                        data = response.json()
                    except Exception as je:
                        logger.error(f"[GoodWe] Falha parse JSON base={base}: {je}")
                        continue
                    code = data.get('code') if isinstance(data, dict) else None
                    if code == 100002:
                        comp_api = data.get('components', {}).get('api') if isinstance(data, dict) else None
                        if comp_api and 'PowerStationMonitor' in comp_api:
                            base_part = comp_api.split('PowerStationMonitor/')[0]
                            if not base_part.endswith('/'):
                                base_part += '/'
                            if base_part not in candidates:
                                candidates.append(base_part)
                                logger.info(f"[GoodWe] Adicionando base sugerida components.api={base_part}")
                        logger.warning(f"[GoodWe] code=100002 em base={base} date={date_var}")
                        continue
                    logger.debug(f"[GoodWe] Sucesso base={base} date={date_var} code={code} keys={list(data.keys()) if isinstance(data, dict) else type(data)}")
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
                new_token = self.crosslogin(self.account, self.password)
                if not new_token:
                    logger.error("[GoodWe] Falha ao renovar token - abortando")
                    break
                current_token = new_token
                if self._data_base_url_override and self._data_base_url_override not in candidates:
                    candidates.insert(0, self._data_base_url_override)
            else:
                logger.error("[GoodWe] Não há credenciais salvas para renovar token")
                break
        logger.error("[GoodWe] Todas as tentativas esgotadas sem sucesso")
        return {"error": True, "msg": "Falha ao obter dados depois de retries", "code": 100002}

    def debug_raw_column_fetch(self, account: str, password: str, inv_id: str, column: str, date: str, region: str = 'us') -> dict:
        """Método de depuração que replica abordagem 'mínima' do professor.
        Não usa caches ou overrides, para comparar comportamento.
        """
        try:
            raw_token = self.crosslogin(account, password)
            if not raw_token:
                return {"error": True, "stage": "login", "details": "login falhou"}
            url = f"https://{region}.semsportal.com/api/PowerStationMonitor/GetInverterDataByColumn"
            headers = {"Token": raw_token, "Content-Type": "application/json", "Accept": "*/*"}
            payload = {"date": date, "column": column, "id": inv_id}
            r = self.session.post(url, json=payload, headers=headers, timeout=30)
            return {"status": r.status_code, "body": r.text[:800]}
        except Exception as e:
            return {"error": True, "exception": str(e)}

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

    def _get_token(self, force: bool = False) -> str | None:
        """Obtém (ou renova) token usando credenciais do ambiente.

        Args:
            force: força renovação
        """
        self._load_env_credentials()
        if not all([self.account, self.password]):
            logger.warning("Credenciais GoodWe não configuradas.")
            return None
        # Uso de cache (5 minutos)
        if not force and self._token_cache:
            ts = self._token_cache.get('ts')
            if ts and datetime.utcnow() - ts < timedelta(minutes=5):
                return self._token_cache.get('token')
        # Fazer login na região de login
        prev_region = self.region
        try:
            self.region = self.login_region
            token = self.crosslogin(self.account, self.password)
            if token:
                self._token_cache = {'token': token, 'ts': datetime.utcnow()}
            return token
        finally:
            # Restaurar a região (evitar efeitos colaterais)
            self.region = prev_region

    @staticmethod
    def _extract_last_numeric(data_resp) -> float:
        """Extrai último valor numérico de uma resposta variada da API.
        Reaproveita lógica parecida usada em dashboard."""
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
                        last = data_resp[list_key][-1]
                        if isinstance(last, dict):
                            for val_key in ('column', 'value', 'val', 'v'):
                                if val_key in last:
                                    try:
                                        return float(last[val_key])
                                    except Exception:
                                        continue
                            for v in last.values():
                                if isinstance(v, (int, float)):
                                    return float(v)
                        elif isinstance(last, (int, float)):
                            return float(last)
                # Se não achou, tentar se for lista direta
            if isinstance(data_resp, list) and data_resp:
                last = data_resp[-1]
                if isinstance(last, (int, float)):
                    return float(last)
                if isinstance(last, dict):
                    for val_key in ('column', 'value', 'val', 'v'):
                        if val_key in last:
                            try:
                                return float(last[val_key])
                            except Exception:
                                continue
                    for v in last.values():
                        if isinstance(v, (int, float)):
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
                for k, v in d.items():
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
        token = self._get_token()
        if not token:
            raise ValueError('Credenciais GoodWe ausentes ou login falhou')
        if not self.inverter_id:
            raise ValueError('SEMS_INV_ID não configurado')
        date_today = datetime.now().strftime('%Y-%m-%d 00:00:00')
        prev_region = self.region
        # Forçar uso da data_region se já detectada (auto-switch)
        self.region = self.data_region
        try:
            results = {}
            for col in ('ppv', 'pac', 'Cbattery1'):
                try:
                    resp = self.get_inverter_data_by_column(token, self.inverter_id, col, date_today)
                    results[col] = resp
                except Exception as e:
                    logger.warning(f"Falha ao buscar coluna {col}: {e}")
        finally:
            self.region = prev_region
        ppv = self._extract_last_numeric(results.get('ppv'))
        pac = self._extract_last_numeric(results.get('pac'))
        soc = self._extract_last_numeric(results.get('Cbattery1'))
        return {
            'sistema_online': True,
            'potencia_pv': ppv,
            'potencia_ac': pac,
            'soc_bateria': soc,
            'temperatura': 0,
            'status_inversor': 'Operando' if pac > 0 else 'Standby',
            'ultima_atualizacao': datetime.utcnow().isoformat() + 'Z',
            'fonte_dados': 'GOODWE_SEMS_API',
            'inverter_id': self.inverter_id
        }

    def build_data(self) -> dict:
        """Retorna dados agregados (produção, consumo estimado, bateria, economia)."""
        token = self._get_token()
        if not token:
            raise ValueError('Credenciais GoodWe ausentes ou login falhou')
        if not self.inverter_id:
            raise ValueError('SEMS_INV_ID não configurado')
        today = datetime.now().strftime('%Y-%m-%d')
        # Alterar para região de dados para coleta
        prev_region = self.region
        self.region = self.data_region
        try:
            eday_resp = self.get_inverter_data_by_column(token, self.inverter_id, 'eday', today)
            battery_series_resp = self.get_inverter_data_by_column(token, self.inverter_id, 'Cbattery1', today)
            pac_resp = self.get_inverter_data_by_column(token, self.inverter_id, 'pac', today)
        finally:
            self.region = prev_region
        producao_hoje = round(self._last_series_value(eday_resp), 2)
        soc_atual = 0.0
        if isinstance(battery_series_resp, dict):
            soc_atual = round(self._extract_last_numeric(battery_series_resp), 1)
        potencia_atual = round(self._extract_last_numeric(pac_resp), 1)
        # Produção mensal (últimos 30 dias)
        producao_mes = 0.0
        # Forçar uso da região de dados durante o loop mensal para evitar tentativas US redundantes
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
        return historico

    def build_intraday_series(self) -> dict:
        """Busca séries intradiárias (Pac e SOC) para o dia atual."""
        if not self.token:
            self._ensure_login()
        if not self.token:
            raise ValueError("Credenciais GoodWe ausentes ou login falhou")

        today_str = datetime.now().strftime('%Y-%m-%d')
        logger.info(f"Buscando dados intradiários para {today_str}...")

        try:
            series = self.get_inverter_data_by_column(
                ['Pac', 'Cbattery1'],
                today_str
            )
            # Padroniza a saída para garantir que as chaves sempre existam
            pac_series = series.get('Pac', [])
            soc_series = series.get('Cbattery1', [])

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
            # Retorna uma estrutura vazia em caso de erro para não quebrar o frontend
            return {
                'date': today_str,
                'series': {'pac': [], 'soc': []},
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }