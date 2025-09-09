# 🤖 Configuração do Gemini AI - SolarMind

## 🚀 Como obter sua API Key GRATUITA

### Passo 1: Acesse o Google AI Studio
- Vá para: https://makersuite.google.com/app/apikey
- Faça login com sua conta Google

### Passo 2: Crie sua API Key
1. Clique em **"Create API Key"**
2. Escolha **"Create API key in new project"** (recomendado)
3. Copie a key gerada (algo como: `AIzaSy...`)

### Passo 3: Configure no projeto
1. Copie o arquivo `.env.example` para `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edite o arquivo `.env` e substitua:
   ```bash
   GEMINI_API_KEY=your-gemini-api-key-here
   ```
   Por:
   ```bash
   GEMINI_API_KEY=AIzaSy_sua_key_aqui
   ```

## 🔧 Funcionalidades Disponíveis

### 💡 Insights Inteligentes
- **Dashboard**: Clique em "Gerar Insights" no card de IA
- **Análise**: Gemini analisa seus dados e gera insights personalizados
- **Contexto**: Considera histórico, clima, padrões de consumo

### 💬 Chat Inteligente
- **Acesso**: Menu "Chat IA" na navbar
- **Perguntas**: Faça perguntas sobre energia solar, seu sistema, eficiência
- **Exemplos**: 
  - "Como melhorar minha eficiência energética?"
  - "Qual o melhor horário para usar meus aparelhos?"
  - "Explique meus dados de hoje"

### 📊 Análises Automáticas
- **Resumo Diário**: Todo dia às 21:30
- **Autopilot Matinal**: Todo dia às 08:00
- **Alertas Inteligentes**: Via IFTTT quando necessário

## 🛡️ Segurança

### API Key
- ✅ **Gratuita**: Gemini oferece cota generosa grátis
- ✅ **Segura**: Sua key fica apenas no seu `.env` local
- ✅ **Privada**: Não é commitada no GitHub

### Dados
- ✅ **Locais**: Seus dados ficam no seu SQLite
- ✅ **Contextuais**: Gemini só recebe dados necessários para análise
- ✅ **Temporários**: Não armazenamos dados no Google

## 🚨 Solução de Problemas

### Chat não funciona?
1. Verifique se `GEMINI_API_KEY` está configurada no `.env`
2. Confirme se `ENABLE_GEMINI=true` no `.env`
3. Veja os logs no terminal se há erros de API

### Insights não geram?
1. Teste a API: http://localhost:5000/api/gemini/test
2. Verifique sua cota na Google AI Console
3. Certifique-se que tem dados de energia no sistema

### Erro de permissão?
- A API key pode ter restrições geográficas
- Tente criar uma nova key no Google AI Studio

## 📈 Limites da API Gratuita

| Recurso | Limite Gratuito |
|---------|----------------|
| Requests/minuto | 15 |
| Requests/dia | 1.500 |
| Tokens/request | 32.000 |

**💡 Dica**: Para uso pessoal, os limites gratuitos são mais que suficientes!

## 🔮 Próximas Features

- [ ] **RAG System**: Chat baseado em conhecimento do projeto
- [ ] **Análise de Tendências**: Previsões baseadas em histórico
- [ ] **Relatórios Automáticos**: PDFs com insights semanais/mensais
- [ ] **Integração Alexa**: Perguntas por voz via IFTTT

---

**🎯 Agora é só configurar sua API key e aproveitar a IA integrada no seu sistema solar!**
