from app import create_app
from extensions import db
from models.aparelho import Aparelho
from models.usuario import Usuario

app = create_app()

with app.app_context():
    # Cria todas as tabelas
    db.create_all()
    print("Tabelas criadas com sucesso!")