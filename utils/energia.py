"""
Energy management utilities for solar power monitoring and automation.

This module provides functions for energy calculations, device control,
IFTTT alerts, and battery monitoring for solar energy systems.
"""

import os
import requests
import schedule
import time
from datetime import datetime
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv

load_dotenv()

IFTTT_KEY = os.getenv("IFTTT_KEY")
DEFAULT_ENERGY_RATE = 0.95  # R$ per kWh


def dispara_alerta(evento: str, mensagem: str) -> bool:
    """
    Trigger IFTTT alert with custom event and message.
    
    Args:
        evento: IFTTT event name
        mensagem: Alert message content
        
    Returns:
        bool: True if alert sent successfully, False otherwise
    """
    if not IFTTT_KEY:
        return False
        
    try:
        url = f'https://maker.ifttt.com/trigger/{evento}/with/key/{IFTTT_KEY}'
        data = {"value1": mensagem}
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False


def calcular_custo(consumo_kwh: float, tarifa: float = DEFAULT_ENERGY_RATE) -> float:
    """
    Calculate energy cost in Brazilian Reais.
    
    Args:
        consumo_kwh: Energy consumption in kWh
        tarifa: Energy rate per kWh (default: R$ 0.95)
        
    Returns:
        float: Cost in Brazilian Reais
    """
    return round(consumo_kwh * tarifa, 2)


def gerar_relatorio(consumo: float, geracao: float, tarifa: float = DEFAULT_ENERGY_RATE) -> Dict[str, float]:
    """
    Generate comprehensive energy report.
    
    Args:
        consumo: Energy consumption in kWh
        geracao: Energy generation in kWh
        tarifa: Energy rate per kWh
        
    Returns:
        dict: Report with consumption, generation, balance and cost
    """
    custo = calcular_custo(consumo, tarifa)
    saldo = geracao - consumo
    
    return {
        "consumo": round(consumo, 2),
        "geracao": round(geracao, 2),
        "saldo": round(saldo, 2),
        "custo": custo
    }


def sugerir_desligamento(energia_disponivel: float, aparelhos: List) -> List:
    """
    Suggest devices to turn off based on priority and available energy.
    
    Args:
        energia_disponivel: Available energy in kWh
        aparelhos: List of device objects with consumo, status, and prioridade attributes
        
    Returns:
        list: Devices suggested for shutdown
    """
    consumo_total = sum(a.consumo for a in aparelhos if a.status)
    
    if consumo_total <= energia_disponivel:
        return []
    
    aparelhos_ordenados = sorted(
        [a for a in aparelhos if a.status], 
        key=lambda x: (-x.prioridade, x.consumo)
    )
    
    desligar = []
    for aparelho in aparelhos_ordenados:
        if consumo_total > energia_disponivel:
            desligar.append(aparelho)
            consumo_total -= aparelho.consumo
        else:
            break
    
    return desligar


def dispara_alerta_economia(evento: str, consumo: float, limite: float) -> bool:
    """
    Trigger intelligent energy saving alert.
    
    Args:
        evento: IFTTT event name
        consumo: Current energy consumption
        limite: Energy consumption limit
        
    Returns:
        bool: True if alert sent successfully
    """
    if consumo <= limite:
        return False
        
    percentual = (consumo / limite - 1) * 100
    
    mensagem = (
        f"Alerta de consumo elevado! "
        f"Consumo atual: {consumo:.1f}kWh "
        f"({percentual:.0f}% acima do ideal). "
        "Sugerimos desligar aparelhos não essenciais."
    )
    
    return dispara_alerta(evento, mensagem)


def monitorar_bateria(nivel_bateria: float, limite: float = 20.0) -> bool:
    """
    Monitor battery level and trigger low battery alert.
    
    Args:
        nivel_bateria: Current battery level percentage
        limite: Low battery threshold (default: 20%)
        
    Returns:
        bool: True if alert triggered
    """
    if nivel_bateria < limite:
        mensagem = f"Atenção! Nível da bateria está baixo: {nivel_bateria}%"
        return dispara_alerta("low_battery", mensagem)
    return False


def alerta_falha_sistema(descricao: str) -> bool:
    """
    Send system failure alert.
    
    Args:
        descricao: Failure description
        
    Returns:
        bool: True if alert sent successfully
    """
    mensagem = f"Alerta de falha no sistema: {descricao}"
    return dispara_alerta("falha_inversor", mensagem)


def gerar_relatorio_diario(consumo: float, geracao: float, tarifa: float = DEFAULT_ENERGY_RATE) -> bool:
    """
    Generate and send daily energy report via IFTTT.
    
    Args:
        consumo: Daily energy consumption
        geracao: Daily energy generation
        tarifa: Energy rate per kWh
        
    Returns:
        bool: True if report sent successfully
    """
    relatorio = gerar_relatorio(consumo, geracao, tarifa)
    
    mensagem = (
        f"Resumo Diário:\\n"
        f"Consumo: {relatorio['consumo']} kWh\\n"
        f"Geração: {relatorio['geracao']} kWh\\n"
        f"Saldo: {relatorio['saldo']} kWh\\n"
        f"Custo: R$ {relatorio['custo']}"
    )
    
    return dispara_alerta("resumo_diario", mensagem)


def enviar_relatorio_diario() -> bool:
    """
    Send automated daily report.
    
    Returns:
        bool: True if report sent successfully
    """
    return dispara_alerta("Resumo_Diario", "Relatório diário enviado automaticamente.")


def controlar_aparelhos(energia_disponivel: float, aparelhos: List[Dict]) -> List[Dict]:
    """
    Control device states based on available energy.
    
    Args:
        energia_disponivel: Available energy in kWh
        aparelhos: List of device dictionaries
        
    Returns:
        list: Updated device list with new states
    """
    for aparelho in aparelhos:
        consumo = aparelho.get('consumo', 0)
        status = aparelho.get('status', False)
        
        if consumo <= energia_disponivel and not status:
            aparelho['status'] = True
            energia_disponivel -= consumo
        elif status and consumo > energia_disponivel:
            aparelho['status'] = False
            energia_disponivel += consumo
    
    return aparelhos


def inicializar_agendador() -> None:
    """Initialize task scheduler for automated reports."""
    schedule.every().day.at("09:00").do(enviar_relatorio_diario)
    schedule.every().day.at("18:00").do(enviar_relatorio_diario)


def executar_agendador() -> None:
    """Run the task scheduler in a loop."""
    inicializar_agendador()
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    executar_agendador()