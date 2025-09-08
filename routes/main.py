"""
Main application routes for SolarMind energy management system.

This module provides the primary navigation routes including
the home page and general application information.
"""

from flask import Blueprint, render_template, session, redirect, url_for

from models.usuario import Usuario
from extensions import db
from utils.logger import get_logger

logger = get_logger(__name__)

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    """
    Display the application home page.
    
    Returns:
        str: Rendered home template
    """
    try:
        # Check if user is already logged in
        usuario_logado = None
        if 'usuario_id' in session:
            usuario_logado = Usuario.query.get(session['usuario_id'])
            
        return render_template('home.html', usuario=usuario_logado)
        
    except Exception as e:
        logger.error(f"Error loading home page: {e}")
        return render_template('home.html', usuario=None)


@main_bp.route('/about')
def about():
    """
    Display information about the SolarMind system.
    
    Returns:
        str: Rendered about template
    """
    return render_template('about.html')


@main_bp.route('/features')
def features():
    """
    Display system features and capabilities.
    
    Returns:
        str: Rendered features template
    """
    features_list = [
        {
            'title': 'Monitoramento em Tempo Real',
            'description': 'Acompanhe geração e consumo de energia solar em tempo real',
            'icon': 'fas fa-chart-line'
        },
        {
            'title': 'Automação Inteligente',
            'description': 'Controle automático de aparelhos baseado na disponibilidade de energia',
            'icon': 'fas fa-robot'
        },
        {
            'title': 'Integração IFTTT',
            'description': 'Conecte com Alexa e outros dispositivos smart home',
            'icon': 'fas fa-plug'
        },
        {
            'title': 'Relatórios Detalhados',
            'description': 'Análises completas de consumo e economia de energia',
            'icon': 'fas fa-file-chart-line'
        },
        {
            'title': 'Previsão Climática',
            'description': 'Otimização baseada em previsões de geração solar',
            'icon': 'fas fa-cloud-sun'
        },
        {
            'title': 'Interface Responsiva',
            'description': 'Acesse de qualquer dispositivo com design moderno',
            'icon': 'fas fa-mobile-alt'
        }
    ]
    
    return render_template('features.html', features=features_list)


@main_bp.route('/health')
def health_check() -> dict:
    """
    Health check endpoint for monitoring.
    
    Returns:
        dict: System health status
    """
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        
        return {
            'status': 'healthy',
            'database': 'connected',
            'version': '1.0.0'
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }, 503