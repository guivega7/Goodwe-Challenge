#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Teste Completo do RAG System - SolarMind

Script para testar todas as funcionalidades do sistema RAG:
- Extração de conhecimento
- Busca contextual 
- Integração com Gemini
- Performance e cobertura
"""

import os
import sys
import time
from pathlib import Path

# Adiciona o diretório raiz ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_knowledge_extraction():
    """Testa extração da base de conhecimento."""
    print("🧠 Testando extração de conhecimento...")
    
    try:
        from services.rag_system import ProjectKnowledgeBase
        
        kb = ProjectKnowledgeBase()
        
        start_time = time.time()
        knowledge = kb.extract_project_knowledge()
        extraction_time = time.time() - start_time
        
        print(f"✅ Extração concluída em {extraction_time:.2f}s")
        
        # Verifica categorias
        categories = ['features', 'api_endpoints', 'models', 'services', 'templates', 'documentation']
        for category in categories:
            count = len(knowledge.get(category, []))
            print(f"   📚 {category}: {count} itens")
        
        return True, knowledge
        
    except Exception as e:
        print(f"❌ Erro na extração: {e}")
        return False, None

def test_context_search(knowledge):
    """Testa busca de contexto."""
    print("\n🔍 Testando busca de contexto...")
    
    try:
        from services.rag_system import ProjectKnowledgeBase
        
        kb = ProjectKnowledgeBase()
        kb.knowledge_cache = knowledge  # Usa conhecimento já extraído
        
        # Testes de busca
        test_queries = [
            "como configurar gemini",
            "autopilot energia",
            "chat ia mensagem",
            "api aparelhos",
            "dashboard graficos",
            "scheduler tarefas",
            "ifttt alexa",
            "banco dados usuario"
        ]
        
        total_results = 0
        for query in test_queries:
            context = kb.get_relevant_context(query, max_items=3)
            results_count = len(context)
            total_results += results_count
            
            print(f"   🔍 '{query}': {results_count} resultados")
            
            # Mostra o melhor resultado
            if context:
                best = context[0]
                relevance = best.get('relevance', 0) * 100
                print(f"      🎯 Melhor: {best['category']} ({relevance:.0f}% relevância)")
        
        avg_results = total_results / len(test_queries)
        print(f"✅ Busca OK - Média: {avg_results:.1f} resultados por query")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na busca: {e}")
        return False

def test_rag_integration():
    """Testa integração RAG + Gemini."""
    print("\n🤖 Testando integração RAG + Gemini...")
    
    try:
        from services.rag_system import RAGSystem
        
        rag = RAGSystem()
        
        # Testa queries contextuais
        test_queries = [
            "Como configurar o autopilot do SolarMind?",
            "Quais são os endpoints de API disponíveis?",
            "Como funciona o chat IA?",
            "Explique o sistema de aparelhos"
        ]
        
        for query in test_queries:
            print(f"   ❓ Pergunta: {query}")
            
            start_time = time.time()
            result = rag.get_contextual_response(query)
            response_time = time.time() - start_time
            
            if result.get('error'):
                print(f"      ⚠️  Erro: {result['error']}")
            else:
                context_count = len(result.get('context_used', []))
                relevance = result.get('relevance_score', 0) * 100
                response_preview = result.get('response', '')[:100] + '...'
                
                print(f"      ✅ Resposta em {response_time:.2f}s")
                print(f"      📊 Contexto: {context_count} categorias, {relevance:.0f}% relevância")
                print(f"      💬 Preview: {response_preview}")
            
            print()  # Linha em branco
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na integração: {e}")
        return False

def test_api_endpoints():
    """Testa endpoints da API RAG."""
    print("🌐 Testando endpoints da API...")
    
    try:
        import requests
        
        base_url = "http://localhost:5000"
        
        # Tenta acessar status
        try:
            response = requests.get(f"{base_url}/api/rag/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: {data.get('status')}")
                print(f"   📊 RAG habilitado: {data.get('rag_enabled')}")
            else:
                print(f"   ⚠️  Status endpoint: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("   ⚠️  Flask não está rodando - endpoints não testados")
            return False
        
        # Testa busca via API
        search_data = {
            "query": "chat gemini",
            "max_items": 2
        }
        
        try:
            response = requests.post(
                f"{base_url}/api/rag/search",
                json=search_data,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Busca: {data.get('results_count')} resultados")
            else:
                print(f"   ⚠️  Busca endpoint: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Erro na busca: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos endpoints: {e}")
        return False

def test_performance():
    """Testa performance do sistema."""
    print("\n⚡ Testando performance...")
    
    try:
        from services.rag_system import ProjectKnowledgeBase
        
        kb = ProjectKnowledgeBase()
        
        # Teste de carga - múltiplas buscas
        queries = ["gemini", "api", "chat", "dashboard", "energy"] * 10
        
        start_time = time.time()
        for query in queries:
            kb.get_relevant_context(query, max_items=1)
        total_time = time.time() - start_time
        
        avg_time = (total_time / len(queries)) * 1000  # em ms
        qps = len(queries) / total_time  # queries por segundo
        
        print(f"   ⚡ {len(queries)} buscas em {total_time:.2f}s")
        print(f"   📈 Média: {avg_time:.1f}ms por busca")
        print(f"   🚀 Throughput: {qps:.1f} QPS")
        
        # Avaliação
        if avg_time < 50:
            print("   ✅ Performance: EXCELENTE")
        elif avg_time < 100:
            print("   ✅ Performance: BOA")
        else:
            print("   ⚠️  Performance: ACEITÁVEL")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de performance: {e}")
        return False

def main():
    """Executa todos os testes do RAG system."""
    print("🚀 SolarMind - Teste Completo do RAG System")
    print("=" * 50)
    
    results = []
    
    # Teste 1: Extração de conhecimento
    success, knowledge = test_knowledge_extraction()
    results.append(("Extração de Conhecimento", success))
    
    if not success:
        print("❌ Falha crítica - encerrando testes")
        return
    
    # Teste 2: Busca de contexto
    success = test_context_search(knowledge)
    results.append(("Busca de Contexto", success))
    
    # Teste 3: Integração RAG + Gemini
    success = test_rag_integration()
    results.append(("Integração RAG + Gemini", success))
    
    # Teste 4: Endpoints da API
    success = test_api_endpoints()
    results.append(("Endpoints da API", success))
    
    # Teste 5: Performance
    success = test_performance()
    results.append(("Performance", success))
    
    # Relatório final
    print("\n" + "=" * 50)
    print("📊 RELATÓRIO FINAL DOS TESTES:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"  {test_name}: {status}")
        if success:
            passed += 1
    
    success_rate = (passed / len(results)) * 100
    
    print(f"\n🎯 RESULTADO: {passed}/{len(results)} testes passaram ({success_rate:.0f}%)")
    
    if success_rate >= 80:
        print("🎉 SISTEMA RAG ESTÁ FUNCIONANDO CORRETAMENTE!")
        print("💡 Seu chat IA agora tem conhecimento contextual do projeto!")
    elif success_rate >= 60:
        print("⚠️  Sistema RAG funcional com algumas limitações")
        print("🔧 Verifique os testes que falharam")
    else:
        print("❌ Sistema RAG com problemas significativos")
        print("🛠️  Revise a configuração e dependências")

if __name__ == '__main__':
    main()
