"""
Configurações da Aplicação SolarMind

Define as configurações de ambiente para desenvolvimento,
teste e produção da aplicação.
"""

import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()


class Config:
    """Configuração base da aplicação."""
    
    # Chave secreta para sessões e segurança
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    
    # Configurações do banco de dados
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///solarmind.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de debug
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Configurações IFTTT (se necessário)
    IFTTT_WEBHOOK_URL = os.getenv('IFTTT_WEBHOOK_URL')
    IFTTT_KEY = os.getenv('IFTTT_KEY')


class DevelopmentConfig(Config):
    """Configuração para ambiente de desenvolvimento."""
    DEBUG = True


class ProductionConfig(Config):
    """Configuração para ambiente de produção."""
    DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY')  # Obrigatório em produção


class TestingConfig(Config):
    """Configuração para testes."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Mapeamento de configurações por ambiente
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}