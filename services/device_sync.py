"""Sincronização de dispositivos Tuya com a base local de Aparelhos.

Cria ou atualiza registros na tabela `aparelhos` a partir dos devices
retornados pela API Tuya. Usa heurísticas simples para categoria e
normalização de potência.
"""
from __future__ import annotations
from datetime import datetime
import logging

from extensions import db
from models.aparelho import Aparelho
from services.tuya_client import TuyaClient

logger = logging.getLogger(__name__)

def sync_tuya_devices(usuario_id: int | None = None, force_device_id: str | None = None) -> dict:
    """Sincroniza dispositivos Tuya.

    Se `usuario_id` for fornecido, associa os aparelhos ao usuário informado;
    caso contrário, tenta usar 1 como padrão (ajustar conforme regras de negócio).

    Returns:
        dict: Estatísticas de sincronização
    """
    try:
        client = TuyaClient()
        resp = client.get_device_list()
        result = resp.get("result") if isinstance(resp, dict) else None
        devices = None
        if isinstance(result, dict):
            # Alguns retornos podem ter diretamente a lista, ou dentro de 'devices'
            if isinstance(result.get("devices"), list):
                devices = result.get("devices")
            elif isinstance(result.get("list"), list):  # fallback possível
                devices = result.get("list")
        elif isinstance(result, list):
            devices = result

        # Força dispositivo específico caso pedido
        chosen_id = force_device_id or client.device_id
        if not devices and chosen_id:
            logger.info(f"[DeviceSync] Fallback forçado usando device_id={chosen_id}")
            status_resp = client.get_device_status_by_id(chosen_id)
            res = status_resp.get("result") or {}
            devices = [{
                "id": chosen_id,
                "name": res.get("name") or f"Device {chosen_id[:6]}",
                "category": res.get("category"),
                "product_name": res.get("product_name") or res.get("name")
            }]

        if not devices:
            logger.info("[DeviceSync] Nenhum dispositivo Tuya retornado (sem fallback aplicável)")
            return {"encontrados": 0, "novos": 0, "atualizados": 0, "force": bool(force_device_id)}

        stats = {"encontrados": 0, "novos": 0, "atualizados": 0}
        uid = usuario_id or 1  # suposição: usuário 1 padrão

        for dev in devices:
            stats["encontrados"] += 1
            dev_id = dev.get("id")
            if not dev_id:
                continue

            nome = dev.get("name") or f"Tuya {dev_id[:6]}"
            categoria = "Tomada"
            product_name = (dev.get("product_name") or "").lower()
            cat_code = dev.get("category")
            if "switch" in product_name:
                categoria = "Interruptor"
            elif "light" in product_name or cat_code == "dj":
                categoria = "Iluminação"

            # Obter potência atual
            potencia_w = None
            try:
                status_resp = client.get_device_status_by_id(dev_id)
                status_list = status_resp.get("result", {}).get("status", [])
                for item in status_list:
                    if item.get("code") == "cur_power":
                        val = item.get("value")
                        if isinstance(val, (int, float)):
                            potencia_w = float(val) / 10.0 if val > 200 else float(val)
                        break
            except Exception as e:
                logger.error(f"[DeviceSync] Erro lendo status {dev_id}: {e}")

            # Primeiro procura por codigo_externo (idempotência)
            aparelho = Aparelho.query.filter_by(codigo_externo=dev_id, usuario_id=uid).first()
            if not aparelho:
                # Fallback legado (antes de termos codigo_externo): busca por nome
                aparelho = Aparelho.query.filter_by(nome=nome, usuario_id=uid).first()
            if not aparelho:
                # O modelo atual usa campos: nome, consumo (kWh), prioridade, status, usuario_id
                # Vamos mapear potencia instantânea aproximada para consumo diário estimado inicial
                consumo_kwh_estimado = round(((potencia_w or 50) * 4) / 1000.0, 3)  # suposição: 4h/dia
                aparelho = Aparelho(
                    nome=nome,
                    consumo=consumo_kwh_estimado,
                    prioridade=3,
                    usuario_id=uid,
                    codigo_externo=dev_id,
                    origem='tuya'
                )
                db.session.add(aparelho)
                stats["novos"] += 1
            else:
                # Atualiza consumo estimado se potência nova válida
                if potencia_w:
                    aparelho.consumo = round(((potencia_w) * 4) / 1000.0, 3)
                # Garante que campos novos sejam preenchidos se ainda faltarem
                if not aparelho.codigo_externo:
                    aparelho.codigo_externo = dev_id
                if not aparelho.origem:
                    aparelho.origem = 'tuya'
                stats["atualizados"] += 1

        db.session.commit()
        logger.info(f"[DeviceSync] Concluído: {stats}")
        return stats
    except Exception as e:
        logger.error(f"[DeviceSync] Falha: {e}")
        db.session.rollback()
        return {"error": str(e)}
