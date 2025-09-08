"""
Authentication routes for user login, registration, and logout.

This module provides secure user authentication with password hashing,
session management, and user registration validation.
"""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from models.usuario import Usuario
from extensions import db
from utils.logger import get_logger

logger = get_logger(__name__)

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    """
    Decorator to require login for protected routes.
    
    Args:
        f: Function to be decorated
        
    Returns:
        Decorated function that checks for authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Você precisa fazer login para acessar esta página.')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login authentication.
    
    Returns:
        str: Rendered template or redirect response
    """
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        senha = request.form.get('senha', '')
        
        if not nome or not senha:
            flash('Nome/Email e senha são obrigatórios.')
            return render_template('login.html')
        
        try:
            # Tenta login por nome primeiro, depois por email
            usuario = Usuario.query.filter_by(nome=nome).first()
            if not usuario:
                usuario = Usuario.query.filter_by(email=nome).first()
            
            if usuario and usuario.checar_senha(senha):
                session['usuario_id'] = usuario.id
                session['usuario_nome'] = usuario.nome
                
                logger.info(f"User '{nome}' logged in successfully")
                flash(f'Bem-vindo, {usuario.nome}!')
                
                return redirect(url_for('dash.dashboard'))
            else:
                logger.warning(f"Failed login attempt for user '{nome}'")
                flash('Nome/Email ou senha inválidos.')
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            flash('Erro interno. Tente novamente.')
    
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.
    
    Returns:
        str: Rendered template or redirect response
    """
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        confirmar = request.form.get('confirmar_senha', '')
        
        # Input validation
        if not all([nome, email, senha, confirmar]):
            flash('Todos os campos são obrigatórios.')
            return render_template('register.html')
        
        if len(nome) < 3:
            flash('Nome deve ter pelo menos 3 caracteres.')
            return render_template('register.html')
        
        if len(senha) < 6:
            flash('Senha deve ter pelo menos 6 caracteres.')
            return render_template('register.html')
        
        if senha != confirmar:
            flash('As senhas não coincidem.')
            return render_template('register.html')
        
        if '@' not in email or '.' not in email:
            flash('Email inválido.')
            return render_template('register.html')
        
        try:
            # Check for existing users
            if Usuario.query.filter_by(nome=nome).first():
                flash('Nome de usuário já existe.')
                return render_template('register.html')
            
            if Usuario.query.filter_by(email=email).first():
                flash('E-mail já cadastrado.')
                return render_template('register.html')
            
            # Create new user
            novo_usuario = Usuario(nome=nome, email=email)
            novo_usuario.set_senha(senha)
            
            db.session.add(novo_usuario)
            db.session.commit()
            
            logger.info(f"New user registered: {nome} ({email})")
            flash('Cadastro realizado com sucesso! Faça login.')
            
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            logger.error(f"Error during registration: {e}")
            db.session.rollback()
            flash('Erro interno. Tente novamente.')
    
    return render_template('register.html')


@auth_bp.route('/logout')
def logout():
    """
    Handle user logout and session cleanup.
    
    Returns:
        str: Redirect response to home page
    """
    user_name = session.get('usuario_nome', 'Unknown')
    session.clear()
    
    logger.info(f"User '{user_name}' logged out")
    flash('Logout realizado com sucesso.')
    
    return redirect(url_for('main.home'))


@auth_bp.route('/profile')
def profile():
    """
    Display user profile information.
    
    Returns:
        str: Rendered profile template or redirect to login
    """
    if 'usuario_id' not in session:
        flash('Faça login para acessar seu perfil.')
        return redirect(url_for('auth.login'))
    
    try:
        usuario = Usuario.query.get(session['usuario_id'])
        if not usuario:
            session.clear()
            flash('Usuário não encontrado. Faça login novamente.')
            return redirect(url_for('auth.login'))
        
        return render_template('profile.html', usuario=usuario)
        
    except Exception as e:
        logger.error(f"Error loading profile: {e}")
        flash('Erro ao carregar perfil.')
        return redirect(url_for('main.home'))