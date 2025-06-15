from flask import Flask
from dotenv import load_dotenv
import os
from extensions import db

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///solarmind.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Importação dos blueprints dentro da função para evitar importação circular
    from routes.auth import auth_bp
    from routes.dashboard import dash_bp
    from routes.api import api_bp
    from routes.main import main_bp
    from routes.estatisticas import estatisticas_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dash_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(estatisticas_bp)

    return app

# Para rodar localmente
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)