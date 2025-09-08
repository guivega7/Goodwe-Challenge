"""
Event simulation service for development and testing.

This module provides mock data generation for solar energy systems
and simulated alert dispatching for development purposes.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from utils.logger import get_logger

logger = get_logger(__name__)


class EventSimulator:
    """
    Event simulator for solar energy system development.
    
    Provides realistic mock data for energy generation, consumption,
    battery status, and weather conditions.
    """
    
    def __init__(self):
        """Initialize event simulator with realistic parameters."""
        self.system_capacity = 5.0  # kW
        self.battery_capacity = 13.5  # kWh
        self.base_consumption = 1.5  # kW baseline consumption
        
    def get_mock_solar_data(self, timestamp: Optional[datetime] = None) -> Dict[str, Union[float, str]]:
        """
        Generate realistic solar system data.
        
        Args:
            timestamp: Specific timestamp for data generation
            
        Returns:
            dict: Mock solar system data
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        hour = timestamp.hour
        minute = timestamp.minute
        
        # Solar generation pattern based on time of day
        if 6 <= hour <= 18:
            # Daylight hours with realistic solar curve
            solar_factor = self._calculate_solar_factor(hour, minute)
            weather_factor = random.uniform(0.7, 1.0)  # Weather variability
            geracao = round(self.system_capacity * solar_factor * weather_factor, 2)
        else:
            geracao = 0.0
            
        # Consumption varies throughout the day
        consumption_factor = self._calculate_consumption_factor(hour)
        consumo = round(self.base_consumption * consumption_factor, 2)
        
        # Daily energy accumulation
        if hour < 6:
            energia_hoje = round(random.uniform(0.1, 2.0), 2)
        else:
            energia_hoje = round(random.uniform(5.0, 30.0), 2)
            
        # Battery SOC with realistic patterns
        soc = self._calculate_battery_soc(hour, geracao, consumo)
        
        return {
            "geracao": geracao,
            "consumo": consumo,
            "energia_hoje": energia_hoje,
            "soc": soc,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "potencia_liquida": round(geracao - consumo, 2),
            "status_sistema": self._get_system_status(geracao, consumo, soc)
        }
    
    def _calculate_solar_factor(self, hour: int, minute: int) -> float:
        """
        Calculate solar generation factor based on time.
        
        Args:
            hour: Hour of day (0-23)
            minute: Minute of hour (0-59)
            
        Returns:
            float: Solar generation factor (0-1)
        """
        # Convert to decimal hour
        decimal_hour = hour + minute / 60.0
        
        # Solar curve peaks at noon
        if 6 <= decimal_hour <= 18:
            # Sine wave approximation for solar generation
            progress = (decimal_hour - 6) / 12  # 0 to 1 from 6AM to 6PM
            factor = max(0, 1.0 - abs(0.5 - progress) * 2)  # Peak at 0.5 (noon)
            return factor * 0.95  # Maximum 95% of capacity
        return 0.0
    
    def _calculate_consumption_factor(self, hour: int) -> float:
        """
        Calculate consumption factor based on typical daily patterns.
        
        Args:
            hour: Hour of day (0-23)
            
        Returns:
            float: Consumption multiplier
        """
        # Typical residential consumption pattern
        if 0 <= hour < 6:  # Night - low consumption
            return random.uniform(0.6, 0.8)
        elif 6 <= hour < 9:  # Morning peak
            return random.uniform(1.2, 1.8)
        elif 9 <= hour < 17:  # Day - moderate consumption
            return random.uniform(0.8, 1.2)
        elif 17 <= hour < 22:  # Evening peak
            return random.uniform(1.5, 2.2)
        else:  # Late evening
            return random.uniform(0.7, 1.0)
    
    def _calculate_battery_soc(self, hour: int, geracao: float, consumo: float) -> float:
        """
        Calculate realistic battery state of charge.
        
        Args:
            hour: Hour of day
            geracao: Current generation
            consumo: Current consumption
            
        Returns:
            float: Battery SOC percentage
        """
        # Base SOC with daily cycle
        if 0 <= hour < 6:  # Night discharge
            base_soc = random.uniform(40, 70)
        elif 6 <= hour < 12:  # Morning charge
            base_soc = random.uniform(60, 85)
        elif 12 <= hour < 18:  # Afternoon full charge
            base_soc = random.uniform(80, 100)
        else:  # Evening discharge
            base_soc = random.uniform(50, 80)
            
        # Adjust based on current generation vs consumption
        net_power = geracao - consumo
        if net_power > 0:  # Charging
            base_soc = min(100, base_soc + random.uniform(0, 5))
        elif net_power < -1:  # Heavy discharge
            base_soc = max(20, base_soc - random.uniform(0, 10))
            
        return round(base_soc, 1)
    
    def _get_system_status(self, geracao: float, consumo: float, soc: float) -> str:
        """
        Determine system status based on current conditions.
        
        Args:
            geracao: Current generation
            consumo: Current consumption
            soc: Battery SOC
            
        Returns:
            str: System status description
        """
        net_power = geracao - consumo
        
        if soc < 20:
            return "Bateria Baixa"
        elif net_power > 1:
            return "Carregando"
        elif net_power < -1:
            return "Descarregando"
        elif geracao > 0:
            return "Gerando"
        else:
            return "Standby"

    def get_historical_data(self, days: int = 7) -> List[Dict]:
        """
        Generate historical data for the specified number of days.
        
        Args:
            days: Number of days to generate data for
            
        Returns:
            list: Historical data points
        """
        historical_data = []
        end_date = datetime.now()
        
        for day in range(days):
            date = end_date - timedelta(days=day)
            
            # Generate data points throughout the day
            for hour in range(0, 24, 2):  # Every 2 hours
                timestamp = date.replace(hour=hour, minute=0, second=0, microsecond=0)
                data_point = self.get_mock_solar_data(timestamp)
                historical_data.append(data_point)
                
        return sorted(historical_data, key=lambda x: x['timestamp'])

    def simulate_weather_event(self, event_type: str) -> Dict[str, Union[float, str]]:
        """
        Simulate specific weather events affecting solar generation.
        
        Args:
            event_type: Type of weather event (sunny, cloudy, rainy, storm)
            
        Returns:
            dict: Modified solar data for weather event
        """
        base_data = self.get_mock_solar_data()
        
        weather_impacts = {
            'sunny': {'factor': 1.0, 'variability': 0.05},
            'cloudy': {'factor': 0.6, 'variability': 0.2},
            'rainy': {'factor': 0.3, 'variability': 0.15},
            'storm': {'factor': 0.1, 'variability': 0.1}
        }
        
        impact = weather_impacts.get(event_type, weather_impacts['sunny'])
        factor = impact['factor'] + random.uniform(-impact['variability'], impact['variability'])
        factor = max(0, min(1, factor))  # Clamp between 0 and 1
        
        base_data['geracao'] = round(base_data['geracao'] * factor, 2)
        base_data['evento_clima'] = event_type
        base_data['fator_clima'] = round(factor, 2)
        
        return base_data


def dispara_alerta_mock(evento: str, mensagem: str) -> Dict[str, Union[bool, Dict]]:
    """
    Mock alert dispatcher for development and testing.
    
    Args:
        evento: Event name/type
        mensagem: Alert message
        
    Returns:
        dict: Mock response indicating success
    """
    payload = {
        "evento": evento,
        "mensagem": mensagem,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mock": True
    }
    
    logger.info(f"Mock alert dispatched: {evento} - {mensagem}")
    
    return {
        "ok": True, 
        "payload": payload,
        "status": "mock_success"
    }


def get_mock_event() -> Dict[str, Union[float, str]]:
    """
    Legacy function for backward compatibility.
    
    Returns:
        dict: Mock event data
    """
    simulator = EventSimulator()
    return simulator.get_mock_solar_data()


# Legacy function alias for backward compatibility
dispara_alerta = dispara_alerta_mock