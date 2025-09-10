"""
Rotas para administração do RAG System.

Página administrativa para gerenciar o sistema de conhecimento
contextual (RAG) do SolarMind.
"""

from flask import Blueprint, render_template
from flask_login import login_required

from utils.logger import get_logger

logger = get_logger(__name__)

# Blueprint para administração do RAG
rag_admin_bp = Blueprint('rag_admin', __name__)


@rag_admin_bp.route('/admin/rag')
@login_required
def rag_admin():
    """
    Página de administração do RAG System.
    
    Returns:
        str: Template da página de admin
    """
    logger.info(f"Acesso à administração RAG")
    return render_template('rag_admin.html')
