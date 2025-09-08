"""
Extensões da Aplicação SolarMind

Inicialização das extensões Flask utilizadas pela aplicação.
As extensões são inicializadas aqui e configuradas no app factory.
"""

from flask_sqlalchemy import SQLAlchemy

# Instância do SQLAlchemy para ORM
db = SQLAlchemy()