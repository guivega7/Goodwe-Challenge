import random

# Esta variável será nossa "fonte única da verdade" para os dados diários
MOCK_STATE = {
    "soc_bateria": 0,
    "geracao_dia": 0,
    "economia_dia": 0,
}

def get_mock_daily_state() -> dict:
    """Retorna o estado diário mockado completo.
    Gera uma vez por processo (soc_bateria, geracao_dia, economia_dia) e mantém estável.
    """
    if MOCK_STATE["soc_bateria"] == 0:
        battery_level = random.randint(60, 95)
        MOCK_STATE["soc_bateria"] = battery_level
        MOCK_STATE["geracao_dia"] = round(battery_level * 0.18, 1)
        MOCK_STATE["economia_dia"] = round(battery_level * 0.09, 2)
        print(f"MOCK DATA STORE: Novos dados diários gerados: {MOCK_STATE}")
    return MOCK_STATE

# Compatibilidade retroativa: mantém a função antiga
def get_mock_battery_level() -> int:
    return get_mock_daily_state()["soc_bateria"]
