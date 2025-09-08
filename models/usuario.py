"""
Modelo Usuario - Sistema SolarMind

Define a estrutura dos usuários do sistema,
incluindo autenticação e relacionamentos.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class Usuario(db.Model):
    """
    Modelo para usuários do sistema SolarMind.
    
    Gerencia autenticação e dados pessoais dos usuários
    que utilizam o sistema de monitoramento solar.
    """
    
    __tablename__ = 'usuario'

    # Campos da tabela
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False, unique=True, index=True)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    senha_hash = db.Column(db.String(128), nullable=False)
    
    # Relacionamentos
    aparelhos = db.relationship('Aparelho', backref='usuario', lazy=True)

    def __init__(self, nome, email, senha=None):
        """
        Inicializa um novo usuário.
        
        Args:
            nome (str): Nome do usuário
            email (str): Email do usuário
            senha (str, optional): Senha em texto plano
        """
        self.nome = nome
        self.email = email
        if senha:
            self.set_senha(senha)

    def set_senha(self, senha):
        """
        Define a senha do usuário (com hash).
        
        Args:
            senha (str): Senha em texto plano
        """
        self.senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha):
        """
        Verifica se a senha está correta.
        
        Args:
            senha (str): Senha em texto plano para verificar
            
        Returns:
            bool: True se a senha estiver correta
        """
        return check_password_hash(self.senha_hash, senha)

    def to_dict(self):
        """
        Converte o usuário para dicionário (sem senha).
        
        Returns:
            dict: Representação em dicionário do usuário
        """
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email
        }

    def __repr__(self):
        """Representação string do usuário."""
        return f'<Usuario {self.nome}>'