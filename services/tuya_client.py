"""Tuya Smart Plug Client

Integração com a Tuya OpenAPI para coletar status e consumo de energia
para dispositivos (ex: tomada inteligente) integráveis via Tuya.

Documentação: https://developer.tuya.com
"""
from __future__ import annotations
import os
import time
import logging
from typing import Any, Dict, Optional

from dotenv import load_dotenv

try:
    from tuya_connector import TuyaOpenAPI, TuyaOpenPulsar  # type: ignore
    _TUYA_LIB_OK = True
except ImportError:  # Biblioteca ainda não instalada
    # Usamos flag para detectar ausência e fornecer mensagem clara ao usuário
    TuyaOpenAPI = object  # type: ignore
    TuyaOpenPulsar = object  # type: ignore
    _TUYA_LIB_OK = False

load_dotenv()
logger = logging.getLogger(__name__)


def _env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(key, default)


class TuyaClient:
    """Cliente simples para acesso à Tuya OpenAPI.

    Fluxo:
    1. Conecta usando ACCESS_ID / ACCESS_SECRET
    2. Recupera status do device
    3. Recupera métricas de energia (se suportado)
    """

    def __init__(self,
                 access_id: Optional[str] = None,
                 access_secret: Optional[str] = None,
                 endpoint: Optional[str] = None,
                 device_id: Optional[str] = None,
                 region: Optional[str] = None):
        self.access_id = access_id or _env("TUYA_ACCESS_ID")
        self.access_secret = access_secret or _env("TUYA_ACCESS_SECRET")
        # Endpoint pode variar por região. Ex: https://openapi.tuyaus.com, https://openapi.tuyaeu.com
        self.endpoint = endpoint or _env("TUYA_ENDPOINT", "https://openapi.tuyaus.com")
        self.device_id = device_id or _env("TUYA_DEVICE_ID")
        self.region = region or _env("TUYA_REGION")  # Opcional se for usar futuros recursos
        self.user_id = _env("TUYA_USER_ID")  # Para fallback em listagem de devices

        if not (self.access_id and self.access_secret):
            raise ValueError("Credenciais Tuya não configuradas (TUYA_ACCESS_ID / TUYA_ACCESS_SECRET)")

        # Verificação explícita da biblioteca para evitar erro genérico: object() takes no arguments
        if not _TUYA_LIB_OK:
            raise ImportError(
                "Biblioteca 'tuya-connector-python' não instalada. Instale com: pip install tuya-connector-python"
            )

        try:
            self.api = TuyaOpenAPI(self.endpoint, self.access_id, self.access_secret)
            self.api.connect()
            logger.info("Conectado à Tuya OpenAPI")
        except Exception as e:
            logger.error(f"Falha ao conectar na Tuya OpenAPI: {e}")
            raise

    # -------------------- Métodos Internos -------------------- #
    def _ensure_device_id(self):
        if not self.device_id:
            raise ValueError("TUYA_DEVICE_ID não configurado no .env")

    # -------------------- Métodos Públicos -------------------- #
    def get_device_status(self) -> Dict[str, Any]:
        """Retorna status bruto do dispositivo (dps / propriedades)."""
        self._ensure_device_id()
        try:
            response = self.api.get(f"/v1.0/devices/{self.device_id}")
            return response or {}
        except Exception as e:
            logger.error(f"Erro ao obter status device Tuya: {e}")
            return {"error": str(e)}

    def get_device_status_by_id(self, device_id: str) -> Dict[str, Any]:
        """Retorna status para um device arbitrário (sem alterar self.device_id)."""
        try:
            response = self.api.get(f"/v1.0/devices/{device_id}")
            return response or {}
        except Exception as e:
            logger.error(f"Erro ao obter status device Tuya {device_id}: {e}")
            return {"error": str(e)}

    def list_devices(self, include_raw: bool = False) -> Dict[str, Any]:
        """Lista dispositivos vinculados.

        Estratégia em camadas:
        1. /v1.0/devices (padrão)
        2. /v1.0/users/{user_id}/devices (se code 1100 ou vazio e tiver TUYA_USER_ID)
        3. Fallback: monta lista sintética a partir de TUYA_DEVICE_ID + status
        Retorna sempre em formato compatível: {'result': {'devices': [...]}}
        """
        raw_attempts = {}
        devices: list[Dict[str, Any]] = []
        fallback_used = None
        success = False
        try:
            primary = self.api.get("/v1.0/devices")
            raw_attempts['primary'] = primary
            # Estrutura esperada: {'success': True, 'result': [...] OU {'devices': [...]}}
            if primary:
                if primary.get('success') and primary.get('result'):
                    r = primary['result']
                    if isinstance(r, list):
                        devices = r
                    elif isinstance(r, dict):
                        if isinstance(r.get('devices'), list):
                            devices = r['devices']
                        elif isinstance(r.get('list'), list):
                            devices = r['list']
                # Se retornou erro code 1100 ou lista vazia, tentar fallback user
                if (not devices) and (primary.get('code') == 1100 or not primary.get('success')) and self.user_id:
                    try:
                        user_resp = self.api.get(f"/v1.0/users/{self.user_id}/devices")
                        raw_attempts['user_devices'] = user_resp
                        if user_resp and user_resp.get('success') and user_resp.get('result'):
                            r2 = user_resp['result']
                            if isinstance(r2, list):
                                devices = r2
                            elif isinstance(r2, dict):
                                if isinstance(r2.get('devices'), list):
                                    devices = r2['devices']
                                elif isinstance(r2.get('list'), list):
                                    devices = r2['list']
                            if devices:
                                fallback_used = 'user_devices'
                    except Exception as ue:
                        logger.warning(f"Fallback user_devices falhou: {ue}")
            # Fallback final sintético
            if not devices and self.device_id:
                try:
                    status_one = self.get_device_status()
                    raw_attempts['single_status'] = status_one
                    res = status_one.get('result') or {}
                    name = res.get('name') or f"Device {self.device_id[:6]}"
                    devices = [{
                        'id': self.device_id,
                        'name': name,
                        'category': res.get('category'),
                        'product_name': res.get('product_name') or res.get('name')
                    }]
                    fallback_used = 'single_fallback'
                except Exception as se:
                    logger.warning(f"Fallback single device falhou: {se}")
            success = bool(devices)
        except Exception as e:
            logger.error(f"Erro ao listar dispositivos Tuya (sequência): {e}")
            return {
                'error': str(e),
                'success': False,
                'result': {'devices': []},
                'fallback': fallback_used,
                'raw': raw_attempts if include_raw else None
            }

        return {
            'success': success,
            'fallback': fallback_used,
            'result': {'devices': devices},
            **({'raw': raw_attempts} if include_raw else {})
        }

    # Alias usado pelo device_sync (nome anterior)
    def get_device_list(self) -> Dict[str, Any]:  # compat
        return self.list_devices()

    def get_device_functions(self) -> Dict[str, Any]:
        """Retorna funções suportadas (para saber quais comandos existem)."""
        self._ensure_device_id()
        try:
            response = self.api.get(f"/v1.0/devices/{self.device_id}/functions")
            return response or {}
        except Exception as e:
            logger.error(f"Erro ao obter funções device Tuya: {e}")
            return {"error": str(e)}

    def get_energy_today(self) -> Dict[str, Any]:
        """Tenta obter consumo de energia do dia atual.

        Muitos dispositivos expõem estatísticas via endpoints específicos ou dps.
        Este método tenta alguns caminhos comuns.
        """
        self._ensure_device_id()
        # Endpoint genérico de estatísticas (pode variar conforme o tipo de device)
        try:
            # Alguns dispositivos usam estatísticas por tipo, ex: power, electricity, etc.
            # Documentação: Statistic API (necessário ativar no console Tuya)
            # Aqui fazemos uma chamada exemplo. Ajuste conforme retorno real.
            # Exemplo de endpoint: /v1.0/devices/{device_id}/statistics/daily?code=add_ele&start_day=20250101&end_day=20250101
            # Para simplificar: retornamos status e filtramos dps de energia se houver.
            status = self.get_device_status()
            result = status.get("result", {})
            # Alguns dps comuns: cur_power, voltage, cur_current, add_ele (energia acumulada)
            energy_keys = [k for k in (result if isinstance(result, dict) else {})]
            return {
                "raw": status,
                "keys": energy_keys,
            }
        except Exception as e:
            logger.error(f"Erro ao obter energia Tuya: {e}")
            return {"error": str(e)}

    def simple_snapshot(self) -> Dict[str, Any]:
        """Retorna um snapshot consolidado para uso no endpoint."""
        status = self.get_device_status()
        energy = self.get_energy_today()
        parsed = self.parse_metrics(status)
        return {
            "device_id": self.device_id,
            "status": status.get("result"),
            "metrics": parsed,
            "energy": energy,
            "timestamp": int(time.time())
        }

    # ----------- Novos métodos de parsing de métricas ----------- #
    def parse_metrics(self, status_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai métricas padronizadas dos dados de status.

        A resposta típica da Tuya para GET /devices/{id} tem a forma:
        {
          "result": {
             "category": "cz",
             "name": "Tomada X",
             "online": true,
             "status": [ {"code": "switch_1", "value": true}, {"code": "cur_power", "value": 123} ]
          }
        }
        """
        result = status_response.get("result") or {}
        status_list = result.get("status") or []
        metrics: Dict[str, Any] = {
            "power_w": None,
            "voltage_v": None,
            "current_a": None,
            "energy_wh": None,
            "switch_on": None,
        }
        # Mapear códigos comuns
        for item in status_list:
            code = item.get("code")
            val = item.get("value")
            if code in ("switch", "switch_1"):
                metrics["switch_on"] = bool(val)
            elif code in ("cur_power", "power", "power_w"):
                try:
                    fval = float(val)
                    # Heurística: valores grandes podem estar em décimos de watt
                    metrics["power_w"] = fval / 10.0 if fval > 200 else fval
                except Exception:
                    metrics["power_w"] = None
            elif code in ("cur_voltage", "voltage"):
                try:
                    fval = float(val)
                    metrics["voltage_v"] = fval / 10.0 if fval > 300 else fval
                except Exception:
                    metrics["voltage_v"] = None
            elif code in ("cur_current", "current"):
                # Algumas tomadas retornam em mA -> normalizar se valor for muito grande
                try:
                    fval = float(val)
                    metrics["current_a"] = fval / 1000.0 if fval > 50 else fval
                except Exception:
                    metrics["current_a"] = None
            elif code in ("add_ele", "energy", "ele_sum"):
                # Geralmente kWh ou Wh - sem unidade garantida; armazenamos bruto
                try:
                    metrics["energy_wh"] = float(val)
                except Exception:
                    pass

        return metrics

    def get_parsed_metrics(self) -> Dict[str, Any]:
        status = self.get_device_status()
        return self.parse_metrics(status)

    # ---------------- Comandos (ligar/desligar etc.) ---------------- #
    def send_command(self, device_id: str, code: str, value: Any) -> Dict[str, Any]:
        """Envia um comando para o device (ex: switch_1 on/off).

        Args:
            device_id: ID do dispositivo Tuya
            code: Código da função (ex: 'switch_1')
            value: Valor boolean/int/string conforme função
        """
        try:
            payload = {"commands": [{"code": code, "value": value}]}
            resp = self.api.post(f"/v1.0/devices/{device_id}/commands", payload)
            return resp or {}
        except Exception as e:
            logger.error(f"Erro ao enviar comando para {device_id}: {e}")
            return {"error": str(e)}


if __name__ == "__main__":
    # Teste rápido manual (não chamar em produção)
    try:
        client = TuyaClient()
        print(client.simple_snapshot())
    except Exception as e:
        print({"error": str(e)})
