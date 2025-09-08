"""
Energy prediction utilities for solar power systems.

This module provides weather-based energy generation predictions
and smart recommendations for optimal energy usage.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .logger import get_logger

logger = get_logger(__name__)


class PrevisaoEnergia:
    """
    Energy prediction class for solar power generation forecasting.
    
    Provides weather-based generation estimates and usage recommendations
    to optimize energy consumption patterns.
    """
    
    def __init__(self, capacidade_sistema: float = 30.0):
        """
        Initialize energy prediction system.
        
        Args:
            capacidade_sistema: Maximum system capacity in kWh on clear day
        """
        self.DIAS_PREVISAO = 5
        self.capacidade_sistema = capacidade_sistema
        self.fatores_clima = {
            'ensolarado': 1.0,
            'sol': 1.0,
            'claro': 0.95,
            'parcialmente nublado': 0.7,
            'nublado': 0.4,
            'muito nublado': 0.3,
            'chuvoso': 0.2,
            'tempestade': 0.1
        }

    def prever_geracao(self, condicao_clima: str) -> float:
        """
        Estimate solar energy generation based on weather conditions.
        
        Args:
            condicao_clima: Weather condition description
            
        Returns:
            float: Estimated energy generation in kWh
        """
        condicao_normalizada = condicao_clima.lower().strip()
        fator = self.fatores_clima.get(condicao_normalizada, 0.5)
        geracao_estimada = self.capacidade_sistema * fator
        
        logger.info(f"Geração estimada para '{condicao_clima}': {geracao_estimada:.2f} kWh")
        return round(geracao_estimada, 2)

    def calcular_previsao_semanal(self, previsoes_clima: Dict[str, str]) -> Dict[str, Dict]:
        """
        Calculate weekly energy generation forecast.
        
        Args:
            previsoes_clima: Dictionary with date as key and weather condition as value
            
        Returns:
            dict: Weekly forecast with generation estimates and efficiency
        """
        previsao_semanal = {}
        
        for data, clima in previsoes_clima.items():
            geracao = self.prever_geracao(clima)
            eficiencia = (geracao / self.capacidade_sistema) * 100
            
            previsao_semanal[data] = {
                'clima': clima,
                'geracao_estimada': geracao,
                'eficiencia_percentual': round(eficiencia, 1),
                'categoria': self._categorizar_geracao(eficiencia)
            }
        
        return previsao_semanal

    def _categorizar_geracao(self, eficiencia: float) -> str:
        """
        Categorize generation efficiency.
        
        Args:
            eficiencia: Efficiency percentage
            
        Returns:
            str: Generation category
        """
        if eficiencia >= 80:
            return 'Excelente'
        elif eficiencia >= 60:
            return 'Boa'
        elif eficiencia >= 40:
            return 'Moderada'
        else:
            return 'Baixa'

    def sugerir_acoes(self, previsoes: Dict[str, Dict]) -> List[Dict]:
        """
        Suggest energy optimization actions based on forecasts.
        
        Args:
            previsoes: Weekly forecast data
            
        Returns:
            list: Action recommendations for each day
        """
        acoes = []
        
        for dia, previsao in previsoes.items():
            geracao_estimada = previsao['geracao_estimada']
            categoria = previsao['categoria']
            
            recomendacoes = self._gerar_recomendacoes(categoria, geracao_estimada)
            
            if recomendacoes:
                acoes.append({
                    'dia': dia,
                    'geracao_estimada': geracao_estimada,
                    'categoria': categoria,
                    'clima': previsao['clima'],
                    'acoes': recomendacoes
                })
        
        return acoes

    def _gerar_recomendacoes(self, categoria: str, geracao: float) -> List[str]:
        """
        Generate specific recommendations based on generation category.
        
        Args:
            categoria: Generation category
            geracao: Estimated generation in kWh
            
        Returns:
            list: List of recommendations
        """
        recomendacoes = []
        
        if categoria == 'Baixa':
            recomendacoes.extend([
                "Evite usar múltiplos aparelhos de alto consumo simultaneamente",
                "Adie lavagem de roupas e uso do ar condicionado",
                "Use timers para desligar aparelhos automaticamente",
                "Considere usar energia da rede elétrica nos horários de pico"
            ])
        elif categoria == 'Moderada':
            recomendacoes.extend([
                "Use aparelhos de alto consumo com moderação",
                "Prefira usar eletrodomésticos durante o dia",
                "Evite uso simultâneo de ar condicionado e aquecedor"
            ])
        elif categoria == 'Boa':
            recomendacoes.extend([
                "Aproveite para usar aparelhos de alto consumo",
                "Carregue dispositivos eletrônicos",
                "É um bom dia para lavagem e secagem"
            ])
        elif categoria == 'Excelente':
            recomendacoes.extend([
                "Dia ideal para máximo uso de energia solar",
                "Use todos os aparelhos necessários",
                "Considere armazenar energia excedente"
            ])
        
        return recomendacoes

    def calcular_economia_projetada(self, previsoes: Dict[str, Dict], tarifa: float = 0.95) -> Dict:
        """
        Calculate projected energy savings.
        
        Args:
            previsoes: Weekly forecast data
            tarifa: Energy rate per kWh
            
        Returns:
            dict: Projected savings information
        """
        total_geracao = sum(p['geracao_estimada'] for p in previsoes.values())
        economia_total = total_geracao * tarifa
        
        dias_baixa_geracao = len([p for p in previsoes.values() if p['categoria'] == 'Baixa'])
        dias_boa_geracao = len([p for p in previsoes.values() if p['categoria'] in ['Boa', 'Excelente']])
        
        return {
            'geracao_total_estimada': round(total_geracao, 2),
            'economia_estimada': round(economia_total, 2),
            'dias_baixa_geracao': dias_baixa_geracao,
            'dias_boa_geracao': dias_boa_geracao,
            'media_diaria': round(total_geracao / len(previsoes), 2) if previsoes else 0
        }