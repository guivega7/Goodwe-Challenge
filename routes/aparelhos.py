"""
Device management routes for solar energy system.

This module provides web routes for managing smart home devices,
including adding, editing, removing, and controlling device states.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify

from models.aparelho import Aparelho
from extensions import db
from routes.auth import login_required
from utils.logger import get_logger

logger = get_logger(__name__)

aparelhos_bp = Blueprint('aparelhos', __name__)


@aparelhos_bp.route('/aparelhos')
@login_required
def listar():
    """
    Display list of user devices.
    
    Returns:
        str: Rendered template with device list
    """
    if 'usuario_id' not in session:
        logger.warning("Unauthorized access attempt to device list")
        return render_template('aparelhos.html', aparelhos=[], aparelhos_data={"labels": [], "data": []})

    try:
        aparelhos = (Aparelho.query
                    .filter_by(usuario_id=session['usuario_id'])
                    .order_by(Aparelho.prioridade)
                    .all())

        aparelhos_data = {
            "labels": [aparelho.nome for aparelho in aparelhos],
            "data": [aparelho.consumo for aparelho in aparelhos]
        }

        logger.info(f"Retrieved {len(aparelhos)} devices for user {session['usuario_id']}")
        
        return render_template(
            'aparelhos.html', 
            aparelhos=aparelhos, 
            aparelhos_data=aparelhos_data
        )
        
    except Exception as e:
        logger.error(f"Error retrieving device list: {e}")
        return render_template('aparelhos.html', aparelhos=[], aparelhos_data={"labels": [], "data": []})


@aparelhos_bp.route('/aparelhos/adicionar', methods=['POST'])
@login_required
def adicionar():
    """
    Add new device to user's collection.
    
    Returns:
        tuple: JSON response with success/error message and status code
    """
    if not _ensure_authenticated():
        return {"error": "Usuário não autenticado."}, 401

    try:
        data = request.get_json()
        if not data:
            return {"error": "Dados não fornecidos."}, 400

        nome = data.get('nome')
        consumo = data.get('consumo')
        prioridade = data.get('prioridade', 3)

        if not nome or consumo is None:
            return {"error": "Nome e consumo são obrigatórios."}, 400

        try:
            consumo = float(consumo)
            prioridade = int(prioridade)
        except (ValueError, TypeError):
            return {"error": "Consumo deve ser um número e prioridade um inteiro."}, 400

        if consumo < 0:
            return {"error": "Consumo não pode ser negativo."}, 400

        if not (1 <= prioridade <= 5):
            return {"error": "Prioridade deve estar entre 1 e 5."}, 400

        # Check if device name already exists for user
        existing = Aparelho.query.filter_by(
            nome=nome, 
            usuario_id=session['usuario_id']
        ).first()
        
        if existing:
            return {"error": f"Aparelho '{nome}' já existe."}, 409

        aparelho = Aparelho(
            nome=nome,
            consumo=consumo,
            prioridade=prioridade,
            usuario_id=session['usuario_id']
        )
        
        db.session.add(aparelho)
        db.session.commit()

        logger.info(f"Device '{nome}' added for user {session['usuario_id']}")
        return {"message": f"Aparelho '{nome}' adicionado com sucesso."}, 201

    except Exception as e:
        logger.error(f"Error adding device: {e}")
        db.session.rollback()
        return {"error": "Erro interno do servidor."}, 500


@aparelhos_bp.route('/aparelhos/desligar', methods=['POST'])
@login_required
def desligar_aparelho():
    """
    Turn off a specific device.
    
    Returns:
        tuple: JSON response with success/error message and status code
    """
    if not _ensure_authenticated():
        return {"error": "Usuário não autenticado."}, 401

    try:
        data = request.get_json()
        if not data:
            return {"error": "Dados não fornecidos."}, 400

        nome_aparelho = data.get('nome')
        if not nome_aparelho:
            return {"error": "Nome do aparelho não fornecido."}, 400

        aparelho = Aparelho.query.filter_by(
            nome=nome_aparelho, 
            usuario_id=session['usuario_id']
        ).first()
        
        if not aparelho:
            return {"error": f"Aparelho '{nome_aparelho}' não encontrado."}, 404

        if not aparelho.status:
            return {"message": f"Aparelho '{nome_aparelho}' já está desligado."}, 200

        aparelho.status = False
        db.session.commit()

        logger.info(f"Device '{nome_aparelho}' turned off by user {session['usuario_id']}")
        return {"message": f"Aparelho '{nome_aparelho}' desligado com sucesso."}, 200

    except Exception as e:
        logger.error(f"Error turning off device: {e}")
        db.session.rollback()
        return {"error": "Erro interno do servidor."}, 500


@aparelhos_bp.route('/aparelhos/ligar', methods=['POST'])
@login_required
def ligar_aparelho():
    """
    Turn on a specific device.
    
    Returns:
        tuple: JSON response with success/error message and status code
    """
    if not _ensure_authenticated():
        return {"error": "Usuário não autenticado."}, 401

    try:
        data = request.get_json()
        if not data:
            return {"error": "Dados não fornecidos."}, 400

        nome_aparelho = data.get('nome')
        if not nome_aparelho:
            return {"error": "Nome do aparelho não fornecido."}, 400

        aparelho = Aparelho.query.filter_by(
            nome=nome_aparelho, 
            usuario_id=session['usuario_id']
        ).first()
        
        if not aparelho:
            return {"error": f"Aparelho '{nome_aparelho}' não encontrado."}, 404

        if aparelho.status:
            return {"message": f"Aparelho '{nome_aparelho}' já está ligado."}, 200

        aparelho.status = True
        db.session.commit()

        logger.info(f"Device '{nome_aparelho}' turned on by user {session['usuario_id']}")
        return {"message": f"Aparelho '{nome_aparelho}' ligado com sucesso."}, 200

    except Exception as e:
        logger.error(f"Error turning on device: {e}")
        db.session.rollback()
        return {"error": "Erro interno do servidor."}, 500


@aparelhos_bp.route('/aparelhos/editar', methods=['POST'])
@login_required
def editar_aparelho():
    """
    Edit device properties.
    
    Returns:
        Union: Redirect to device list or JSON error response
    """
    if not _ensure_authenticated():
        return {"error": "Usuário não autenticado."}, 401

    try:
        data = request.form
        aparelho_id = data.get('id')
        
        if not aparelho_id:
            return {"error": "ID do aparelho não fornecido."}, 400

        aparelho = Aparelho.query.filter_by(
            id=aparelho_id, 
            usuario_id=session['usuario_id']
        ).first()

        if not aparelho:
            return {"error": "Aparelho não encontrado."}, 404

        novo_nome = data.get('nome')
        novo_consumo = data.get('consumo')
        nova_prioridade = data.get('prioridade')

        if novo_nome:
            # Check for duplicate names (excluding current device)
            existing = Aparelho.query.filter(
                Aparelho.nome == novo_nome,
                Aparelho.usuario_id == session['usuario_id'],
                Aparelho.id != aparelho_id
            ).first()
            
            if existing:
                return {"error": f"Aparelho '{novo_nome}' já existe."}, 409
                
            aparelho.nome = novo_nome

        if novo_consumo:
            try:
                consumo = float(novo_consumo)
                if consumo < 0:
                    return {"error": "Consumo não pode ser negativo."}, 400
                aparelho.consumo = consumo
            except (ValueError, TypeError):
                return {"error": "Consumo deve ser um número."}, 400

        if nova_prioridade:
            try:
                prioridade = int(nova_prioridade)
                if not (1 <= prioridade <= 5):
                    return {"error": "Prioridade deve estar entre 1 e 5."}, 400
                aparelho.prioridade = prioridade
            except (ValueError, TypeError):
                return {"error": "Prioridade deve ser um inteiro."}, 400

        db.session.commit()
        logger.info(f"Device {aparelho_id} edited by user {session['usuario_id']}")
        
        return redirect(url_for('aparelhos.listar'))

    except Exception as e:
        logger.error(f"Error editing device: {e}")
        db.session.rollback()
        return {"error": "Erro interno do servidor."}, 500


@aparelhos_bp.route('/aparelhos/remover', methods=['POST'])
@login_required
def remover_aparelho():
    """
    Remove device from user's collection.
    
    Returns:
        Union: Redirect to device list or JSON error response
    """
    if not _ensure_authenticated():
        return {"error": "Usuário não autenticado."}, 401

    try:
        data = request.form
        aparelho_id = data.get('id')
        
        if not aparelho_id:
            return {"error": "ID do aparelho não fornecido."}, 400

        aparelho = Aparelho.query.filter_by(
            id=aparelho_id, 
            usuario_id=session['usuario_id']
        ).first()

        if not aparelho:
            return {"error": "Aparelho não encontrado."}, 404

        nome_aparelho = aparelho.nome
        db.session.delete(aparelho)
        db.session.commit()

        logger.info(f"Device '{nome_aparelho}' removed by user {session['usuario_id']}")
        return redirect(url_for('aparelhos.listar'))

    except Exception as e:
        logger.error(f"Error removing device: {e}")
        db.session.rollback()
        return {"error": "Erro interno do servidor."}, 500


@aparelhos_bp.route('/aparelhos/status/<int:aparelho_id>')
@login_required
def obter_status(aparelho_id: int):
    """
    Get device status information.
    
    Args:
        aparelho_id: Device ID
        
    Returns:
        tuple: JSON response with device status and HTTP code
    """
    if not _ensure_authenticated():
        return {"error": "Usuário não autenticado."}, 401

    try:
        aparelho = Aparelho.query.filter_by(
            id=aparelho_id, 
            usuario_id=session['usuario_id']
        ).first()

        if not aparelho:
            return {"error": "Aparelho não encontrado."}, 404

        return {
            "id": aparelho.id,
            "nome": aparelho.nome,
            "status": aparelho.status,
            "consumo": aparelho.consumo,
            "prioridade": aparelho.prioridade
        }, 200

    except Exception as e:
        logger.error(f"Error getting device status: {e}")
        return {"error": "Erro interno do servidor."}, 500


def _ensure_authenticated():
    """
    Ensure user is authenticated, creating session if needed for development.
    
    Returns:
        bool: True if user is authenticated
    """
    if 'usuario_id' not in session:
        # For development purposes only - remove in production
        session['usuario_id'] = 1
        logger.warning("Auto-authenticated user for development")
    
    return True