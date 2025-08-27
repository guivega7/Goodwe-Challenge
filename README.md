# 🌞 SolarMind - Dashboard GoodWe com Integração Alexa

> **Challenge FIAP - Automação Inteligente de Energia Solar**  
> Sistema completo de monitoramento solar com alertas automáticos via Alexa e validação inteligente de inversores.

## 🚀 Funcionalidades Principais

### 📊 **Dashboard Inteligente**
- **Monitoramento em tempo real**: Potência instantânea, energia diária, SOC da bateria
- **Validação automática**: Reconhece padrões válidos de números de série GoodWe
- **Multi-região**: Suporte para servidores US e EU do SEMS Portal
- **Fallback inteligente**: Dados simulados quando API não está disponível

### 🎙️ **Integração Alexa (IFTTT)**
- **Alertas automáticos**: Bateria baixa (<20%) e falhas do inversor
- **Webhooks configurados**: Sistema funcional com Voice Monkey
- **Notificações contextuais**: Mensagens personalizadas baseadas nos dados

### 🔧 **Sistema de Validação**
- **Padrões GoodWe**: Reconhece formatos oficiais de números de série
- **Feedback visual**: Indicadores coloridos para status dos dados
- **Tratamento de erros**: Diferencia entre SN inválido vs. sem acesso à API

## 📋 Pré-requisitos

- Python 3.8+
- Conta GoodWe SEMS Portal (opcional para dados reais)
- Conta IFTTT + Alexa (para alertas de voz)

## ⚡ Instalação Rápida

### 1. **Clone e Configure o Ambiente**
```bash
git clone https://github.com/guivega7/Goodwe-Challenge.git
cd "Challenge GoodWe"
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. **Configure as Credenciais**

Edite o arquivo `.env` com suas credenciais:

```properties
# Configuração do Banco
DATABASE_URL=sqlite:///solarmind.db
SECRET_KEY=sua_chave_secreta_aqui

# === CONFIGURAÇÃO GOODWE SEMS ===
# Separação de regiões conforme orientação do professor
SEMS_LOGIN_REGION=us     # Região para login (us.semsportal.com)
SEMS_DATA_REGION=eu      # Região para buscar dados (eu.semsportal.com)

# Suas credenciais reais do SEMS Portal
SEMS_ACCOUNT=seu_email@exemplo.com
SEMS_PASSWORD=sua_senha_real
SEMS_INV_ID=75000ESN333WV001  # Número de série do seu inversor

# === INTEGRAÇÃO ALEXA (IFTTT) ===
IFTTT_KEY=sua_chave_ifttt
WEBHOOK_LOW_BATTERY=https://maker.ifttt.com/trigger/low_battery/with/key/SUA_CHAVE
WEBHOOK_FALHA_INVERSOR=https://maker.ifttt.com/trigger/falha_inversor/with/key/SUA_CHAVE
```

### 3. **Inicialize o Banco de Dados**
```bash
python init_db.py
```

### 4. **Execute a Aplicação**
```bash
python app.py
```

Acesse: **http://127.0.0.1:5000**

## 🎯 Como Usar o Dashboard

### **Controles da Interface:**

1. **Selector de Fonte de Dados**:
   - 🔵 **"Dados Simulados"** - Sempre funciona com dados fictícios
   - 🔗 **"GoodWe SEMS API"** - Tenta usar dados reais do inversor

2. **Campo Número de Série**:
   - Aparece quando seleciona "API"
   - Digite o SN do seu inversor (ex: `75000ESN333WV001`)

3. **Botão "Atualizar Dados"**:
   - Aplica as configurações selecionadas

### **Indicadores de Status:**
- 🔵 **Azul**: Dados simulados (desenvolvimento/teste)
- 🟡 **Amarelo**: SN válido, mas sem acesso à API 
- 🟢 **Verde**: Dados reais da API GoodWe
- 🔴 **Vermelho**: Erro (SN inválido ou falha crítica)

## 🧪 Testando o Sistema

### **Números de Série para Teste:**

#### ✅ **Padrões Válidos** (mostram dados simulados com aviso):
```
75000ESN333WV001    # Formato principal GoodWe
GW123456789ABC      # Com prefixo GW  
1234567890123       # Apenas números (13+ dígitos)
AB123456789         # Prefixo alfabético + números
```

#### ❌ **Padrões Inválidos** (mostram erro):
```
INVALID_123         # Formato não reconhecido
ABC                 # Muito curto
12345               # Poucos dígitos
```

### **Modos de Operação:**

| Situação | Comportamento |
|----------|---------------|
| **Sem credenciais + SN válido** | Dados simulados + aviso "sem acesso" |
| **Sem credenciais + SN inválido** | Erro de formato |
| **Com credenciais + SN correto** | Dados reais da API |
| **Com credenciais + SN incorreto** | Erro real da API |
| **Dados simulados** | Sempre funciona |

## 🔊 Configuração Alexa + IFTTT

### **1. Configure os Webhooks IFTTT:**

1. Acesse [IFTTT.com](https://ifttt.com) e faça login
2. Crie um novo Applet:
   - **IF**: Webhooks → Receive web request
   - **Event Name**: `low_battery`
   - **THEN**: Voice Monkey → Say a phrase
   - **Phrase**: "Atenção! Bateria do sistema solar está baixa: {{Value1}}"

3. Repita para `falha_inversor`:
   - **Phrase**: "Alerta! {{Value1}}"

### **2. Obtenha sua chave IFTTT:**
- Acesse: https://maker.ifttt.com/use/
- Copie sua chave e adicione no `.env`

### **3. Teste os Alertas:**
Os alertas são disparados automaticamente quando:
- **Bateria < 20%**: Trigger `low_battery`
- **Potência baixa durante o dia**: Trigger `falha_inversor`

## 🏗️ Arquitetura do Sistema

```
SolarMind/
├── 📱 app.py                    # Aplicação Flask principal
├── ⚙️  config.py                # Configurações
├── 🔗 extensions.py             # Extensões (SQLAlchemy)
├── 🗃️  init_db.py               # Inicialização do banco
├── 📊 models/                   # Modelos do banco de dados
│   ├── usuario.py              # Modelo de usuário
│   └── aparelho.py             # Modelo de aparelhos
├── 🛣️  routes/                  # Rotas da aplicação
│   ├── auth.py                 # Autenticação e registro
│   ├── dashboard.py            # Dashboard principal
│   ├── main.py                 # Página inicial
│   ├── api.py                  # Endpoints da API
│   ├── aparelhos.py            # Gestão de aparelhos
│   └── estatisticas.py         # Estatísticas e relatórios
├── 🛠️  services/                # Serviços e integrações
│   ├── goodwe_client.py        # Cliente da API GoodWe SEMS
│   ├── simula_evento.py        # Geração de dados simulados
│   └── automacao.py            # Automação e alertas
├── 🎨 templates/                # Templates HTML
│   ├── base.html               # Template base
│   ├── dashboard.html          # Interface do dashboard
│   ├── login.html              # Página de login
│   └── ...                     # Outros templates
├── 📦 utils/                    # Utilitários
│   ├── energia.py              # Cálculos de energia
│   ├── logger.py               # Sistema de logs
│   └── previsao.py             # Previsões e análises
└── 🎯 static/                   # Arquivos estáticos
    ├── css/                    # Estilos CSS
    ├── js/                     # JavaScript
    └── images/                 # Imagens e ícones
```

## 🚨 Resolução de Problemas

### **❌ "No access, please log in"**
- **Causa**: Token sem permissões ou credenciais incorretas
- **Solução**: Configure `SEMS_ACCOUNT` e `SEMS_PASSWORD` reais no `.env`

### **❌ "Formato de SN inválido"**
- **Causa**: Número de série não segue padrões GoodWe
- **Solução**: Use um SN válido ou ative modo simulado

### **❌ "API não responde"**
- **Causa**: Servidor SEMS indisponível
- **Solução**: Sistema usa fallback automático para dados simulados

### **❌ "Alexa não fala"**
- **Causa**: Webhooks IFTTT mal configurados
- **Solução**: Verifique chave IFTTT e configure Voice Monkey

## 📈 Dados Monitorados

| Métrica | Descrição | Unidade |
|---------|-----------|---------|
| **Pac** | Potência instantânea | kW |
| **Eday** | Energia gerada hoje | kWh |
| **Cbattery1** | Estado de carga da bateria | % |
| **CO₂ evitado** | Emissões evitadas | kg |
| **Economia** | Economia financeira | R$ |

## 🎓 Sobre o Projeto

Este é um projeto acadêmico desenvolvido para o **Challenge FIAP**, demonstrando:

- ✅ **Integração com APIs reais** (GoodWe SEMS)
- ✅ **Automação IoT** (IFTTT + Alexa)
- ✅ **Interface web responsiva** (Flask + Bootstrap)
- ✅ **Validação inteligente** de dados
- ✅ **Tratamento robusto de erros**
- ✅ **Fallbacks** para desenvolvimento

---

## 👨‍💻 Desenvolvedor

**Guilherme Vega**  
📧 Email: [guivega7@outlook.com]  
🔗 GitHub: [@guivega7](https://github.com/guivega7)

---

*Sistema em constante desenvolvimento - contribuições são bem-vindas!* 🚀
