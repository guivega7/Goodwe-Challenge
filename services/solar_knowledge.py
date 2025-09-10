"""
RAG B2C - Base de Conhecimento de Energia Solar para Usuários Finais

Sistema de conhecimento focado em ajudar usuários comuns a:
- Entender energia solar de forma simples
- Otimizar consumo e economia
- Interpretar dados do sistema
- Cuidar melhor dos equipamentos
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

from utils.logger import get_logger

logger = get_logger(__name__)


class SolarKnowledgeBase:
    """
    Base de conhecimento sobre energia solar para usuários finais.
    
    Contém informações práticas e educativas sobre:
    - Conceitos básicos de energia solar
    - Interpretação de dados e métricas
    - Dicas de economia e otimização
    - Cuidados com equipamentos
    - Melhores práticas de uso
    """
    
    def __init__(self):
        self.knowledge = self._build_solar_knowledge()
    
    def _build_solar_knowledge(self) -> Dict[str, Any]:
        """Constrói a base de conhecimento de energia solar."""
        return {
            "conceitos_basicos": self._get_conceitos_basicos(),
            "interpretacao_dados": self._get_interpretacao_dados(),
            "dicas_economia": self._get_dicas_economia(),
            "cuidados_equipamentos": self._get_cuidados_equipamentos(),
            "otimizacao_consumo": self._get_otimizacao_consumo(),
            "horarios_ideais": self._get_horarios_ideais(),
            "manutencao": self._get_manutencao(),
            "troubleshooting": self._get_troubleshooting(),
            "sustentabilidade": self._get_sustentabilidade(),
            "generated_at": datetime.now().isoformat()
        }
    
    def _get_conceitos_basicos(self) -> List[Dict[str, str]]:
        """Conceitos básicos de energia solar."""
        return [
            {
                "termo": "kWh",
                "definicao": "Quilowatt-hora - unidade que mede a energia consumida ou gerada",
                "exemplo": "Se você deixar uma lâmpada de 100W ligada por 10 horas, ela consome 1 kWh",
                "categoria": "unidades"
            },
            {
                "termo": "SOC",
                "definicao": "State of Charge - porcentagem de carga da bateria (0-100%)",
                "exemplo": "SOC 80% significa que sua bateria está 80% carregada",
                "categoria": "bateria"
            },
            {
                "termo": "Energia Gerada",
                "definicao": "Quantidade de energia que seus painéis solares produziram",
                "exemplo": "Se gerou 25 kWh hoje, seus painéis captaram bastante sol",
                "categoria": "geracao"
            },
            {
                "termo": "Energia Consumida",
                "definicao": "Quantidade de energia que sua casa gastou",
                "exemplo": "Consumiu 20 kWh hoje = funcionamento normal de uma casa",
                "categoria": "consumo"
            },
            {
                "termo": "Energia Injetada",
                "definicao": "Energia excedente que você vendeu para a rede elétrica",
                "exemplo": "Injetou 5 kWh = você produziu mais do que gastou",
                "categoria": "rede"
            },
            {
                "termo": "Autopilot",
                "definicao": "Sistema inteligente que otimiza automaticamente o uso da energia",
                "exemplo": "Liga a máquina de lavar quando há sol e bateria carregada",
                "categoria": "automacao"
            },
            {
                "termo": "Tarifa Branca",
                "definicao": "Sistema de cobrança com preços diferentes por horário",
                "exemplo": "18h às 21h = horário de pico (mais caro)",
                "categoria": "tarifas"
            }
        ]
    
    def _get_interpretacao_dados(self) -> List[Dict[str, str]]:
        """Como interpretar os dados do sistema."""
        return [
            {
                "metrica": "SOC da Bateria",
                "faixa_otima": "20% - 90%",
                "explicacao": "Mantenha sempre entre 20% e 90% para prolongar a vida útil",
                "sinais_atencao": "Abaixo de 15% ou sempre acima de 95%",
                "acao": "Configure alertas para monitorar estes limites"
            },
            {
                "metrica": "Geração vs Consumo",
                "faixa_otima": "Geração > Consumo durante o dia",
                "explicacao": "Durante o dia, você deve gerar mais energia do que consome",
                "sinais_atencao": "Geração muito baixa em dias ensolarados",
                "acao": "Verifique se há sombra nos painéis ou sujeira"
            },
            {
                "metrica": "Eficiência do Sistema",
                "faixa_otima": "80% - 95%",
                "explicacao": "Porcentagem da energia solar que realmente chega até você",
                "sinais_atencao": "Abaixo de 75%",
                "acao": "Limpeza dos painéis ou verificação técnica"
            },
            {
                "metrica": "Consumo Horário",
                "faixa_otima": "Maior consumo entre 10h-16h",
                "explicacao": "Use mais energia quando há sol para economizar",
                "sinais_atencao": "Pico de consumo no horário de ponta (18h-21h)",
                "acao": "Agende aparelhos para funcionarem durante o dia"
            }
        ]
    
    def _get_dicas_economia(self) -> List[Dict[str, str]]:
        """Dicas práticas de economia de energia."""
        return [
            {
                "categoria": "Horários",
                "dica": "Use aparelhos pesados durante o dia",
                "explicacao": "Entre 10h e 16h você tem sol forte e não paga pela energia",
                "exemplos": "Máquina de lavar, secadora, ferro de passar, aspirador",
                "economia_estimada": "30-50% na conta de luz"
            },
            {
                "categoria": "Bateria",
                "dica": "Priorize bateria no horário de ponta",
                "explicacao": "18h às 21h use a energia da bateria, não da rede",
                "exemplos": "Iluminação, TV, computador, geladeira",
                "economia_estimada": "20-30% na conta de luz"
            },
            {
                "categoria": "Aparelhos",
                "dica": "Configure modo eco nos equipamentos",
                "explicacao": "Ar condicionado em 24°C, geladeira em temperatura média",
                "exemplos": "Ar 24°C em vez de 18°C, geladeira no nível 3 de 5",
                "economia_estimada": "15-25% no consumo"
            },
            {
                "categoria": "Monitoramento",
                "dica": "Acompanhe os dados diariamente",
                "explicacao": "5 minutos por dia para verificar geração e consumo",
                "exemplos": "Abrir o app, verificar alertas, ajustar horários",
                "economia_estimada": "10-20% por otimizações constantes"
            },
            {
                "categoria": "Standby",
                "dica": "Desligue aparelhos da tomada",
                "explicacao": "Modo standby consome energia 24h mesmo sem usar",
                "exemplos": "TV, micro-ondas, carregadores, computadores",
                "economia_estimada": "5-10% no consumo base"
            }
        ]
    
    def _get_cuidados_equipamentos(self) -> List[Dict[str, str]]:
        """Cuidados com equipamentos do sistema solar."""
        return [
            {
                "equipamento": "Painéis Solares",
                "frequencia": "Mensal",
                "cuidado": "Limpeza com água e pano macio",
                "motivo": "Sujeira reduz eficiência em até 25%",
                "sinais_problema": "Geração muito baixa em dias ensolarados"
            },
            {
                "equipamento": "Bateria",
                "frequencia": "Diário",
                "cuidado": "Manter SOC entre 20-90%",
                "motivo": "Preserva vida útil da bateria",
                "sinais_problema": "SOC sempre muito baixo ou muito alto"
            },
            {
                "equipamento": "Inversor",
                "frequencia": "Semanal",
                "cuidado": "Verificar ventilação e temperatura",
                "motivo": "Superaquecimento reduz eficiência",
                "sinais_problema": "Ruído excessivo ou muito quente"
            },
            {
                "equipamento": "Cabos e Conexões",
                "frequencia": "Trimestral",
                "cuidado": "Inspeção visual de desgaste",
                "motivo": "Conexões soltas causam perdas",
                "sinais_problema": "Quedas súbitas na geração"
            }
        ]
    
    def _get_otimizacao_consumo(self) -> List[Dict[str, str]]:
        """Estratégias de otimização do consumo."""
        return [
            {
                "estrategia": "Programação de Aparelhos",
                "descricao": "Agende aparelhos para horários de sol forte",
                "horario_ideal": "10h às 16h",
                "aparelhos": "Máquina de lavar, lava-louças, ferro elétrico",
                "beneficio": "Usa energia solar direta sem custo"
            },
            {
                "estrategia": "Gestão de Temperatura",
                "descricao": "Pré-resfrie a casa durante o dia",
                "horario_ideal": "14h às 17h",
                "aparelhos": "Ar condicionado, ventiladores",
                "beneficio": "Casa já fria para o horário de ponta"
            },
            {
                "estrategia": "Carregamento de Dispositivos",
                "descricao": "Carregue todos os dispositivos durante o dia",
                "horario_ideal": "12h às 15h",
                "aparelhos": "Celular, notebook, tablet, baterias",
                "beneficio": "Aproveita energia solar gratuita"
            },
            {
                "estrategia": "Aquecimento de Água",
                "descricao": "Use resistência elétrica no horário solar",
                "horario_ideal": "13h às 16h",
                "aparelhos": "Chuveiro elétrico, aquecedor",
                "beneficio": "Água quente grátis do sol"
            }
        ]
    
    def _get_horarios_ideais(self) -> List[Dict[str, str]]:
        """Horários ideais para diferentes atividades."""
        return [
            {
                "periodo": "06h às 10h - Manhã",
                "caracteristica": "Sol fraco, bateria carregando",
                "atividades_ideais": "Atividades leves: café, computador, iluminação",
                "evitar": "Aparelhos pesados que vão drenar a bateria",
                "dica": "Bom momento para verificar dados do sistema"
            },
            {
                "periodo": "10h às 16h - Dia",
                "caracteristica": "Sol forte, energia grátis",
                "atividades_ideais": "TUDO! Máquina, ferro, ar condicionado, carregamentos",
                "evitar": "Desperdiçar essa janela de oportunidade",
                "dica": "MELHOR horário - use energia à vontade"
            },
            {
                "periodo": "16h às 18h - Tarde",
                "caracteristica": "Sol diminuindo, últimas oportunidades",
                "atividades_ideais": "Finalizar tarefas pesadas, carregar dispositivos",
                "evitar": "Começar atividades que vão além das 18h",
                "dica": "Última chance de energia solar do dia"
            },
            {
                "periodo": "18h às 21h - Ponta",
                "caracteristica": "HORÁRIO MAIS CARO - usar bateria",
                "atividades_ideais": "Iluminação, TV, computador (baixo consumo)",
                "evitar": "Qualquer aparelho pesado - vai custar caro!",
                "dica": "Sobreviva com energia da bateria"
            },
            {
                "periodo": "21h às 06h - Noite",
                "caracteristica": "Tarifa normal, economia de energia",
                "atividades_ideais": "Atividades essenciais, descanso dos equipamentos",
                "evitar": "Desperdícios desnecessários",
                "dica": "Prepare-se para o próximo dia solar"
            }
        ]
    
    def _get_manutencao(self) -> List[Dict[str, str]]:
        """Dicas de manutenção preventiva."""
        return [
            {
                "item": "Limpeza dos Painéis",
                "quando": "Todo mês ou após chuvas com poeira",
                "como": "Água limpa + pano macio, de manhã cedo",
                "cuidados": "Nunca use produtos químicos ou água fria em painel quente",
                "resultado": "Até 25% mais geração de energia"
            },
            {
                "item": "Verificação Visual",
                "quando": "Toda semana",
                "como": "Olhar painéis, cabos, inversor por 2 minutos",
                "cuidados": "Procurar rachaduras, animais, folhas acumuladas",
                "resultado": "Detecta problemas antes que virem grandes defeitos"
            },
            {
                "item": "Monitoramento de Dados",
                "quando": "Todo dia",
                "como": "Verificar app por 1 minuto: geração, consumo, bateria",
                "cuidados": "Anotar valores estranhos para mostrar ao técnico",
                "resultado": "Identifica queda de performance rapidamente"
            },
            {
                "item": "Inspeção Técnica",
                "quando": "Uma vez por ano",
                "como": "Chamar técnico especializado para revisão completa",
                "cuidados": "Escolher profissional certificado e experiente",
                "resultado": "Garante vida útil máxima do sistema (25+ anos)"
            }
        ]
    
    def _get_troubleshooting(self) -> List[Dict[str, str]]:
        """Soluções para problemas comuns."""
        return [
            {
                "problema": "Geração baixa em dia ensolarado",
                "causas": "Sujeira nos painéis, sombra, defeito técnico",
                "solucao": "1. Limpe os painéis 2. Verifique sombras 3. Chame técnico",
                "prevencao": "Limpeza mensal e inspeção visual semanal"
            },
            {
                "problema": "Bateria descarrega muito rápido",
                "causas": "Consumo alto, bateria velha, configuração errada",
                "solucao": "1. Reduza consumo noturno 2. Verifique equipamentos em standby",
                "prevencao": "Evite descarregar abaixo de 20%"
            },
            {
                "problema": "Conta de luz ainda alta",
                "causas": "Uso inadequado dos horários, consumo excessivo",
                "solucao": "1. Use aparelhos pesados só durante o dia 2. Evite horário de ponta",
                "prevencao": "Monitore dados diários e ajuste hábitos"
            },
            {
                "problema": "Sistema desliga sozinho",
                "causas": "Proteção por temperatura, sobrecarga, defeito",
                "solucao": "1. Verifique ventilação 2. Reduza carga 3. Chame técnico urgente",
                "prevencao": "Não sobrecarregue o sistema"
            }
        ]
    
    def _get_sustentabilidade(self) -> List[Dict[str, str]]:
        """Impacto ambiental e sustentabilidade."""
        return [
            {
                "aspecto": "Redução de CO2",
                "explicacao": "Cada kWh solar evita emissão de 0.5kg de CO2",
                "exemplo": "Sistema de 5kW evita 2.5 toneladas de CO2 por ano",
                "equivalencia": "Como plantar 30 árvores por ano",
                "beneficio": "Contribui diretamente contra mudanças climáticas"
            },
            {
                "aspecto": "Economia de Água",
                "explicacao": "Energia solar não precisa de água para gerar eletricidade",
                "exemplo": "Evita uso de 20.000L de água por ano (vs termelétrica)",
                "equivalencia": "Água suficiente para 200 banhos",
                "beneficio": "Preserva recursos hídricos"
            },
            {
                "aspecto": "Independência Energética",
                "explicacao": "Menos dependência de energia fóssil importada",
                "exemplo": "Cada casa solar reduz pressão na rede elétrica",
                "equivalencia": "Menos necessidade de construir usinas",
                "beneficio": "País mais independente energeticamente"
            },
            {
                "aspecto": "Vida Útil dos Equipamentos",
                "explicacao": "Painéis solares duram 25+ anos com manutenção",
                "exemplo": "Investimento se paga em 5-7 anos, lucro por 20 anos",
                "equivalencia": "Como comprar energia antecipada com desconto",
                "beneficio": "Economia a longo prazo garantida"
            }
        ]
    
    def get_relevant_context(self, query: str, max_items: int = 3) -> List[Dict[str, Any]]:
        """
        Busca contexto relevante para responder perguntas sobre energia solar.
        
        Args:
            query: Pergunta do usuário
            max_items: Máximo de itens relevantes
            
        Returns:
            List: Contexto relevante encontrado
        """
        query_lower = query.lower()
        relevant_items = []
        
        # Palavras-chave para cada categoria
        keywords = {
            "conceitos_basicos": ["kwh", "soc", "energia", "o que é", "significa", "conceito"],
            "interpretacao_dados": ["dados", "números", "gráfico", "dashboard", "interpretar", "entender"],
            "dicas_economia": ["economia", "economizar", "conta", "dinheiro", "barato", "dicas"],
            "cuidados_equipamentos": ["cuidado", "manutenção", "equipamento", "painel", "bateria", "limpar"],
            "otimizacao_consumo": ["otimizar", "melhor", "horário", "quando usar", "programar"],
            "horarios_ideais": ["horário", "quando", "melhor hora", "período", "manhã", "tarde", "noite"],
            "manutencao": ["manutenção", "limpar", "cuidar", "conservar", "durar"],
            "troubleshooting": ["problema", "erro", "não funciona", "defeito", "ajuda"],
            "sustentabilidade": ["meio ambiente", "co2", "sustentavel", "ecológico", "planeta"]
        }
        
        # Busca por categoria
        for category, category_keywords in keywords.items():
            if any(keyword in query_lower for keyword in category_keywords):
                category_data = self.knowledge.get(category, [])
                if category_data:
                    relevant_items.append({
                        'category': category,
                        'data': category_data,
                        'relevance': self._calculate_relevance(query_lower, category_keywords)
                    })
        
        # Ordena por relevância e retorna os mais relevantes
        relevant_items.sort(key=lambda x: x['relevance'], reverse=True)
        return relevant_items[:max_items]
    
    def _calculate_relevance(self, query: str, keywords: List[str]) -> float:
        """Calcula relevância baseada em palavras-chave encontradas."""
        matches = sum(1 for keyword in keywords if keyword in query)
        return matches / len(keywords)
    
    def get_contextual_prompt(self, user_question: str, user_data: Dict = None) -> str:
        """
        Gera prompt contextual para o Gemini com base na pergunta do usuário.
        
        Args:
            user_question: Pergunta do usuário
            user_data: Dados do sistema do usuário (energia, SOC, etc.)
            
        Returns:
            str: Prompt completo com contexto
        """
        # Busca contexto relevante
        relevant_context = self.get_relevant_context(user_question, max_items=2)
        
        prompt = """Você é um assistente especialista em energia solar residencial, focado em ajudar usuários finais (não técnicos) a aproveitar melhor seu sistema fotovoltaico.

CARACTERÍSTICAS DO SEU ATENDIMENTO:
- Use linguagem simples e amigável
- Dê exemplos práticos e concretos
- Foque em economia e sustentabilidade
- Seja didático mas não condescendente
- Termine com uma dica prática

"""
        
        # Adiciona dados do usuário se disponíveis
        if user_data:
            prompt += "DADOS ATUAIS DO USUÁRIO:\n"
            if user_data.get('energia_gerada'):
                prompt += f"- Energia gerada hoje: {user_data['energia_gerada']} kWh\n"
            if user_data.get('energia_consumida'):
                prompt += f"- Energia consumida hoje: {user_data['energia_consumida']} kWh\n"
            if user_data.get('soc_bateria'):
                prompt += f"- Carga da bateria: {user_data['soc_bateria']}%\n"
            prompt += "\n"
        
        # Adiciona contexto relevante
        if relevant_context:
            prompt += "CONTEXTO RELEVANTE PARA ESTA PERGUNTA:\n"
            for i, ctx in enumerate(relevant_context, 1):
                category = ctx['category'].replace('_', ' ').title()
                prompt += f"\n{i}. {category}:\n"
                
                # Adiciona alguns itens da categoria
                data = ctx['data'][:3]  # Primeiros 3 itens
                for item in data:
                    if isinstance(item, dict):
                        if 'dica' in item:
                            prompt += f"   • {item['dica']}: {item.get('explicacao', '')}\n"
                        elif 'termo' in item:
                            prompt += f"   • {item['termo']}: {item.get('definicao', '')}\n"
                        elif 'problema' in item:
                            prompt += f"   • {item['problema']}: {item.get('solucao', '')}\n"
                        elif 'estrategia' in item:
                            prompt += f"   • {item['estrategia']}: {item.get('descricao', '')}\n"
                        elif 'metrica' in item:
                            prompt += f"   • {item['metrica']}: {item.get('explicacao', '')}\n"
        
        prompt += f"\nPERGUNTA DO USUÁRIO: {user_question}\n\n"
        prompt += """INSTRUÇÕES FINAIS:
1. Responda de forma clara e prática
2. Use os dados do usuário quando relevante
3. Baseie-se no contexto fornecido
4. Dê exemplos concretos
5. Termine com uma dica prática
6. Mantenha o tom amigável e encorajador
7. Limite a resposta a 200 palavras

Sua resposta:"""
        
        return prompt


# Instância global da base de conhecimento solar
solar_knowledge = SolarKnowledgeBase()
