from models.aparelho import Aparelho
from utils.energia import dispara_alerta
import datetime

class AutomacaoEnergia:
    def __init__(self):
        self.HORARIO_PICO = {
            'inicio': datetime.time(17, 30),
            'fim': datetime.time(20, 30)
        }
        self.META_DIARIA = 30.0  # kWh

    def verificar_horario_pico(self):
        """Verifica se estamos no horário de pico"""
        agora = datetime.datetime.now().time()
        return self.HORARIO_PICO['inicio'] <= agora <= self.HORARIO_PICO['fim']

    def sugerir_desligamentos(self, aparelhos, consumo_atual):
        """Sugere aparelhos para desligar baseado no consumo e horário"""
        sugestoes = []
        
        # Horário de pico = mais rigoroso
        if self.verificar_horario_pico():
            limite = self.META_DIARIA * 0.7
        else:
            limite = self.META_DIARIA

        if consumo_atual > limite:
            aparelhos_ordenados = sorted(
                aparelhos, 
                key=lambda x: (x.prioridade, -x.consumo)
            )
            
            for ap in aparelhos_ordenados:
                if ap.status and ap.prioridade > 2:  # Não sugere desligar prioridades altas
                    sugestoes.append({
                        'aparelho': ap.nome,
                        'economia_potencial': ap.consumo,
                        'prioridade': ap.prioridade
                    })
                    
                    if sum(s['economia_potencial'] for s in sugestoes) >= (consumo_atual - limite):
                        break

        return sugestoes

    def gerar_relatorio_economia(self, consumo_historico):
        """Gera relatório de economia com sugestões personalizadas"""
        media_consumo = sum(consumo_historico) / len(consumo_historico)
        pico_consumo = max(consumo_historico)
        
        return {
            'media_diaria': media_consumo,
            'pico_consumo': pico_consumo,
            'sugestoes': [
                "Desligue aparelhos em standby no horário de pico",
                "Configure timers para desligamento automático",
                f"Tente manter o consumo abaixo de {self.META_DIARIA}kWh/dia",
                "Priorize o uso de aparelhos fora do horário de pico"
            ]
        }