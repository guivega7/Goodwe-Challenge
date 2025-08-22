import requests
from datetime import datetime, timedelta

class PrevisaoEnergia:
    def __init__(self):
        self.DIAS_PREVISAO = 5

    def prever_geracao(self, condicao_clima):
        """Estima geração baseada no clima"""
        base_geracao = 30.0  # kWh em dia limpo
        
        fatores = {
            'ensolarado': 1.0,
            'parcialmente nublado': 0.7,
            'nublado': 0.4,
            'chuvoso': 0.2
        }
        
        return base_geracao * fatores.get(condicao_clima, 0.5)

    def sugerir_acoes(self, previsoes):
        """Sugere ações baseadas nas previsões"""
        acoes = []
        for dia, previsao in previsoes.items():
            geracao_estimada = self.prever_geracao(previsao['clima'])
            
            if geracao_estimada < 20:  # Dia com pouca geração
                acoes.append({
                    'dia': dia,
                    'geracao_estimada': geracao_estimada,
                    'acoes': [
                        "Evite usar múltiplos aparelhos simultaneamente",
                        "Programe lavagem de roupas para outro dia",
                        "Use timers para desligar aparelhos automaticamente"
                    ]
                })
        
        return acoes