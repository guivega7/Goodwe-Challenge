"""
Cliente Gemini para análises e insights inteligentes do SolarMind.

Integra com a API do Google Gemini para:
- Gerar insights sobre consumo/geração solar
- Chat inteligente sobre energia solar para usuários
- Análises em linguagem natural dos dados históricos
"""

import os
import json
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


class GeminiClient:
    """Cliente para integração com Google Gemini API focado em energia solar B2C."""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.base_url = 'https://generativelanguage.googleapis.com/v1beta/models'
        self.model = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
        self.timeout = int(os.getenv('GEMINI_TIMEOUT', '30'))
        self.max_tokens = int(os.getenv('GEMINI_MAX_TOKENS', '1000'))
        
    def is_enabled(self) -> bool:
        """Verifica se o Gemini está habilitado e configurado."""
        enabled = os.getenv('ENABLE_GEMINI', 'true').lower() in ('1', 'true', 'yes', 'on')
        return enabled and bool(self.api_key)
    
    def generate_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera insights personalizados sobre dados de energia solar.
        
        Args:
            data: Dados do sistema (energia_gerada, consumida, SOC, etc.)
            
        Returns:
            Dict com insights gerados ou fallback em caso de erro
        """
        if not self.is_enabled():
            return self._get_fallback_insights(data)
        
        try:
            # Cria prompt focado em B2C com contexto de energia solar
            prompt = self._create_insights_prompt(data)
            
            # Chama API do Gemini
            response = self._call_gemini_api(prompt)
            
            if response:
                return {
                    'insights': response,
                    'source': 'gemini_ai',
                    'generated_at': datetime.now().isoformat(),
                    'data_analyzed': data
                }
            else:
                return self._get_fallback_insights(data)
                
        except Exception as e:
            logger.error(f"Erro ao gerar insights: {e}")
            return self._get_fallback_insights(data)
    
    def chat_response(self, message: str, user_data: Dict = None, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Resposta de chat sobre energia solar para usuários finais.
        
        Args:
            message: Mensagem do usuário
            user_data: Dados do sistema do usuário
            conversation_history: Histórico da conversa
            
        Returns:
            Dict com resposta ou fallback
        """
        if not self.is_enabled():
            return self._get_fallback_chat_response(message)
        
        try:
            # Cria prompt simples focado em energia solar
            prompt = self._create_simple_chat_prompt(message, user_data)
            
            # Adiciona histórico se disponível
            if conversation_history:
                prompt = self._add_conversation_history(prompt, conversation_history)
            
            # Chama API do Gemini
            response = self._call_gemini_api(prompt)
            
            if response:
                return {
                    'response': response,
                    'source': 'gemini_solar_ai',
                    'generated_at': datetime.now().isoformat(),
                    'context_used': True
                }
            else:
                return self._get_fallback_chat_response(message)
                
        except Exception as e:
            logger.error(f"Erro no chat: {e}")
            return self._get_fallback_chat_response(message)
    
    def _create_insights_prompt(self, data: Dict[str, Any]) -> str:
        """Cria prompt para insights focado em usuário final."""
        energia_gerada = data.get('energia_gerada', 0)
        energia_consumida = data.get('energia_consumida', 0)
        soc_bateria = data.get('soc_bateria', 0)
        economia_estimada = data.get('economia_estimada', 0)
        
        prompt = f"""Você é um consultor de energia solar especializado em ajudar usuários residenciais.

DADOS DE HOJE:
- Energia gerada: {energia_gerada:.1f} kWh
- Energia consumida: {energia_consumida:.1f} kWh
- Bateria: {soc_bateria:.0f}%
- Economia estimada: R$ {economia_estimada:.2f}

TAREFA: Gere 3 insights práticos e motivadores para o usuário, focando em:
1. Performance do sistema hoje
2. Dica prática de otimização
3. Impacto positivo (economia/sustentabilidade)

FORMATO:
- Use linguagem simples e amigável
- Seja específico com os números
- Termine cada insight com uma ação prática
- Máximo 50 palavras por insight
- Tom positivo e encorajador

Insights:"""
        
        return prompt
    
    def _create_simple_chat_prompt(self, message: str, user_data: Dict = None) -> str:
        """Cria prompt simples para chat sobre energia solar."""
        prompt = """Você é um assistente de energia solar residencial especializado em ajudar usuários comuns.

SUAS CARACTERÍSTICAS:
- Use linguagem simples e amigável
- Foque em economia e sustentabilidade
- Dê dicas práticas
- Seja motivador e positivo
- Use emojis ocasionalmente

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
        
        prompt += f"PERGUNTA DO USUÁRIO: {message}\n\n"
        prompt += """Responda de forma clara e prática, máximo 150 palavras. Se possível, use os dados do usuário na resposta."""
        
        return prompt
    
    def _add_conversation_history(self, prompt: str, history: List[Dict]) -> str:
        """Adiciona histórico relevante ao prompt."""
        if not history or len(history) == 0:
            return prompt
        
        # Pega últimas 3 mensagens para contexto
        recent_history = history[-3:] if len(history) > 3 else history
        
        history_text = "\nCONVERSA ANTERIOR:\n"
        for msg in recent_history:
            role = "Usuário" if msg.get('role') == 'user' else "Assistente"
            content = msg.get('content', '')[:100]  # Limita a 100 chars
            history_text += f"{role}: {content}\n"
        
        return history_text + "\n" + prompt
    
    def _call_gemini_api(self, prompt: str) -> Optional[str]:
        """Faz chamada para API do Gemini."""
        if not self.api_key:
            logger.warning("API key do Gemini não configurada")
            return None
        
        try:
            url = f"{self.base_url}/{self.model}:generateContent"
            
            headers = {
                'Content-Type': 'application/json',
            }
            
            payload = {
                'contents': [{
                    'parts': [{
                        'text': prompt
                    }]
                }],
                'generationConfig': {
                    'maxOutputTokens': self.max_tokens,
                    'temperature': 0.7
                }
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                params={'key': self.api_key},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0].get('content', {})
                    if 'parts' in content and len(content['parts']) > 0:
                        return content['parts'][0].get('text', '').strip()
            else:
                logger.error(f"Erro na API Gemini: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            logger.error("Timeout na chamada para Gemini API")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão com Gemini API: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado na API Gemini: {e}")
        
        return None
    
    def _get_fallback_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insights de fallback quando Gemini não está disponível."""
        energia_gerada = data.get('energia_gerada', 0)
        energia_consumida = data.get('energia_consumida', 0)
        soc_bateria = data.get('soc_bateria', 0)
        economia_estimada = data.get('economia_estimada', 0)
        hora_atual = data.get('horario_atual', datetime.now().hour)
        
        insights = []
        
        # Insight 1: Performance baseado na hora do dia
        if 6 <= hora_atual <= 18:  # Durante o dia
            if energia_gerada > energia_consumida:
                eficiencia = (energia_gerada / energia_consumida * 100) if energia_consumida > 0 else 150
                insights.append(
                    f"🌞 Excelente performance diurna! Gerou {energia_gerada:.1f} kWh contra {energia_consumida:.1f} kWh consumidos. "
                    f"Seu sistema está {eficiencia:.0f}% eficiente - parabéns!"
                )
            else:
                insights.append(
                    f"☀️ Produção solar em andamento: {energia_gerada:.1f} kWh gerados. "
                    f"Para maximizar economia, use aparelhos pesados entre 10h-16h quando o sol estiver forte!"
                )
        else:  # Durante a noite
            insights.append(
                f"🌙 Modo noturno ativo. Bateria em {soc_bateria:.0f}% - suficiente para cobrir consumo noturno. "
                f"Próxima carga solar começa às 6h da manhã."
            )
        
        # Insight 2: Bateria e armazenamento
        if soc_bateria > 80:
            insights.append(
                f"🔋 Bateria totalmente carregada ({soc_bateria:.0f}%)! Perfeita para enfrentar o horário de ponta (18h-21h) "
                f"sem depender da rede elétrica cara. Economia garantida!"
            )
        elif soc_bateria > 50:
            insights.append(
                f"🔋 Bateria em ótimo nível ({soc_bateria:.0f}%). Continue usando energia solar durante o dia "
                f"para manter este nível e garantir autonomia noturna."
            )
        elif soc_bateria > 20:
            insights.append(
                f"🔋 Bateria em {soc_bateria:.0f}%. Nível adequado, mas considere reduzir consumo de aparelhos pesados "
                f"à noite para preservar a carga até amanhã."
            )
        else:
            insights.append(
                f"⚠️ Bateria baixa ({soc_bateria:.0f}%). Evite usar aparelhos de alto consumo agora. "
                f"Amanhã cedo o sol recarregará completamente a bateria."
            )
        
        # Insight 3: Economia e sustentabilidade
        if economia_estimada > 0:
            co2_evitado = energia_gerada * 0.5  # kg CO2 por kWh
            insights.append(
                f"💰 Economia hoje: R$ {economia_estimada:.2f} só com energia solar! "
                f"Isso equivale a evitar {co2_evitado:.1f}kg de CO2 - mesmo que dirigir {co2_evitado/2:.1f}km de carro. "
                f"Continue investindo em energia limpa!"
            )
        else:
            insights.append(
                f"🌱 Mesmo sem geração hoje, seu investimento em energia solar já evitou toneladas de CO2. "
                f"Os dias nublados fazem parte do ciclo - amanhã o sol volta mais forte!"
            )
        
        return {
            'insights': insights,
            'source': 'fallback_intelligent',
            'generated_at': datetime.now().isoformat(),
            'data_analyzed': data
        }
    
    def _get_fallback_chat_response(self, message: str) -> Dict[str, Any]:
        """Resposta de fallback para chat quando Gemini não está disponível."""
        message_lower = message.lower()
        
        # Respostas baseadas em palavras-chave
        if any(word in message_lower for word in ['economia', 'economizar', 'conta', 'dinheiro']):
            response = (
                "💰 Para economizar mais: 1) Use aparelhos pesados entre 10h-16h (energia grátis do sol), "
                "2) Evite horário de ponta 18h-21h (mais caro), 3) Carregue dispositivos durante o dia. "
                "Dica: acompanhe os dados diários para otimizar seu consumo!"
            )
        elif any(word in message_lower for word in ['bateria', 'soc', 'carga']):
            response = (
                "🔋 Sobre a bateria: mantenha entre 20-90% para durar mais. Durante o dia ela carrega com sol, "
                "à noite use com moderação. No horário de ponta (18h-21h) é sua melhor amiga para evitar energia cara!"
            )
        elif any(word in message_lower for word in ['limpeza', 'limpar', 'sujeira', 'manutenção']):
            response = (
                "🧽 Limpeza dos painéis: uma vez por mês com água limpa e pano macio, de manhã cedo. "
                "Sujeira pode reduzir 25% da geração! Evite produtos químicos e nunca limpe painéis quentes."
            )
        elif any(word in message_lower for word in ['horário', 'quando', 'melhor hora']):
            response = (
                "⏰ Horários ideais: 10h-16h = energia grátis (use à vontade), "
                "18h-21h = horário de ponta (só o essencial), resto do dia = consumo moderado. "
                "Programe máquina de lavar, ferro e aparelhos pesados para o meio do dia!"
            )
        else:
            response = (
                "☀️ Olá! Sou seu assistente de energia solar. Posso ajudar com dicas de economia, "
                "horários ideais, cuidados com equipamentos e interpretação dos seus dados. "
                "O que gostaria de saber sobre seu sistema solar?"
            )
        
        return {
            'response': response,
            'source': 'fallback_keywords',
            'generated_at': datetime.now().isoformat(),
            'context_used': False
        }


# Instância global do cliente
gemini_client = GeminiClient()
