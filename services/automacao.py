"""
Energy automation service for smart device control and optimization.

This module provides intelligent energy management through automated
device control, peak hour management, and consumption optimization.
"""

import datetime
from typing import Dict, List, Optional, Tuple
from models.aparelho import Aparelho
from utils.energia import dispara_alerta
from utils.logger import get_logger

logger = get_logger(__name__)


class AutomacaoEnergia:
    """
    Energy automation system for smart home optimization.
    
    Manages device schedules, peak hour detection, and energy consumption
    optimization based on user preferences and energy availability.
    """

    def __init__(self, meta_diaria: float = 30.0):
        """
        Initialize automation system.
        
        Args:
            meta_diaria: Daily energy consumption target in kWh
        """
        self.HORARIO_PICO = {
            'inicio': datetime.time(17, 30),
            'fim': datetime.time(20, 30)
        }
        self.META_DIARIA = meta_diaria
        self.FATOR_PICO = 0.7  # Reduce consumption by 30% during peak hours

    def verificar_horario_pico(self, momento: Optional[datetime.datetime] = None) -> bool:
        """
        Check if current time is within peak hours.
        
        Args:
            momento: Specific datetime to check (default: current time)
            
        Returns:
            bool: True if within peak hours
        """
        if momento is None:
            momento = datetime.datetime.now()
            
        hora_atual = momento.time()
        return self.HORARIO_PICO['inicio'] <= hora_atual <= self.HORARIO_PICO['fim']

    def calcular_limite_consumo(self, momento: Optional[datetime.datetime] = None) -> float:
        """
        Calculate consumption limit based on time of day.
        
        Args:
            momento: Specific datetime to check
            
        Returns:
            float: Consumption limit in kWh
        """
        if self.verificar_horario_pico(momento):
            return self.META_DIARIA * self.FATOR_PICO
        return self.META_DIARIA

    def sugerir_desligamentos(self, aparelhos: List[Aparelho], consumo_atual: float) -> List[Dict]:
        """
        Suggest devices to turn off based on consumption and time.
        
        Args:
            aparelhos: List of device objects
            consumo_atual: Current energy consumption in kWh
            
        Returns:
            list: Suggested devices for shutdown with potential savings
        """
        limite = self.calcular_limite_consumo()
        
        if consumo_atual <= limite:
            return []

        aparelhos_ligados = [ap for ap in aparelhos if ap.status]
        aparelhos_ordenados = sorted(
            aparelhos_ligados, 
            key=lambda x: (x.prioridade, -x.consumo)
        )
        
        sugestoes = []
        economia_acumulada = 0
        excesso = consumo_atual - limite
        
        for aparelho in aparelhos_ordenados:
            if aparelho.prioridade > 2:  # Skip high priority devices
                economia_potencial = aparelho.consumo
                sugestoes.append({
                    'aparelho_id': aparelho.id,
                    'aparelho': aparelho.nome,
                    'economia_potencial': economia_potencial,
                    'prioridade': aparelho.prioridade,
                    'categoria': self._categorizar_prioridade(aparelho.prioridade)
                })
                
                economia_acumulada += economia_potencial
                
                if economia_acumulada >= excesso:
                    break

        logger.info(f"Sugeridos {len(sugestoes)} aparelhos para desligamento")
        return sugestoes

    def _categorizar_prioridade(self, prioridade: int) -> str:
        """
        Categorize device priority level.
        
        Args:
            prioridade: Priority level (1-5)
            
        Returns:
            str: Priority category description
        """
        categorias = {
            1: 'Crítica',
            2: 'Alta', 
            3: 'Média',
            4: 'Baixa',
            5: 'Opcional'
        }
        return categorias.get(prioridade, 'Indefinida')

    def gerar_relatorio_economia(self, consumo_historico: List[float]) -> Dict:
        """
        Generate economy report with personalized suggestions.
        
        Args:
            consumo_historico: Historical consumption data
            
        Returns:
            dict: Economy report with statistics and suggestions
        """
        if not consumo_historico:
            return self._relatorio_vazio()

        media_consumo = sum(consumo_historico) / len(consumo_historico)
        pico_consumo = max(consumo_historico)
        consumo_minimo = min(consumo_historico)
        variacao = pico_consumo - consumo_minimo
        
        # Calculate efficiency metrics
        dias_acima_meta = len([c for c in consumo_historico if c > self.META_DIARIA])
        eficiencia = ((len(consumo_historico) - dias_acima_meta) / len(consumo_historico)) * 100
        
        sugestoes = self._gerar_sugestoes_personalizadas(media_consumo, eficiencia)
        
        return {
            'periodo_analisado': len(consumo_historico),
            'media_diaria': round(media_consumo, 2),
            'pico_consumo': round(pico_consumo, 2),
            'consumo_minimo': round(consumo_minimo, 2),
            'variacao_consumo': round(variacao, 2),
            'meta_diaria': self.META_DIARIA,
            'dias_acima_meta': dias_acima_meta,
            'eficiencia_percentual': round(eficiencia, 1),
            'sugestoes': sugestoes,
            'economia_potencial': self._calcular_economia_potencial(media_consumo)
        }

    def _gerar_sugestoes_personalizadas(self, media_consumo: float, eficiencia: float) -> List[str]:
        """
        Generate personalized suggestions based on consumption patterns.
        
        Args:
            media_consumo: Average daily consumption
            eficiencia: Efficiency percentage
            
        Returns:
            list: Personalized suggestions
        """
        sugestoes = []
        
        if media_consumo > self.META_DIARIA:
            sugestoes.append(f"Reduza o consumo médio de {media_consumo:.1f} para {self.META_DIARIA}kWh/dia")
            
        if eficiencia < 70:
            sugestoes.extend([
                "Configure timers para desligamento automático",
                "Evite deixar aparelhos em standby",
                "Concentre o uso de aparelhos fora do horário de pico"
            ])
        elif eficiencia < 85:
            sugestoes.extend([
                "Otimize o uso durante horário de pico",
                "Monitore aparelhos de alto consumo"
            ])
        else:
            sugestoes.append("Parabéns! Seu consumo está otimizado")
            
        sugestoes.extend([
            f"Horário de pico: {self.HORARIO_PICO['inicio']} às {self.HORARIO_PICO['fim']}",
            "Priorize energia solar durante o dia"
        ])
        
        return sugestoes

    def _calcular_economia_potencial(self, media_consumo: float, tarifa: float = 0.95) -> Dict:
        """
        Calculate potential energy savings.
        
        Args:
            media_consumo: Average consumption
            tarifa: Energy rate per kWh
            
        Returns:
            dict: Potential savings information
        """
        if media_consumo <= self.META_DIARIA:
            return {'economia_kwh': 0, 'economia_reais': 0}
            
        economia_kwh = media_consumo - self.META_DIARIA
        economia_mensal = economia_kwh * 30 * tarifa
        economia_anual = economia_mensal * 12
        
        return {
            'economia_kwh_dia': round(economia_kwh, 2),
            'economia_mensal': round(economia_mensal, 2),
            'economia_anual': round(economia_anual, 2)
        }

    def _relatorio_vazio(self) -> Dict:
        """Return empty report structure."""
        return {
            'periodo_analisado': 0,
            'media_diaria': 0,
            'pico_consumo': 0,
            'consumo_minimo': 0,
            'variacao_consumo': 0,
            'meta_diaria': self.META_DIARIA,
            'dias_acima_meta': 0,
            'eficiencia_percentual': 0,
            'sugestoes': ['Dados insuficientes para análise'],
            'economia_potencial': {'economia_kwh': 0, 'economia_reais': 0}
        }

    def executar_automacao_inteligente(self, aparelhos: List[Aparelho], energia_disponivel: float) -> Dict:
        """
        Execute intelligent automation based on available energy.
        
        Args:
            aparelhos: List of devices
            energia_disponivel: Available energy in kWh
            
        Returns:
            dict: Automation execution results
        """
        acoes_executadas = []
        energia_economizada = 0
        
        if self.verificar_horario_pico():
            # More aggressive during peak hours
            limite = energia_disponivel * 0.8
        else:
            limite = energia_disponivel
            
        consumo_atual = sum(ap.consumo for ap in aparelhos if ap.status)
        
        if consumo_atual > limite:
            desligamentos = self.sugerir_desligamentos(aparelhos, consumo_atual)
            for sugestao in desligamentos:
                aparelho_id = sugestao['aparelho_id']
                aparelho = next((ap for ap in aparelhos if ap.id == aparelho_id), None)
                
                if aparelho and aparelho.status:
                    # Here would implement actual device control
                    acoes_executadas.append(f"Desligado: {aparelho.nome}")
                    energia_economizada += aparelho.consumo
                    
                    # Send alert
                    dispara_alerta(
                        "automacao_desligamento",
                        f"Aparelho {aparelho.nome} foi desligado automaticamente para economia de energia"
                    )
        
        return {
            'acoes_executadas': acoes_executadas,
            'energia_economizada': round(energia_economizada, 2),
            'horario_pico': self.verificar_horario_pico(),
            'limite_aplicado': round(limite, 2)
        }