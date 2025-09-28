"""Modelo de leituras da tomada inteligente (Tuya).

Armazena snapshots periódicos do estado elétrico para análise histórica
e correlação com a geração solar.
"""
from datetime import datetime
from extensions import db

class SmartPlugReading(db.Model):
    __tablename__ = 'smartplug_readings'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(64), index=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True, nullable=False)

    # Métricas elétricas básicas (nem todo device expõe todas)
    power_w = db.Column(db.Float)         # Potência instantânea (W)
    voltage_v = db.Column(db.Float)       # Tensão (V)
    current_a = db.Column(db.Float)       # Corrente (A)
    energy_wh = db.Column(db.Float)       # Energia acumulada (Wh / ou kWh*1000 dependendo do DPS)

    raw_status = db.Column(db.JSON)       # Payload bruto retornado pela API Tuya (status/result)

    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'created_at': self.created_at.isoformat(),
            'power_w': self.power_w,
            'voltage_v': self.voltage_v,
            'current_a': self.current_a,
            'energy_wh': self.energy_wh,
        }

    def __repr__(self):
        return f'<SmartPlugReading {self.device_id} {self.created_at.isoformat()}>'
