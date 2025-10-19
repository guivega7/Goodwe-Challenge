import json
import re


def generate_gemini_text(prompt: str) -> str:
    """
    Versão final da IA mock.
    Analisa o prompt para extrair dados e tomar uma decisão inteligente
    baseada em múltiplos fatores (bateria E previsão do tempo).
    Sempre retorna uma string JSON com as chaves 'acao' e 'explicacao'.
    """
    print("--- MOCK GEMINI AVANÇADO: Analisando o prompt recebido. ---")

    prompt_text = prompt if isinstance(prompt, str) else ""
    prompt_lower = prompt_text.lower()

    # 1) Extrair dados do prompt (case-insensitive)
    try:
        battery_match = re.search(r"bateria[_\s]*atual:\s*(\d+)", prompt_text, re.IGNORECASE)
        battery_level = int(battery_match.group(1)) if battery_match else 0

        is_bad_weather = ("chuva" in prompt_lower) or ("nublado" in prompt_lower) or ("tempestade" in prompt_lower)
        print(f"--- MOCK GEMINI: Dados extraídos -> Bateria: {battery_level}%, Tempo Ruim: {is_bad_weather} ---")
    except Exception:
        battery_level = 0
        is_bad_weather = True

    # 2) Decisão
    if is_bad_weather:
        acao = "ATIVAR_MODO_ECO"
        explicacao = (
            f"Atenção! A previsão para hoje é de tempo instável, o que vai impactar a geração. "
            f"Mesmo com a bateria em {battery_level}%, estou ativando o modo de economia para garantir sua autonomia para a noite."
        )
    elif battery_level < 50:
        acao = "ATIVAR_MODO_ECO"
        explicacao = (
            f"Apesar do sol, a bateria está baixa, em apenas {battery_level}%. O Autopilot vai focar em recarregar o sistema. "
            f"Recomendo evitar alto consumo até a bateria se recuperar."
        )
    else:
        acao = "MANTER_NORMAL"
        explicacao = (
            f"A previsão para hoje é de sol e com a bateria em {battery_level}%, o sistema operará normalmente. "
            f"É um ótimo dia para aproveitar a energia gerada!"
        )

    # 3) Saída JSON
    return json.dumps({
        "acao": acao,
        "explicacao": explicacao
    }, ensure_ascii=False)
