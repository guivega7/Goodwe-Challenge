# 🌞 SolarMind - Sistema Inteligente de Monitoramento Solar

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-orange.svg)](https://sqlalchemy.org)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

Sistema inteligente para monitoramento e controle de energia solar com integração a assistentes virtuais e automação residencial.

## 🚀 Funcionalidades Principais

### 🏠 Automação Residencial
- **Controle Inteligente**: Controle de aparelhos via API REST
- **Monitoramento de Consumo**: Acompanhamento em tempo real do consumo energético
- **Otimização Automática**: Sugestões inteligentes para economia de energia

### 🤖 Integração com Assistentes Virtuais
- **Amazon Alexa**: Comandos de voz via IFTTT
- **Google Home**: Automação integrada
- **Webhooks IFTTT**: Triggers automáticos baseados em eventos

### 📊 Inteligência Artificial
- **Gemini AI**: Chat inteligente e geração de insights personalizados
- **Análise Preditiva**: Previsão de consumo baseada em padrões históricos
- **Aprendizado de Máquina**: Identificação automática de padrões de uso
- **Alertas Inteligentes**: Notificações proativas sobre manutenção e consumo
- **Chat IA**: Assistente virtual especializado em energia solar
- **Insights Automáticos**: Relatórios inteligentes gerados por IA

### ⚡ Monitoramento Solar
- **Status do Sistema**: Monitoramento em tempo real do sistema fotovoltaico
- **Alertas de Manutenção**: Notificações preventivas
- **Análise de Eficiência**: Relatórios detalhados de performance

## 🛠️ Tecnologias Utilizadas

### Backend
- **Flask**: Framework web Python
- **SQLAlchemy**: ORM para banco de dados
- **SQLite**: Banco de dados local
- **Python 3.8+**: Linguagem principal
- **APScheduler**: Agendamento de tarefas automáticas
- **Flask-Login**: Sistema de autenticação profissional

### Inteligência Artificial
- **Google Gemini**: IA generativa para insights e chat
- **RAG System**: Conhecimento contextual do projeto
- **NLP**: Processamento de linguagem natural

### Frontend
- **HTML5/CSS3**: Interface web responsiva
- **Bootstrap**: Framework CSS
- **JavaScript**: Interatividade dinâmica

### Integrações
- **IFTTT**: Automação e integração com assistentes
- **Webhooks**: Comunicação em tempo real
- **API REST**: Endpoints para integração externa

## 📁 Estrutura do Projeto

```
solarmind/
├── 📁 models/              # Modelos de dados (SQLAlchemy)
│   ├── aparelho.py         # Modelo de aparelhos
│   ├── usuario.py          # Modelo de usuários
│   └── __init__.py
├── 📁 routes/              # Rotas da aplicação (Blueprints)
│   ├── api.py             # API REST principal
│   ├── auth.py            # Autenticação
│   ├── dashboard.py       # Dashboard web
│   ├── aparelhos.py       # Gestão de aparelhos
│   ├── estatisticas.py    # Relatórios e gráficos
│   ├── main.py            # Páginas principais
│   └── alexa.py           # Integração Alexa
├── 📁 services/           # Serviços e lógica de negócio
│   ├── automacao.py       # Automação residencial
│   ├── goodwe_client.py   # Cliente API GoodWe
│   ├── tuya_client.py     # Integração tomada inteligente (Tuya)
│   └── simula_evento.py   # Simulador de eventos
├── 📁 utils/              # Utilitários
│   ├── energia.py         # Funções de energia
│   ├── previsao.py        # Algoritmos de previsão
│   ├── logger.py          # Sistema de logs
│   └── errors.py          # Tratamento de erros
├── 📁 templates/          # Templates HTML
├── 📁 static/            # Arquivos estáticos (CSS, JS, imagens)
├── app.py                # Aplicação principal
├── config.py             # Configurações
├── extensions.py         # Extensões Flask
├── requirements.txt      # Dependências Python
└── README.md            # Documentação
```

## 🚀 Instalação e Configuração

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Git

### Passo a Passo

1. **Clone o repositório**
   ```bash
   git clone https://github.com/guivega7/Goodwe-Challenge.git
   cd Goodwe-Challenge
   ```

2. **Crie um ambiente virtual**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente**
   ```bash
   # Copie o arquivo de exemplo
   copy .env.example .env
   
   # Edite o .env com suas configurações
   SECRET_KEY=sua-chave-secreta-super-segura
   FLASK_DEBUG=True
   DATABASE_URL=sqlite:///instance/solarmind.db
   
   # Para usar IA, configure sua API key do Gemini (GRATUITA):
   GEMINI_API_KEY=sua-api-key-aqui
   ENABLE_GEMINI=true
   ```

   **🤖 Para configurar o Gemini AI:**
   1. Acesse: https://makersuite.google.com/app/apikey
   2. Crie uma API key gratuita
   3. Cole no arquivo `.env`
   4. Veja instruções detalhadas em: [GEMINI_SETUP.md](GEMINI_SETUP.md)
   IFTTT_WEBHOOK_URL=https://maker.ifttt.com/trigger/
   IFTTT_KEY=sua-chave-ifttt
   ```

5. **Inicialize o banco de dados**
   ```bash
   python init_db.py
   ```

6. **Execute a aplicação**
   ```bash
   python app.py
   ```

A aplicação estará disponível em `http://localhost:5000`

## 📚 API Documentation

### Endpoints Principais

#### 🔌 Status da API
```http
GET /api/status
```
Retorna o status de funcionamento da API.

#### 🏠 Controle de Aparelhos
```http
POST /ifttt/desligar
Content-Type: application/json

{
  "value1": "nome_do_aparelho"
}
```

#### 📊 Alertas do Sistema
```http
POST /api/alertas/low_battery
Content-Type: application/json

{
  "soc": 15
}
```

#### 🤖 IA - Previsão de Consumo
```http
GET /api/ia/previsao_consumo
```

#### 🔧 Automação Residencial
```http
POST /api/automacao/aparelhos/{id}/toggle
Content-Type: application/json

{
  "acao": "desligar"
}
```

### 🔌 Tomada Inteligente (Tuya)

Integração com tomada inteligente compatível com Tuya para capturar status e (quando suportado) métricas de energia.

#### Endpoints
```http
GET /api/smartplug/status
GET /api/smartplug/energy
GET /api/smartplug/readings?limit=100
GET /api/smartplug/summary
```

Exemplo de resposta `/api/smartplug/status`:
```json
{
   "ok": true,
   "data": {
      "device_id": "xxxx",
      "status": {...},
      "energy": {...},
      "timestamp": 1730000000
   },
   "fonte": "TUYA_API"
}
```

#### Configuração
Adicione ao `.env` (NÃO COMMITAR credenciais reais):
```
TUYA_ACCESS_ID=seu_access_id
TUYA_ACCESS_SECRET=seu_access_secret
TUYA_ENDPOINT=https://openapi.tuyaus.com
TUYA_DEVICE_ID=seu_device_id
```

Descobrir o `DEVICE_ID`: Painel Tuya > Cloud > Linked Devices.

Observação: Alguns dispositivos não expõem todas as métricas de energia via OpenAPI sem habilitar permissões extras no projeto Tuya Cloud (ex: Energy API / Electricity).

#### Coleta Automática
Um job do scheduler coleta leituras periódicas (default: a cada 60s) e salva em `smartplug_readings`.

Configurar intervalo no `.env`:
```
SMARTPLUG_INTERVAL=60  # segundos (coloque 0 ou remova para desativar)
```

Endpoints adicionais:
- `/api/smartplug/readings` retorna últimas leituras persistidas
- `/api/smartplug/summary` retorna agregados (médias/máximos)

Tabela criada automaticamente via `db.create_all()` se o modelo estiver importado no startup.

## 🤖 Inteligência Artificial

### Chat IA
Converse com o assistente virtual especializado em energia solar:
```http
POST /chat/send
Content-Type: application/json

{
  "message": "Como posso melhorar minha eficiência energética?"
}
```

### Insights Inteligentes
Gere análises personalizadas dos seus dados:
```http
POST /api/ia/insights
Content-Type: application/json

{
  "energia_gerada": 25.5,
  "energia_consumida": 18.2,
  "soc_bateria": 85,
  "periodo": "hoje"
}
```

### Teste de Configuração
Verifique se sua API key do Gemini está funcionando:
```bash
# Teste direto via endpoint
GET /api/gemini/test

# Ou use o script de teste
python test_gemini.py
```

### Funcionalidades IA Disponíveis
- 💬 **Chat Inteligente**: Perguntas sobre energia solar e otimização
- 📊 **Insights Personalizados**: Análises baseadas nos seus dados reais
- 📅 **Resumos Automáticos**: Relatórios diários às 21:30
- 🌅 **Anúncios Matinais**: Alertas inteligentes às 08:00
- 📈 **Análise de Tendências**: Identificação de padrões de consumo

## 🔧 Configuração IFTTT

### Alexa Integration

1. **Crie uma conta no IFTTT**
2. **Configure o webhook:**
   - URL: `http://seu-servidor.com/ifttt/desligar`
   - Método: POST
   - Body: `{"value1": "{{TextField}}"}`

3. **Configure o trigger da Alexa:**
   - "Alexa, trigger desligar ventilador"

### Google Home Integration

Similar ao Alexa, mas usando o serviço Google Assistant no IFTTT.

## 🤝 Contribuindo

1. **Fork o projeto**
2. **Crie uma branch para sua feature** (`git checkout -b feature/AmazingFeature`)
3. **Commit suas mudanças** (`git commit -m 'Add some AmazingFeature'`)
4. **Push para a branch** (`git push origin feature/AmazingFeature`)
5. **Abra um Pull Request**

## 📋 Roadmap

- [x] **Dashboard Avançado**: Gráficos interativos com Chart.js ✅
- [x] **Integração IA**: Google Gemini para insights e chat ✅  
- [x] **Scheduler Automático**: Tarefas agendadas com APScheduler ✅
- [x] **Flask-Login**: Sistema de autenticação profissional ✅
- [ ] **RAG System**: Chat com conhecimento específico do projeto
- [ ] **App Mobile**: Aplicativo React Native
- [ ] **ML Avançado**: Modelos TensorFlow para previsão
- [ ] **IoT Integration**: Suporte a dispositivos IoT
- [ ] **Cloud Deploy**: Deploy automático na AWS/Azure
- [ ] **API GraphQL**: Endpoint GraphQL para queries flexíveis

## 🛡️ Segurança

- **Autenticação**: Sistema de login com hash de senhas
- **Validação**: Validação de inputs em todas as rotas
- **HTTPS**: Recomendado para produção
- **Rate Limiting**: Implementar em produção

## 📝 Changelog

### v2.0.0 (2025-09-09) - IA INTEGRATION 🤖
- ✨ **Gemini AI**: Chat inteligente e geração de insights
- 🕒 **APScheduler**: Resumos diários automáticos (21:30) e anúncios matinais (08:00)  
- 🔐 **Flask-Login**: Sistema de autenticação profissional com UserMixin
- 💬 **Chat IA**: Interface de conversação com histórico persistente
- 📊 **Insights Dashboard**: Card de IA no dashboard com geração on-demand
- 🗃️ **ChatMessage Model**: Persistência de conversas no SQLite
- 🧪 **Script de Teste**: Verificação automática de configuração do Gemini
- 📚 **Documentação IA**: Guia completo de setup em GEMINI_SETUP.md

### v1.0.0 (2024-12-07) - FOUNDATION 🏗️
- ✨ Integração completa com IFTTT e Alexa
- 🤖 Sistema de IA para previsão de consumo
- 🏠 Automação residencial inteligente
- 📊 Dashboard web responsivo
- 🔒 Sistema de autenticação
- 📱 API REST completa

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👥 Autores

- **Guilherme Vega** - *Desenvolvimento inicial* - [@guivega7](https://github.com/guivega7)

## 🙏 Agradecimentos

- FIAP - Faculdade de Informática e Administração Paulista
- GoodWe - Inspiração para o projeto
- Comunidade Flask pela excelente documentação
- IFTTT pela plataforma de automação

---

<div align="center">
  <p>Feito com ❤️ para um futuro mais sustentável</p>
  <p>⭐ Se este projeto te ajudou, considere dar uma estrela!</p>
</div>
