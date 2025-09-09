"""
Energy Autopilot - Plano do Dia Inteligente

Gera recomendações operacionais a partir de:
- SoC (estado de carga da bateria)
- Janela de tarifa/pico (configurável via .env)
- Previsão de geração (kWh estimados para o dia)

Retorna um plano com janela de pico, cargas a reduzir e uma mensagem curta
amigável para a Alexa/IFTTT.
"""

from __future__ import annotations

import os
from datetime import time
from typing import Dict, List


def _parse_time(hhmm: str | None, default: str) -> time:
    try:
        raw = (hhmm or default).strip()
        hh, mm = raw.split(":", 1)
        return time(int(hh), int(mm))
    except Exception:
        dh, dm = default.split(":", 1)
        return time(int(dh), int(dm))


def build_daily_plan(current_soc: float, forecast_kwh: float) -> Dict:
    """
    Constrói o plano do dia considerando SoC, janela de pico e previsão solar.

    Args:
        current_soc: Estado de carga da bateria (0-100)
        forecast_kwh: Geração prevista no dia (kWh)

    Returns:
        dict com dados do plano (janela de pico, recomendações, shed e mensagem Alexa)
    """
    peak_start = _parse_time(os.getenv("TARIFF_PEAK_START", "18:00"), "18:00")
    peak_end = _parse_time(os.getenv("TARIFF_PEAK_END", "21:59"), "21:59")
    soc_min = float(os.getenv("SOC_MIN_SAFETY", "20"))
    critical_devices = [
        d.strip() for d in os.getenv("DEVICES_CRITICAL", "").split(",") if d.strip()
    ]

    shed_list: List[str] = []
    recommendations: List[str] = []

    # Regra 1: Se SOC < mínimo de segurança → reduzir cargas críticas
    if current_soc < soc_min:
        shed_list = critical_devices
        recommendations.append(
            f"SoC {current_soc:.0f}% abaixo do mínimo ({soc_min:.0f}%). Cortar cargas críticas até recuperar."
        )
    else:
        recommendations.append(
            f"SoC saudável ({current_soc:.0f}%). Operar cargas fora do pico {peak_start.strftime('%H:%M')}-{peak_end.strftime('%H:%M')}."
        )

    # Regra 2: Usar geração prevista fora do pico
    if forecast_kwh >= 3:
        recommendations.append("Agendar tarefas pesadas para 10:00–16:00 (janela solar).")
    else:
        recommendations.append("Geração prevista baixa. Priorizar apenas cargas essenciais hoje.")

    # Mensagem compacta para Alexa (value1)
    alexa_msg = (
        f"Plano do dia: SoC {current_soc:.0f}%. "
        + ("Cortar cargas críticas agora. " if shed_list else "Operar fora do pico. ")
        + f"Pico {peak_start.strftime('%H:%M')} a {peak_end.strftime('%H:%M')}."
    )

    return {
        "soc": current_soc,
        "forecast_kwh": forecast_kwh,
        "peak_window": {"start": peak_start.strftime("%H:%M"), "end": peak_end.strftime("%H:%M")},
        "shed": shed_list,
        "recommendations": recommendations,
        "alexa_message": alexa_msg,
    }
