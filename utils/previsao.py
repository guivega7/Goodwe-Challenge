"""
Módulo para buscar dados de previsão do tempo usando Open-Meteo API.
"""

import os
import requests
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)

# API Open-Meteo (100% gratuita, sem limites)
BASE_URL = "https://api.open-meteo.com/v1/forecast"

def obter_previsao_tempo(cidade="Sao Paulo,BR", dias=5):
    """
    Busca a previsão do tempo para os próximos dias usando Open-Meteo API.

    Args:
        cidade (str): A cidade para a qual buscar a previsão (usado apenas para coordenadas).
        dias (int): O número de dias de previsão (máx 7 com Open-Meteo).

    Returns:
        list: Uma lista de dicionários, cada um representando a previsão para um dia.
    """
    # Coordenadas aproximadas de São Paulo (pode ser expandido para outras cidades)
    coordenadas = {
        "Sao Paulo,BR": {"lat": -23.5505, "lon": -46.6333},
        # Adicione outras cidades se necessário
    }

    coords = coordenadas.get(cidade, coordenadas["Sao Paulo,BR"])

    params = {
        'latitude': coords['lat'],
        'longitude': coords['lon'],
        'daily': ['temperature_2m_max', 'temperature_2m_min', 'weathercode'],
        'timezone': 'America/Sao_Paulo',
        'forecast_days': min(dias + 1, 7)  # +1 para incluir hoje se necessário
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        previsao_diaria = []
        hoje = datetime.now()

        for i, date_str in enumerate(data.get('daily', {}).get('time', [])):
            data_prev = datetime.strptime(date_str, '%Y-%m-%d')

            # Pula dias passados
            if data_prev.date() < hoje.date():
                continue

            temp_max = data['daily']['temperature_2m_max'][i]
            temp_min = data['daily']['temperature_2m_min'][i]
            weather_code = data['daily']['weathercode'][i]

            # Converte código do tempo para descrição em português
            descricao, icone = _converter_codigo_tempo(weather_code)

            previsao_diaria.append({
                "data": f"{date_str} 12:00:00",
                "temperatura": round((temp_max + temp_min) / 2, 1),  # Temperatura média
                "descricao": descricao,
                "icone": icone
            })

            if len(previsao_diaria) >= dias:
                break

        return previsao_diaria[:dias]

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao chamar a API Open-Meteo: {e}")
        return _dados_exemplo_previsao()
    except Exception as e:
        logger.error(f"Erro inesperado ao processar previsão do tempo: {e}")
        return _dados_exemplo_previsao()

def _converter_codigo_tempo(codigo):
    """
    Converte código de tempo do Open-Meteo para descrição em português e ícone.

    Args:
        codigo (int): Código do tempo do Open-Meteo

    Returns:
        tuple: (descrição, código_do_ícone)
    """
    # Mapeamento baseado na documentação do Open-Meteo
    mapeamento = {
        0: ('céu limpo', '01d'),
        1: ('principalmente limpo', '01d'),
        2: ('parcialmente nublado', '02d'),
        3: ('nublado', '03d'),
        45: ('neblina', '50d'),
        48: ('neblina com geada', '50d'),
        51: ('chuvisco leve', '09d'),
        53: ('chuvisco moderado', '09d'),
        55: ('chuvisco intenso', '09d'),
        56: ('chuvisco congelante leve', '09d'),
        57: ('chuvisco congelante intenso', '09d'),
        61: ('chuva leve', '10d'),
        63: ('chuva moderada', '10d'),
        65: ('chuva forte', '10d'),
        66: ('chuva congelante leve', '10d'),
        67: ('chuva congelante forte', '10d'),
        71: ('neve leve', '13d'),
        73: ('neve moderada', '13d'),
        75: ('neve forte', '13d'),
        77: ('grãos de neve', '13d'),
        80: ('chuva leve', '10d'),
        81: ('chuva moderada', '10d'),
        82: ('chuva forte', '10d'),
        85: ('neve leve', '13d'),
        86: ('neve forte', '13d'),
        95: ('tempestade', '11d'),
        96: ('tempestade com granizo leve', '11d'),
        99: ('tempestade com granizo forte', '11d'),
    }

    return mapeamento.get(codigo, ('desconhecido', '01d'))

def _dados_exemplo_previsao():
    """Retorna uma lista de dados de previsão dinâmicos para desenvolvimento."""
    hoje = datetime.now()
    dados_exemplo = [
        {'data': (hoje + timedelta(days=0)).strftime('%Y-%m-%d 12:00:00'), 'temperatura': 25.5, 'descricao': 'céu limpo', 'icone': '01d'},
        {'data': (hoje + timedelta(days=1)).strftime('%Y-%m-%d 12:00:00'), 'temperatura': 26.1, 'descricao': 'algumas nuvens', 'icone': '02d'},
        {'data': (hoje + timedelta(days=2)).strftime('%Y-%m-%d 12:00:00'), 'temperatura': 24.8, 'descricao': 'chuva leve', 'icone': '10d'},
        {'data': (hoje + timedelta(days=3)).strftime('%Y-%m-%d 12:00:00'), 'temperatura': 27.0, 'descricao': 'ensolarado', 'icone': '01d'},
        {'data': (hoje + timedelta(days=4)).strftime('%Y-%m-%d 12:00:00'), 'temperatura': 23.9, 'descricao': 'nuvens dispersas', 'icone': '03d'},
    ]
    return dados_exemplo

def obter_icone_url(codigo_icone):
    """Retorna a URL completa para um ícone de tempo."""
    # Usando ícones do OpenWeatherMap que são compatíveis com os códigos
    return f"https://openweathermap.org/img/wn/{codigo_icone}@2x.png"