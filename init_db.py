"""
Inicializador do Banco de Dados - SolarMind

Script para criar as tabelas do banco de dados e popular
com dados iniciais para desenvolvimento e teste.

Uso:
    python init_db.py
"""

from app import create_app
from extensions import db
from models.aparelho import Aparelho
from models.usuario import Usuario


def init_database():
    """
    Inicializa o banco de dados criando todas as tabelas
    e adicionando dados de exemplo para desenvolvimento.
    """
    app = create_app()
    
    with app.app_context():
        # Remove todas as tabelas existentes
        db.drop_all()
        print("🗑️  Tabelas existentes removidas")
        
        # Cria todas as tabelas
        db.create_all()
        print("✅ Tabelas criadas com sucesso!")
        
        # Cria usuário de exemplo
        usuario_exemplo = Usuario(
            nome="admin",
            email="admin@solarmind.com",
            senha="admin123"
        )
        
        db.session.add(usuario_exemplo)
        db.session.commit()
        print("👤 Usuário administrador criado")
        
        # Cria aparelhos de exemplo
        aparelhos_exemplo = [
            Aparelho("ventilador", 0.1, 3, usuario_exemplo.id),
            Aparelho("ar condicionado", 2.5, 1, usuario_exemplo.id),
            Aparelho("geladeira", 0.3, 1, usuario_exemplo.id),
            Aparelho("tv", 0.2, 4, usuario_exemplo.id),
            Aparelho("notebook", 0.1, 3, usuario_exemplo.id)
        ]
        
        for aparelho in aparelhos_exemplo:
            db.session.add(aparelho)
        
        db.session.commit()
        print(f"🏠 {len(aparelhos_exemplo)} aparelhos de exemplo criados")
        
        print("\n🌞 Banco de dados SolarMind inicializado com sucesso!")
        print("📊 Dashboard disponível em: http://localhost:5000")
        print("🔑 Login: admin@solarmind.com | Senha: admin123")


if __name__ == "__main__":
    init_database()