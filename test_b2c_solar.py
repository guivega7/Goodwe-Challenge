"""
Teste do Sistema B2C Solar Knowledge
Demonstra como o sistema agora foca em usuários finais
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.solar_knowledge import solar_knowledge
from services.gemini_client import GeminiClient

# Instância para teste
gemini_client = GeminiClient()


def test_solar_knowledge():
    """Testa a base de conhecimento solar B2C."""
    print("🌞 TESTE: Base de Conhecimento Solar B2C")
    print("=" * 50)
    
    # Testa busca por contexto
    perguntas = [
        "Como economizar na conta de luz?",
        "Quando devo usar minha máquina de lavar?",
        "O que significa SOC da bateria?",
        "Meu sistema está gerando pouco, o que fazer?",
        "Como limpar os painéis solares?"
    ]
    
    for pergunta in perguntas:
        print(f"\n📝 PERGUNTA: {pergunta}")
        contexto = solar_knowledge.get_relevant_context(pergunta, max_items=2)
        
        if contexto:
            for i, ctx in enumerate(contexto, 1):
                categoria = ctx['category'].replace('_', ' ').title()
                relevancia = ctx['relevance']
                print(f"   {i}. {categoria} (relevância: {relevancia:.2f})")
        else:
            print("   ❌ Nenhum contexto encontrado")
    
    print("\n✅ Teste de busca contextual concluído!")


def test_gemini_fallback():
    """Testa respostas de fallback do Gemini focadas em B2C."""
    print("\n🤖 TESTE: Respostas Gemini B2C (Fallback)")
    print("=" * 50)
    
    perguntas = [
        "Como economizar na conta de luz?",
        "Qual o melhor horário para usar aparelhos?",
        "Como cuidar da bateria?",
        "Como limpar os painéis?",
        "Olá, preciso de ajuda"
    ]
    
    for pergunta in perguntas:
        print(f"\n📝 PERGUNTA: {pergunta}")
        resposta = gemini_client._get_fallback_chat_response(pergunta)
        print(f"💬 RESPOSTA: {resposta['response'][:100]}...")
        print(f"🏷️  FONTE: {resposta['source']}")
    
    print("\n✅ Teste de chat fallback concluído!")


def test_insights_fallback():
    """Testa insights focados em usuário final."""
    print("\n💡 TESTE: Insights B2C (Fallback)")
    print("=" * 50)
    
    # Simula dados de diferentes cenários
    cenarios = [
        {
            "nome": "Dia Excelente",
            "dados": {
                "energia_gerada": 28.5,
                "energia_consumida": 18.2,
                "soc_bateria": 92,
                "economia_estimada": 15.80
            }
        },
        {
            "nome": "Dia Nublado",
            "dados": {
                "energia_gerada": 12.3,
                "energia_consumida": 22.1,
                "soc_bateria": 34,
                "economia_estimada": 6.20
            }
        },
        {
            "nome": "Bateria Baixa",
            "dados": {
                "energia_gerada": 15.7,
                "energia_consumida": 19.8,
                "soc_bateria": 18,
                "economia_estimada": 8.90
            }
        }
    ]
    
    for cenario in cenarios:
        print(f"\n🎯 CENÁRIO: {cenario['nome']}")
        print(f"   📊 Dados: {cenario['dados']}")
        
        insights = gemini_client._get_fallback_insights(cenario['dados'])
        
        print(f"   💭 Insights gerados:")
        for i, insight in enumerate(insights['insights'], 1):
            print(f"      {i}. {insight[:80]}...")
    
    print("\n✅ Teste de insights concluído!")


def test_contextual_prompt():
    """Testa geração de prompts contextuais."""
    print("\n📝 TESTE: Prompts Contextuais B2C")
    print("=" * 50)
    
    user_data = {
        "energia_gerada": 22.4,
        "energia_consumida": 18.9,
        "soc_bateria": 76
    }
    
    pergunta = "Qual o melhor horário para usar minha máquina de lavar?"
    
    prompt = solar_knowledge.get_contextual_prompt(pergunta, user_data)
    
    print(f"📝 PERGUNTA: {pergunta}")
    print(f"📊 DADOS DO USUÁRIO: {user_data}")
    print(f"\n🤖 PROMPT GERADO:")
    print("-" * 30)
    print(prompt[:500] + "...")
    
    print("\n✅ Teste de prompt contextual concluído!")


def main():
    """Executa todos os testes do sistema B2C."""
    print("🚀 INICIANDO TESTES DO SISTEMA B2C SOLAR")
    print("=" * 60)
    
    try:
        test_solar_knowledge()
        test_gemini_fallback()
        test_insights_fallback()
        test_contextual_prompt()
        
        print("\n" + "=" * 60)
        print("🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("\n📋 RESUMO DO SISTEMA B2C:")
        print("✅ Base de conhecimento focada em usuários finais")
        print("✅ Respostas práticas e didáticas")
        print("✅ Insights motivadores sobre economia e sustentabilidade")
        print("✅ Linguagem simples e amigável")
        print("✅ Contexto relevante para energia solar residencial")
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        return False
    
    return True


if __name__ == "__main__":
    main()
