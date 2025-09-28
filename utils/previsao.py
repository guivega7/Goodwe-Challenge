"""
Módulo para buscar dados de previsão do tempo.
"""

import os
import requests
from utils.logger import get_logger

logger = get_logger(__name__)

# É recomendado usar uma API de previsão do tempo como OpenWeatherMap,
# WeatherAPI, etc. A chave da API deve ser guardada no .env
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "http://api.openweathermap.org/data/2.5/forecast"

def obter_previsao_tempo(cidade="Sao Paulo,BR", dias=5):
    """
    Busca a previsão do tempo para os próximos dias.

    Args:
        cidade (str): A cidade para a qual buscar a previsão.
        dias (int): O número de dias de previsão (máx 5 com a API gratuita).

    Returns:
        list: Uma lista de dicionários, cada um representando a previsão para um dia.
              Retorna uma lista vazia se a API falhar ou a chave não for fornecida.
    """
    if not OPENWEATHER_API_KEY:
        logger.warning("OPENWEATHER_API_KEY não definida no .env. Usando dados de exemplo.")
        return _dados_exemplo_previsao()

    params = {
        'q': cidade,
        'appid': OPENWEATHER_API_KEY,
        'units': 'metric',
        'lang': 'pt_br',
        'cnt': dias * 8 # A API retorna dados a cada 3 horas, 8 pontos por dia
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status() # Lança exceção para erros HTTP
        data = response.json()

        previsao_diaria = []
        dias_processados = set()

        for item in data.get('list', []):
            dia = item['dt_txt'].split(' ')[0]
            if dia not in dias_processados:
                previsao_diaria.append({
                    "data": item['dt_txt'],
                    "temperatura": item['main']['temp'],
                    "descricao": item['weather'][0]['description'],
                    "icone": item['weather'][0]['icon']
                })
                dias_processados.add(dia)
        
        # Garante que não retorne mais dias que o solicitado
        return previsao_diaria[:dias]

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao chamar a API de previsão do tempo: {e}")
        return _dados_exemplo_previsao() # Retorna dados de exemplo em caso de falha
    except Exception as e:
        logger.error(f"Erro inesperado ao processar previsão do tempo: {e}")
        return _dados_exemplo_previsao()

def _dados_exemplo_previsao():
    """Retorna uma lista de dados de previsão estáticos para desenvolvimento."""
    return [
        {'data': '2025-09-28 12:00:00', 'temperatura': 25.5, 'descricao': 'céu limpo', 'icone': '01d'},
        {'data': '2025-09-29 12:00:00', 'temperatura': 26.1, 'descricao': 'algumas nuvens', 'icone': '02d'},
        {'data': '2025-09-30 12:00:00', 'temperatura': 24.8, 'descricao': 'chuva leve', 'icone': '10d'},
        {'data': '2025-10-01 12:00:00', 'temperatura': 27.0, 'descricao': 'ensolarado', 'icone': '01d'},
        {'data': '2025-10-02 12:00:00', 'temperatura': 23.9, 'descricao': 'nuvens dispersas', 'icone': '03d'},
    ]

def obter_icone_url(codigo_icone):
    """Retorna a URL completa para um ícone de tempo do OpenWeatherMap."""
    return f"http://openweathermap.org/img/wn/{codigo_icone}@2x.png"