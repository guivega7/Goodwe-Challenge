# 🌞 SolarMind - Sistema Inteligente de Monitoramento Solar

![Static Badge](https://img.shields.io/badge/Status-Est%C3%A1vel-brightgreen) ![Static Badge](https://img.shields.io/badge/Python-3.8%2B-blue) ![Static Badge](https://img.shields.io/badge/Licen%C3%A7a-MIT-lightgrey)

> Sistema inteligente de monitoramento de energia solar com automação residencial, controle por voz (Alexa) e insights gerados por IA (Google Gemini).

<br>

## 🎬 Demonstração Rápida

![GIF do Projeto Funcionando](link_para_o_seu_gif.gif)

<br>

## 🎯 O Problema

Muitos sistemas de energia solar oferecem dados brutos, mas não ajudam o usuário a tomar decisões inteligentes para economizar energia, automatizar a casa ou prever a manutenção.

## ✨ A Solução

O SolarMind é uma plataforma completa que não apenas monitora, mas também **controla e otimiza** o uso de energia. Ele integra dados do inversor solar, dispositivos inteligentes (tomadas) e assistentes de voz, usando IA para fornecer insights e automações que realmente fazem a diferença na conta de luz e na conveniência do dia a dia.

---

## 🚀 Principais Funcionalidades

* **🤖 Inteligência Artificial com Gemini:** Chat para tirar dúvidas e geração de insights para otimizar o consumo.
* **🗣️ Controle por Voz:** Integração total com **Amazon Alexa** e Google Home via IFTTT para ligar e desligar aparelhos.
* **📊 Dashboard em Tempo Real:** Gráficos interativos para acompanhar produção, consumo e estado da bateria (com dados reais via API da GoodWe ou simulados).
* **🏠 Automação Residencial:** Controle tomadas inteligentes e crie regras para economizar energia automaticamente.
* **🔔 Alertas Proativos:** Notificações sobre necessidade de manutenção ou consumo anormal.

---

## 🛠️ Tecnologias Utilizadas

| Categoria | Tecnologias |
| :--- | :--- |
| **Backend** | `Python`, `Flask`, `SQLAlchemy`, `APScheduler` |
| **Frontend** | `HTML5`, `CSS3`, `JavaScript`, `Bootstrap` |
| **Banco de Dados** | `SQLite` (com suporte para `PostgreSQL`) |
| **Inteligência Artificial** | `Google Gemini API` |
| **Integrações** | `GoodWe SEMS API`, `Tuya API`, `IFTTT Webhooks`, `API REST` |
| **DevOps** | `Git`, `Docker`, `Gunicorn` |

<br>

<details>
<summary><strong>🚀 Clique aqui para ver as instruções de Instalação e Execução</strong></summary>

### Instalação e Configuração

**Pré-requisitos:** Python 3.8+, Git

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/guivega7/Goodwe-Challenge.git](https://github.com/guivega7/Goodwe-Challenge.git)
    cd Goodwe-Challenge
    ```
2.  **Crie e ative o ambiente virtual:**
    ```bash
    python -m venv venv
    # Windows: venv\Scripts\activate | Linux/macOS: source venv/bin/activate
    ```
3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure as variáveis de ambiente:**
    ```bash
    # Copie o arquivo de exemplo e edite com suas chaves
    copy .env.example .env
    ```
5.  **Inicialize o banco de dados:**
    ```bash
    python init_db.py
    ```
6.  **Execute a aplicação:**
    ```bash
    python app.py
    ```
    Acesse em `http://localhost:5000/dashboard?fonte=mock`

</details>

<details>
<summary><strong>📄 Clique aqui para ver a Documentação Detalhada da API e Endpoints</strong></summary>

  ### Principais Endpoints Solares
  | Endpoint | Descrição | Cache |
  | :--- | :--- | :--- |
  | `GET /api/solar/status` | Status resumido (potência, SOC, etc.) | 30s |
  | `GET /api/solar/data` | Agregado produção/consumo/bateria/economia | 120s |

  *(continue com o resto da sua documentação aqui)*

</details>

<details>
<summary><strong>⚙️ Clique aqui para ver todas as Variáveis de Ambiente</strong></summary>

  | Categoria | Variável | Obrigatório | Default / Exemplo | Descrição |
  | :--- | :--- | :--- | :--- | :--- |
  | Core | `SECRET_KEY` | Produção | `dev-key-change-in-production` | Chave Flask... |

  *(continue com o resto da sua tabela aqui)*

</details>

---

### 🤝 Como Contribuir
Fork o projeto, crie uma branch (`git checkout -b feature/SuaFeature`) e abra um Pull Request!

### 📝 Licença
Este projeto está licenciado sob a Licença MIT.

⭐ Se este projeto te ajudou, considere dar uma estrela!