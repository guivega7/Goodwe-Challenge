#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Teste de Configuração do Gemini AI - SolarMind

Execute este script para verificar se sua API key está funcionando.
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_env_file():
    """Testa se o arquivo .env existe e tem a API key."""
    print("🔍 Verificando arquivo .env...")
    
    env_file = project_root / '.env'
    if not env_file.exists():
        print("❌ Arquivo .env não encontrado!")
        print("💡 Copie .env.example para .env e configure sua API key")
        return False
    
    # Lê o .env
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'GEMINI_API_KEY=' in content:
            # Verifica se não é o valor placeholder
            if 'your-gemini-api-key-here' in content:
                print("❌ API key ainda não foi configurada!")
                print("💡 Substitua 'your-gemini-api-key-here' pela sua API key real")
                return False
            else:
                print("✅ Arquivo .env configurado!")
                return True
        else:
            print("❌ GEMINI_API_KEY não encontrada no .env")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao ler .env: {e}")
        return False

def test_gemini_client():
    """Testa a conexão com o Gemini."""
    print("\n🤖 Testando conexão com Gemini...")
    
    try:
        # Carrega variáveis de ambiente do .env
        from dotenv import load_dotenv
        load_dotenv()
        
        # Importa o cliente
        from services.gemini_client import GeminiClient
        
        client = GeminiClient()
        
        # Verifica se está habilitado
        if not client.is_enabled():
            print("❌ Gemini não está habilitado ou configurado")
            print("💡 Verifique GEMINI_API_KEY e ENABLE_GEMINI no .env")
            return False
        
        # Testa conexão
        result = client.test_connection()
        
        if result['status'] == 'success':
            print("✅ Conexão com Gemini funcionando!")
            print(f"📝 Teste: {result.get('test_response', 'OK')}")
            return True
        else:
            print(f"❌ Erro na conexão: {result.get('message', 'Desconhecido')}")
            return False
            
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("💡 Execute: pip install python-dotenv google-generativeai")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_flask_endpoint():
    """Testa o endpoint da API Flask."""
    print("\n🌐 Testando endpoint Flask...")
    
    try:
        import requests
        
        # Testa se o Flask está rodando
        try:
            response = requests.get('http://localhost:5000/api/gemini/test', timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    print("✅ Endpoint Flask funcionando!")
                    return True
                else:
                    print(f"❌ Endpoint retornou erro: {result.get('message')}")
                    return False
            else:
                print(f"❌ Endpoint retornou status {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("⚠️  Flask não está rodando")
            print("💡 Execute: python app.py")
            return False
            
    except ImportError:
        print("❌ Biblioteca 'requests' não encontrada")
        print("💡 Execute: pip install requests")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def main():
    """Executa todos os testes."""
    print("🚀 SolarMind - Teste de Configuração Gemini AI")
    print("=" * 50)
    
    tests = [
        test_env_file,
        test_gemini_client,
        test_flask_endpoint
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except KeyboardInterrupt:
            print("\n⚡ Teste interrompido pelo usuário")
            sys.exit(1)
        except Exception as e:
            print(f"💥 Erro crítico: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 RESULTADO DOS TESTES:")
    
    test_names = ["Arquivo .env", "Cliente Gemini", "Endpoint Flask"]
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {i+1}. {name}: {status}")
    
    if all(results):
        print("\n🎉 TUDO FUNCIONANDO! Seu Gemini AI está pronto!")
        print("💡 Agora você pode usar o chat e gerar insights no dashboard")
    else:
        print("\n⚠️  Alguns testes falharam. Verifique a configuração.")
        print("📖 Leia o GEMINI_SETUP.md para instruções detalhadas")

if __name__ == '__main__':
    main()
