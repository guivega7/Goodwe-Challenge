import random
from datetime import datetime

IFTTT_KEY = None  # quando usar IFTTT real, setar via env e atualizar aqui

def get_mock_event():
    """Retorna um dicionário com dados simulados (formato esperado pelo dashboard)."""
    agora = datetime.now()
    geracao = round(random.uniform(0.5, 5.0), 2)
    consumo = round(max(0.0, geracao * random.uniform(0.6, 1.4)), 2)
    energia_hoje = round(random.uniform(5.0, 30.0), 2)
    soc = round(random.uniform(10, 100), 1)
    return {
        "geracao": geracao,
        "consumo": consumo,
        "energia_hoje": energia_hoje,
        "soc": soc,
        "timestamp": agora.strftime("%Y-%m-%d %H:%M:%S")
    }

def dispara_alerta(evento: str, mensagem: str):
    """Mock de disparo de alerta. Apenas loga / retorna sucesso (substituir por IFTTT/HTTP real se quiser)."""
    payload = {
        "evento": evento,
        "mensagem": mensagem,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    # Aqui apenas logamos — em produção chamar IFTTT/webhook/etc.
    print(f"[SIMULA_EVENTO] Alerta disparado (mock): {payload}")
    return {"ok": True, "payload": payload}