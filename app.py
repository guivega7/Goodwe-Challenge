"""
SolarMind - Sistema Inteligente de Monitoramento Solar

Aplicação Flask para monitoramento e controle de sistemas de energia solar
com integração a assistentes inteligentes e automação residencial.

Funcionalidades principais:
- Monitoramento em tempo real do sistema solar
- Integração com Alexa e Google Home via IFTTT
- IA para análise e previsão de consumo
- Automação residencial inteligente
- Dashboard web para visualização de dados
"""

import os
from flask import Flask
from dotenv import load_dotenv

from extensions import db


def create_app():
    """
    Factory function para criação da aplicação Flask.
    
    Configura a aplicação, inicializa extensões e registra blueprints.
    
    Returns:
        Flask: Instância configurada da aplicação
    """
    # Carrega variáveis de ambiente
    load_dotenv()
    
    # Cria instância da aplicação
    app = Flask(__name__)
    
    # Configurações da aplicação
    app.secret_key = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///solarmind.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializa extensões
    db.init_app(app)
    
    # Importa e registra blueprints
    from routes.api import api_bp
    from routes.auth import auth_bp
    from routes.dashboard import dash_bp
    from routes.main import main_bp
    from routes.estatisticas import estatisticas_bp
    from routes.aparelhos import aparelhos_bp
    from routes.alexa import alexa_bp
    
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dash_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(aparelhos_bp)
    app.register_blueprint(estatisticas_bp)
    app.register_blueprint(alexa_bp)
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)