from flask import Flask
from dotenv import load_dotenv
import os
from extensions import db

def create_app():
    """
    Função de criação da aplicação Flask SolarMind.
    Carrega as configurações, inicializa o banco de dados e registra as rotas.
    """
    load_dotenv()
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///solarmind.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Importação das rotas para evitar importação circular
    from routes.auth import auth_bp
    from routes.dashboard import dash_bp
    from routes.api import api_bp
    from routes.main import main_bp
    from routes.estatisticas import estatisticas_bp
    from routes.aparelhos import aparelhos_bp

    # Registro das rotas
    app.register_blueprint(auth_bp)
    app.register_blueprint(dash_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(aparelhos_bp)
    app.register_blueprint(estatisticas_bp)

    return app

# Execução local
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)