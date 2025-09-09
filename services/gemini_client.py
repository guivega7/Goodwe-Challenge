"""
Cliente Gemini para análises e insights inteligentes do SolarMind.

Integra com a API do Google Gemini para:
- Gerar insights sobre consumo/geração solar
- Chat inteligente sobre o projeto
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
    """Cliente para integração com Google Gemini API."""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.base_url = 'https://generativelanguage.googleapis.com/v1beta/models'
        self.model = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
        self.timeout = int(os.getenv('GEMINI_TIMEOUT', '30'))
        self.max_tokens = int(os.getenv('GEMINI_MAX_TOKENS', '1000'))
        
    def is_enabled(self) -> bool:
        """Verifica se o Gemini está habilitado e configurado."""
        enabled = os.getenv('ENABLE_GEMINI', 'true').lower() in ('1', 'true', 'yes', 'on')
        has_key = bool(self.api_key and self.api_key.strip())
        return enabled and has_key
    
    def _make_request(self, prompt: str, context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Faz requisição para a API do Gemini."""
        if not self.is_enabled():
            logger.warning("Gemini está desabilitado ou sem API key")
            return None
            
        # Monta o prompt final
        full_prompt = prompt
        if context:
            full_prompt = f"Contexto:\n{context}\n\nPergunta: {prompt}"
            
        url = f"{self.base_url}/{self.model}:generateContent"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            'contents': [{
                'parts': [{
                    'text': full_prompt
                }]
            }],
            'generationConfig': {
                'maxOutputTokens': self.max_tokens,
                'temperature': 0.7
            }
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                params={'key': self.api_key},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Gemini API error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Timeout na requisição para Gemini")
            return None
        except Exception as e:
            logger.error(f"Erro na requisição Gemini: {e}")
            return None
    
    def extract_text_response(self, response: Optional[Dict[str, Any]]) -> str:
        """Extrai o texto da resposta do Gemini."""
        if not response:
            return "Desculpe, não consegui gerar uma resposta no momento."
            
        try:
            candidates = response.get('candidates', [])
            if candidates:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                if parts:
                    return parts[0].get('text', '').strip()
        except Exception as e:
            logger.error(f"Erro ao extrair texto do Gemini: {e}")
            
        return "Erro ao processar resposta da IA."
    
    def generate_insights(self, energia_gerada: float, energia_consumida: float, 
                         soc_bateria: float, periodo: str = "hoje") -> str:
        """
        Gera insights sobre o desempenho do sistema solar.
        
        Args:
            energia_gerada: Energia gerada em kWh
            energia_consumida: Energia consumida em kWh  
            soc_bateria: Estado de carga da bateria (%)
            periodo: Período de análise ("hoje", "semana", etc.)
            
        Returns:
            str: Insights em linguagem natural
        """
        prompt = f"""
        Você é um especialista em energia solar analisando dados de um sistema residencial.
        
        Dados do sistema {periodo}:
        - Energia gerada: {energia_gerada} kWh
        - Energia consumida: {energia_consumida} kWh
        - Estado da bateria: {soc_bateria}%
        
        Gere insights úteis em português brasileiro sobre:
        1. Eficiência do sistema
        2. Oportunidades de economia
        3. Recomendações práticas
        4. Comparação com médias típicas
        
        Seja objetivo, prático e use uma linguagem amigável.
        Limite sua resposta a 200 palavras.
        """
        
        response = self._make_request(prompt)
        return self.extract_text_response(response)
    
    def chat_response(self, message: str, conversation_context: Optional[List[Dict]] = None) -> str:
        """
        Responde uma mensagem de chat sobre o sistema solar.
        
        Args:
            message: Mensagem do usuário
            conversation_context: Histórico da conversa
            
        Returns:
            str: Resposta do assistente
        """
        # Monta contexto da conversa
        context_str = ""
        if conversation_context:
            context_str = "Histórico da conversa:\n"
            for msg in conversation_context[-5:]:  # Últimas 5 mensagens
                role = "Usuário" if msg.get('role') == 'user' else "Assistente"
                context_str += f"{role}: {msg.get('content', '')}\n"
            context_str += "\n"
        
        prompt = f"""
        Você é um assistente especializado em energia solar e o sistema SolarMind.
        
        O SolarMind é uma plataforma que:
        - Monitora sistemas solares residenciais GoodWe
        - Controla aparelhos domésticos
        - Gera insights com IA
        - Integra com Alexa e IFTTT
        - Tem funcionalidades como Energy Autopilot (plano do dia)
        
        {context_str}Pergunta atual: {message}
        
        Responda de forma útil, técnica quando necessário, mas sempre amigável.
        Se a pergunta não for sobre energia solar ou o sistema, redirecione educadamente.
        Limite sua resposta a 150 palavras.
        """
        
        response = self._make_request(prompt)
        return self.extract_text_response(response)
    
    def analyze_project_question(self, question: str, project_context: str = "") -> str:
        """
        Responde perguntas sobre o projeto SolarMind usando contexto dos arquivos.
        
        Args:
            question: Pergunta sobre o projeto
            project_context: Contexto extraído dos arquivos do projeto
            
        Returns:
            str: Resposta baseada no contexto do projeto
        """
        prompt = f"""
        Você é um assistente que conhece profundamente o projeto SolarMind.
        
        Responda a pergunta baseando-se no contexto fornecido.
        Se não souber algo específico, seja honesto sobre isso.
        
        Pergunta: {question}
        """
        
        response = self._make_request(prompt, project_context)
        return self.extract_text_response(response)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Testa a conexão com o Gemini.
        
        Returns:
            dict: Status da conexão e resposta de teste
        """
        if not self.is_enabled():
            return {
                'status': 'disabled',
                'message': 'Gemini está desabilitado ou sem API key',
                'enabled': False,
                'has_key': bool(self.api_key)
            }
        
        test_prompt = "Responda apenas: 'Conexão com Gemini funcionando!'"
        response = self._make_request(test_prompt)
        
        if response:
            text = self.extract_text_response(response)
            return {
                'status': 'success',
                'message': text,
                'enabled': True,
                'model': self.model
            }
        else:
            return {
                'status': 'error',
                'message': 'Falha na comunicação com Gemini',
                'enabled': True,
                'model': self.model
            }


# Instância global para reutilização
gemini_client = GeminiClient()
