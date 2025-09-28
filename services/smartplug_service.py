"""Serviço de coleta e persistência da Smart Plug (Tuya)."""
from __future__ import annotations
import traceback
from datetime import datetime
from typing import Optional

from extensions import db
from services.tuya_client import TuyaClient
from models.smartplug_reading import SmartPlugReading
from utils.logger import get_logger

logger = get_logger(__name__)

def collect_and_store(device_id: Optional[str] = None) -> Optional[int]:
    """Coleta snapshot atual da smart plug e salva no banco.

    Returns:
        ID do registro criado ou None em caso de falha.
    """
    try:
        client = TuyaClient(device_id=device_id)
        status = client.get_device_status()
        metrics = client.parse_metrics(status)

        reading = SmartPlugReading(
            device_id=client.device_id or device_id or "unknown",
            power_w=metrics.get("power_w"),
            voltage_v=metrics.get("voltage_v"),
            current_a=metrics.get("current_a"),
            energy_wh=metrics.get("energy_wh"),
            raw_status=status.get("result")
        )
        db.session.add(reading)
        db.session.commit()
        logger.info(f"[SmartPlug] Leitura armazenada id={reading.id} device={reading.device_id} power={reading.power_w}")
        return reading.id
    except Exception as e:
        logger.error(f"[SmartPlug] Falha ao coletar: {e}\n{traceback.format_exc()}")
        db.session.rollback()
        return None

def latest_readings(limit: int = 50):
    q = (SmartPlugReading.query
         .order_by(SmartPlugReading.created_at.desc())
         .limit(limit))
    return [r.to_dict() for r in q]

def summary():
    from sqlalchemy import func
    agg = db.session.query(
        func.count(SmartPlugReading.id),
        func.avg(SmartPlugReading.power_w),
        func.max(SmartPlugReading.power_w),
        func.avg(SmartPlugReading.voltage_v),
        func.avg(SmartPlugReading.current_a),
    ).one()
    return {
        'total_readings': agg[0] or 0,
        'avg_power_w': round(agg[1], 2) if agg[1] is not None else None,
        'max_power_w': round(agg[2], 2) if agg[2] is not None else None,
        'avg_voltage_v': round(agg[3], 2) if agg[3] is not None else None,
        'avg_current_a': round(agg[4], 3) if agg[4] is not None else None,
        'updated_at': datetime.utcnow().isoformat() + 'Z'
    }
