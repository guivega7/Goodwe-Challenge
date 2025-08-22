import requests

IFTTT_KEY = 'SUA_KEY_DO_IFTTT'  # coloque sua chave aqui

def dispara_alerta(evento, mensagem):
    url = f'https://maker.ifttt.com/trigger/{evento}/with/key/{IFTTT_KEY}'
    data = {"value1": mensagem}
    requests.post(url, json=data)

def calcular_custo(consumo_kwh, tarifa=0.95):
    """Calcula o custo em reais do consumo de energia."""
    return round(consumo_kwh * tarifa, 2)

def gerar_relatorio(consumo, geracao, tarifa=0.95):
    custo = calcular_custo(consumo, tarifa)
    saldo = geracao - consumo
    return {
        "consumo": consumo,
        "geracao": geracao,
        "saldo": saldo,
        "custo": custo
    }

def sugerir_desligamento(energia_disponivel, aparelhos):
    """
    Sugere quais aparelhos desligar baseado na prioridade e energia disponível
    """
    consumo_total = sum(a.consumo for a in aparelhos if a.status)
    if consumo_total <= energia_disponivel:
        return []
    
    # Ordena aparelhos por prioridade (maior número = menor prioridade)
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
    
def dispara_alerta_economia(evento, consumo, limite):
    """Dispara alerta inteligente de economia"""
    percentual = (consumo / limite - 1) * 100
    
    mensagem = (
        f"Alerta de consumo elevado! "
        f"Consumo atual: {consumo:.1f}kWh "
        f"({percentual:.0f}% acima do ideal). "
        "Sugerimos desligar aparelhos não essenciais."
    )
    
    dispara_alerta(evento, mensagem)