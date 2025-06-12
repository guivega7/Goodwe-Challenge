from flask import Flask
from routes.auth import auth_bp
from routes.dashboard import dash_bp
from routes.api import api_bp
from routes.main import main_bp
from routes.estatisticas import estatisticas_bp
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

app.register_blueprint(auth_bp)
app.register_blueprint(dash_bp)
app.register_blueprint(api_bp)
app.register_blueprint(main_bp)
app.register_blueprint(estatisticas_bp)

if __name__ == '__main__':
    app.run(debug=True,port=5000)
