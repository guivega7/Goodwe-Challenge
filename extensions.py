"""
Extensões da Aplicação SolarMind

Inicialização das extensões Flask utilizadas pela aplicação.
As extensões são inicializadas aqui e configuradas no app factory.
"""

from flask_sqlalchemy import SQLAlchemy
import logging

# Instância do SQLAlchemy para ORM
db = SQLAlchemy()

# Logger compartilhado simples
logger = logging.getLogger('solarmind')
if not logger.handlers:
	handler = logging.StreamHandler()
	formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)
logger.setLevel(logging.INFO)