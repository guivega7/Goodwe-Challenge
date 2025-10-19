# Mock básico de previsão do tempo; em produção, integrar com utils.previsao

from utils.previsao import obter_previsao_tempo

def get_weather_forecast() -> str:
    """Retorna uma descrição simples do tempo para hoje.
    Tenta usar utils.previsao.obter_previsao_tempo(); cai para um valor padrão se indisponível.
    """
    try:
        previsao = obter_previsao_tempo()
        if previsao and isinstance(previsao, list) and len(previsao) > 0:
            desc = previsao[0].get('descricao') or previsao[0].get('description')
            if isinstance(desc, str) and desc.strip():
                return desc
    except Exception:
        pass
    return "Ensolarado com poucas nuvens"
