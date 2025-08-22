import requests
import random
import datetime

IFTTT_KEY = 'cAReVh3CAb4asODHvjEZLm'  # Coloque sua chave aqui

def dispara_alerta(evento, mensagem):
    url = f'https://maker.ifttt.com/trigger/{evento}/with/key/{IFTTT_KEY}'
    data = {"value1": mensagem}
    response = requests.post(url, json=data)
    print(f'Evento: {evento} | Status:', response.status_code)
    print('Resposta:', response.text)

if __name__ == "__main__":
    # Evento: low_battery
    dispara_alerta('low_battery', "Atenção: a bateria está abaixo de 20%!")

    # Evento: Resumo_Diario
    geracao = round(random.uniform(25, 35), 1)
    consumo = round(random.uniform(20, 30), 1)
    mensagem_resumo = f"{geracao} {consumo} "
    dispara_alerta('Resumo_Diario', mensagem_resumo)

    # Evento: inversor
    dispara_alerta('inversor', "Alerta crítico! O inversor solar está com falha. Verifique o sistema ou contate o suporte técnico imediatamente.")

    # Evento: high_energy
    consumo_alto = round(random.uniform(40, 60), 1)
    mensagem_high_energy = f"{consumo_alto}"
    dispara_alerta('high_energy', mensagem_high_energy)

    # Evento: manutencao
    ultima_manutencao = datetime.date(2024, 1, 1)
    hoje = datetime.date.today()
    dias_desde_manutencao = (hoje - ultima_manutencao).days
    mensagem_manutencao = f"{dias_desde_manutencao}"
    dispara_alerta('manutencao', mensagem_manutencao)
