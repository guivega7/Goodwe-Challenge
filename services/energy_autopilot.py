"""
Energy Autopilot - Plano do Dia Inteligente

Gera recomendações operacionais a partir de:
- SoC (estado de carga da bateria)
- Janela de tarifa/pico (configurável via .env)
- Previsão de geração (kWh estimados para o dia)
- Horário atual e condições dinâmicas

Retorna um plano com janela de pico, cargas a reduzir e uma mensagem curta
amigável para a Alexa/IFTTT.
"""

from __future__ import annotations

import os
import random
from datetime import time, datetime
from typing import Dict, List
from flask import session


def _parse_time(hhmm: str | None, default: str) -> time:
    try:
        raw = (hhmm or default).strip()
        hh, mm = raw.split(":", 1)
        return time(int(hh), int(mm))
    except Exception:
        dh, dm = default.split(":", 1)
        return time(int(dh), int(dm))


def _get_dynamic_recommendations(current_soc: float, forecast_kwh: float, current_hour: int) -> List[str]:
    """Gera recomendações dinâmicas baseadas no horário e condições atuais."""
    recs = []
    
    # Recomendações baseadas no horário
    if 6 <= current_hour <= 8:  # Manhã
        recs.append("Aproveite o início da geração solar para usar eletrodomésticos")
        if current_soc < 50:
            recs.append("Evite cargas pesadas até a bateria carregar mais")
    elif 10 <= current_hour <= 15:  # Pico solar
        recs.append("Horário ideal para usar ar condicionado e aquecedor")
        recs.append("Bateria sendo carregada pela energia solar gratuita")
        if forecast_kwh > 15:
            recs.append("Geração alta prevista - use aparelhos pesados agora!")
    elif 16 <= current_hour <= 17:  # Fim do pico solar
        recs.append("Últimas horas de boa geração - finalize tarefas energéticas")
        if current_soc > 80:
            recs.append("Bateria cheia - momento ideal para lavar/secar roupas")
    elif 18 <= current_hour <= 21:  # Pico tarifário
        recs.append("EVITE aparelhos pesados - energia mais cara da rede")
        recs.append("Use energia armazenada na bateria")
        if current_soc < 30:
            recs.append("⚠️ Bateria baixa - reduza consumo ao mínimo")
    else:  # Noite/madrugada
        recs.append("Mantenha apenas cargas essenciais ligadas")
        recs.append("Prepare sistema para novo ciclo solar amanhã")
    
    # Recomendações baseadas no SoC
    if current_soc > 90:
        recs.append("🔋 Bateria cheia - use toda energia que precisar!")
    elif current_soc > 70:
        recs.append("✅ Bateria com boa carga - sistema funcionando bem")
    elif current_soc > 50:
        recs.append("🟡 Bateria moderada - prefira horários de sol")
    elif current_soc > 30:
        recs.append("🟠 Atenção - gerencie consumo com cuidado")
    else:
        recs.append("🔴 Bateria baixa - URGENTE reduzir consumo")
    
    # Recomendações baseadas na previsão
    if forecast_kwh > 20:
        recs.append("☀️ Dia ensolarado previsto - aproveite a energia gratuita!")
    elif forecast_kwh > 10:
        recs.append("⛅ Dia normal - planeje uso para horários de sol")
    else:
        recs.append("☁️ Pouca geração prevista - economize energia hoje")
    
    return recs


def _get_dynamic_shed_devices(current_soc: float, current_hour: int) -> List[str]:
    """Retorna lista dinâmica de dispositivos para reduzir baseado nas condições."""
    devices = []
    
    # Busca aparelhos reais do usuário logado
    user_devices = []
    try:
        from models.aparelho import Aparelho
        
        if 'usuario_id' in session:
            user_aparelhos = Aparelho.query.filter_by(usuario_id=session['usuario_id']).all()
            user_devices = [aparelho.nome for aparelho in user_aparelhos]
    except Exception:
        # Fallback se houver erro ou usuário não logado
        pass
    
    # Lista de fallback caso usuário não tenha aparelhos cadastrados
    fallback_devices = [
        "Ar Condicionado", "Aquecedor Elétrico", "Chuveiro Elétrico",
        "Micro-ondas", "Máquina de Lavar", "Secadora", "Ferro de Passar",
        "Aspirador de Pó", "Cafeteira", "Torradeira", "Liquidificador"
    ]
    
    # Usa aparelhos do usuário se disponíveis, senão usa fallback
    available_devices = user_devices if user_devices else fallback_devices
    
    # Critérios dinâmicos para shed
    if current_soc < 20:  # Bateria crítica
        devices = random.sample(available_devices, min(4, len(available_devices)))
    elif current_soc < 40:  # Bateria baixa
        devices = random.sample(available_devices, min(3, len(available_devices)))
    elif 18 <= current_hour <= 21:  # Horário de pico
        devices = random.sample(available_devices, min(2, len(available_devices)))
    else:
        # Situação normal - poucos ou nenhum device para shed
        if random.random() < 0.3:  # 30% chance de sugerir economia
            devices = [random.choice(available_devices)]
    
    return devices


def build_daily_plan(current_soc: float, forecast_kwh: float) -> Dict:
    """
    Constrói o plano do dia considerando SoC, janela de pico, previsão solar e hora atual.

    Args:
        current_soc: Estado de carga da bateria (0-100)
        forecast_kwh: Geração prevista no dia (kWh)

    Returns:
        dict com dados do plano (janela de pico, recomendações, shed e mensagem Alexa)
    """
    now = datetime.now()
    current_hour = now.hour
    
    peak_start = _parse_time(os.getenv("TARIFF_PEAK_START", "18:00"), "18:00")
    peak_end = _parse_time(os.getenv("TARIFF_PEAK_END", "21:59"), "21:59")
    soc_min = float(os.getenv("SOC_MIN_SAFETY", "20"))

    # Gera recomendações dinâmicas baseadas no contexto atual
    recommendations = _get_dynamic_recommendations(current_soc, forecast_kwh, current_hour)
    
    # Seleciona amostra aleatória para variar a cada carregamento
    final_recommendations = random.sample(recommendations, min(4, len(recommendations)))
    
    # Gera lista dinâmica de dispositivos para shed
    shed_list = _get_dynamic_shed_devices(current_soc, current_hour)

    # Adiciona variação pequena aos valores para simular dinamismo
    soc_display = current_soc + random.uniform(-0.5, 0.5)
    soc_display = max(0, min(100, soc_display))  # Garante range 0-100
    
    forecast_display = forecast_kwh + random.uniform(-0.3, 0.3)
    forecast_display = max(0, forecast_display)  # Não pode ser negativo

    # Mensagem dinâmica para Alexa baseada no contexto
    status_msg = ""
    if current_soc > 80:
        status_msg = "Sistema com ótima carga"
    elif current_soc > 50:
        status_msg = "Sistema funcionando bem"
    elif current_soc > 30:
        status_msg = "Atenção ao consumo"
    else:
        status_msg = "Economia necessária"
    
    time_context = ""
    if 6 <= current_hour <= 10:
        time_context = "Aproveite a manhã solar"
    elif 11 <= current_hour <= 15:
        time_context = "Pico solar - use aparelhos pesados"
    elif 16 <= current_hour <= 17:
        time_context = "Últimas horas de boa geração"
    elif 18 <= current_hour <= 21:
        time_context = "Horário caro - evite consumo alto"
    else:
        time_context = "Período noturno - economia recomendada"

    alexa_message = f"{status_msg}. {time_context}. Bateria em {current_soc:.0f}% e previsão de {forecast_kwh:.1f} kWh hoje."

    return {
        "soc": round(soc_display, 1),
        "forecast_kwh": round(forecast_display, 1),
        "peak_window": {
            "start": peak_start.strftime("%H:%M"),
            "end": peak_end.strftime("%H:%M")
        },
        "recommendations": final_recommendations,
        "shed": shed_list,
        "alexa_message": alexa_message,
        "generated_at": now.isoformat(),
        "context": {
            "current_hour": current_hour,
            "is_peak_time": peak_start.hour <= current_hour <= peak_end.hour,
            "soc_status": status_msg,
            "time_context": time_context
        }
    }

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
