# 🌞 SolarMind - Sistema Inteligente de Monitoramento Solar

> Release estável (fase final de refinamento) 💪

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-orange.svg)](https://sqlalchemy.org)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

Sistema inteligente para monitoramento e controle de energia solar com integração a assistentes virtuais e automação residencial.

> TL;DR Rápido:
> 1. clone repo  2. python -m venv venv & ativar  3. pip install -r requirements.txt  4. copie `.env.example` para `.env`  5. python init_db.py  6. python app.py  7. Acesse http://localhost:5000/dashboard?fonte=mock
> Para dados reais GoodWe, preencha SEMS_* no .env e use `?fonte=api`.

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
- **SOC da Bateria (Cbattery1)**: Visualização intradiária do estado de carga

## 🔌 Integração GoodWe SEMS (Dados Reais)
Para habilitar dados reais no dashboard (modo `api`), configure no `.env`:
```
SEMS_ACCOUNT=seu_email_goodwe
SEMS_PASSWORD=sua_senha_goodwe
SEMS_INV_ID=serial_inversor
SEMS_LOGIN_REGION=us   # ou eu (região para login)
SEMS_DATA_REGION=eu    # região preferida de dados (auto‑switch ocorre se diferente)
```
A aplicação tentará automaticamente alternar para a região correta se receber `code=100002`.

### Alternando entre Dados Simulados e API
O dashboard suporta dois modos:
- `mock`: dados simulados (padrão) – `http://localhost:5000/dashboard?fonte=mock`
- `api`: dados reais da GoodWe – `http://localhost:5000/dashboard?fonte=api`

No modo `api` o backend busca:
- Produção diária (coluna `eday`)
- Potência AC (`pac`)
- SOC bateria (`Cbattery1`)

Se a série vier vazia, o log mostrará linhas como:
```
[GoodWe][build_data] eday: code=0 pontos=0 | Cbattery1: code=0 pontos=0 | pac: code=0 pontos=0
```
Indicando ausência de pontos para aquele dia.

### Principais Endpoints Solares
| Endpoint | Descrição | Cache |
|----------|-----------|-------|
| `GET /api/solar/status` | Status resumido (potência, SOC, etc.) | 30s |
| `GET /api/solar/data` | Agregado produção/consumo/bateria/economia | 120s |
| `GET /api/solar/history?days=7` | Histórico últimos N dias (1–30) | 600s |
| `GET /api/solar/intraday` | (Planejado) Séries intradiárias Pac & SOC | 300s |

## 🖥️ Dashboard Atualizado (v2.1)
Visão geral dos gráficos disponíveis na versão 2.1:
- Produção diária (kWh) e potência instantânea (Pac)
- Estado de carga da bateria (SOC) intradiário
- Distribuição/Resumo (consumo x produção) – modo simulado preenche automaticamente
- Gráfico Mensal (últimos meses com dados reais ou simulação em modo mock)
- Gráfico Anual (acúmulo estimado a partir dos meses disponíveis / simulado em mock)

Notas técnicas:
- Em modo `api`, meses além da janela de varredura (atual ~90 dias) podem aparecer como 0 até implementação de agregação histórica completa
- Em modo `mock`, todos os gráficos são preenchidos para demonstrar a UI
- Logging detalhado ajuda a diferenciar série realmente vazia de valor 0 legítimo
- Datas nas consultas GoodWe usam formato `YYYY-MM-DD 00:00:00` para maior compatibilidade

To toggle real vs simulated data, use `?fonte=api` ou `?fonte=mock` na rota `/dashboard`.

Trecho de log esperado quando uma coluna retorna sem pontos:
```
[GoodWe][build_data] eday: code=0 pontos=0 | Cbattery1: code=0 pontos=0 | pac: code=0 pontos=0
```

Se aparecer `code=100002`, a aplicação tenta automaticamente alternar a região (US ↔ EU).

> Dica: Ative DEBUG apenas em desenvolvimento. Em produção use `FLASK_DEBUG=false` e configure uma SECRET_KEY forte.

---

## 🔧 Variáveis de Ambiente

Crie um arquivo `.env` (ou use variáveis diretas no ambiente) com as chaves abaixo conforme os módulos que deseja ativar.

| Categoria | Variável | Obrigatório | Default / Exemplo | Descrição |
|-----------|----------|-------------|-------------------|-----------|
| Core | `SECRET_KEY` | Produção | `dev-key-change-in-production` | Chave Flask para sessões e cookies. Use valor forte em prod |
| Core | `DATABASE_URL` | Não | `sqlite:///solarmind.db` | URL SQLAlchemy (pode usar Postgres, etc) |
| Core | `FLASK_DEBUG` | Não | `false` | Ativa modo debug |
| Scheduler | `ENABLE_SCHEDULER` | Não | `true` | Inicia jobs APScheduler |
| Scheduler | `DAILY_SUMMARY_TIME` | Não | `21:30` | Horário (HH:MM) resumo diário |
| Scheduler | `AUTOPILOT_ANNOUNCE_TIME` | Não | `08:00` | Horário anúncio Autopilot |
| Scheduler | `TIMEZONE` / `TZ` | Não | `UTC` | Fuso horário dos cron jobs |
| Scheduler | `SMARTPLUG_INTERVAL` | Se usar SmartPlug | `60` | Intervalo coleta leituras (segundos) |
| Scheduler | `ENABLE_DEVICE_SYNC` | Não | `true` | Liga/Desliga sync periódico de devices Tuya |
| Scheduler | `DEVICE_SYNC_INTERVAL` | Não | `1800` | Intervalo sync Tuya (s) |
| Autopilot | `AUTOPILOT_SOC_DEFAULT` | Não | `35` | SOC base para plano diário (fallback) |
| Autopilot | `AUTOPILOT_FORECAST_DEFAULT` | Não | `8` | Geração prevista (kWh) fallback |
| IFTTT | `IFTTT_WEBHOOK_URL` | Se usar alertas | - | URL base Webhooks IFTTT |
| IFTTT | `IFTTT_KEY` | Se usar alertas | - | Key do serviço Webhooks |
| IA (Gemini) | `ENABLE_GEMINI` | Não | `true` | Liga/desliga recursos IA |
| IA (Gemini) | `GEMINI_API_KEY` | Se IA ativa | - | API Key Google Gemini |
| IA (Gemini) | `GEMINI_MODEL` | Não | `gemini-1.5-flash` | Modelo usado |
| IA (Gemini) | `GEMINI_TIMEOUT` | Não | `30` | Timeout requisições (s) |
| IA (Gemini) | `GEMINI_MAX_TOKENS` | Não | `1000` | Limite tokens saída |
| GoodWe | `SEMS_ACCOUNT` | Para dados reais | - | Email conta GoodWe |
| GoodWe | `SEMS_PASSWORD` | Para dados reais | - | Senha conta GoodWe |
| GoodWe | `SEMS_INV_ID` | Para dados reais | - | Serial do inversor |
| GoodWe | `SEMS_LOGIN_REGION` | Não | `us` | Região login inicial (us/eu) |
| GoodWe | `SEMS_DATA_REGION` | Não | `us` | Região preferida dados (auto-switch se necessário) |
| Tuya | `TUYA_ACCESS_ID` | Para SmartPlug | - | Credencial Tuya Cloud |
| Tuya | `TUYA_ACCESS_SECRET` | Para SmartPlug | - | Credencial Tuya Cloud |
| Tuya | `TUYA_ENDPOINT` | Não | `https://openapi.tuyaus.com` | Endpoint região |
| Tuya | `TUYA_DEVICE_ID` | Para SmartPlug | - | ID do dispositivo |
| Tuya | `TUYA_USER_ID` | Opcional | - | Usado em fallback listagem |
| Tuya | `TUYA_REGION` | Opcional | - | Região lógica adicional |

Exemplo mínimo (.env):
```
SECRET_KEY=troque-para-uma-chave-forte
FLASK_DEBUG=true
DATABASE_URL=sqlite:///instance/solarmind.db

# GoodWe (modo api)
SEMS_ACCOUNT=seu_email
SEMS_PASSWORD=sua_senha
SEMS_INV_ID=serial
SEMS_LOGIN_REGION=us
SEMS_DATA_REGION=eu

# Gemini
ENABLE_GEMINI=true
GEMINI_API_KEY=sua_api_key

# IFTTT
IFTTT_WEBHOOK_URL=https://maker.ifttt.com/trigger/
IFTTT_KEY=xxxxxx
```

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

### v2.1.0 (2025-10-04) - Dashboard Solar Refinado
- 🔧 Datas padronizadas com hora para consultas GoodWe (`YYYY-MM-DD 00:00:00`)
- � Gráfico SOC usando timestamps reais da série `Cbattery1`
- 📊 Gráficos Mensal e Anual REINTRODUZIDOS com agregação (API) ou simulação (mock)
- 🎛️ Modo mock agora preenche todos os gráficos (incluindo mensal/anual) sem chamadas externas
- 🛡️ Logging de diagnóstico para identificar séries vazias e códigos 100002 (auto-switch região)
- � Injeção unificada de dados no template (reduz scripts duplicados)
- 🧪 Base para diferenciar “sem dados” de zero legítimo (próxima melhoria visual)

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

## 🚀 Deploy em Produção

Opções suportadas / testadas:

### 1. Gunicorn (Linux)
```
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
Adicionar variável `FLASK_DEBUG=false` e SECRET_KEY forte.

### 2. Docker
```
docker build -t solarmind:2.1 .
docker run -d --env-file .env -p 8000:5000 --name solarmind solarmind:2.1
```

### 3. Docker Compose
```
docker compose up -d
```
(Ver arquivo `docker-compose.yml` se presente; ajuste volumes para persistir `instance/`.)

### 4. Render / Railway / Heroku-like
Use o `Procfile` (exemplo):
```
web: gunicorn app:app --workers=4 --timeout=120 --log-level=info
```

### Hardening / Boas Práticas
- SECRET_KEY forte (>= 32 chars) e nunca commitar `.env`
- Desabilitar `FLASK_DEBUG` em produção
- HTTPS (proxy reverso Nginx / Traefik)
- Limitar origem se expor API publicamente (ex: configurar CORS seletivo)
- Logs: enviar para stdout e coletar via stack (ELK / Loki) se necessário
- Monitorar jobs do scheduler (desabilitar se não precisar: `ENABLE_SCHEDULER=false`)
- Backups do banco: copiar `instance/solarmind.db`

### Escalabilidade (roadmap)
- Migrar para Postgres alterando `DATABASE_URL`
- Adicionar cache Redis para respostas de API GoodWe
- Separar worker de scheduler em container distinto

---
- Comunidade Flask pela excelente documentação
- IFTTT pela plataforma de automação

---

<div align="center">
  <p>Feito com ❤️ para um futuro mais sustentável</p>
  <p>⭐ Se este projeto te ajudou, considere dar uma estrela!</p>
</div>
