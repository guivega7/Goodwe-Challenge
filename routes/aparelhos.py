"""
Device management routes for solar energy system.

This module provides web routes for managing smart home devices,
including adding, editing, removing, and controlling device states.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
import os
from datetime import datetime

from models.aparelho import Aparelho
from services.device_sync import sync_tuya_devices
from services.tuya_client import TuyaClient
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
        # Usa helper para auto autenticar em dev
        _ensure_authenticated()

    try:
        aparelhos = (Aparelho.query
                    .filter_by(usuario_id=session['usuario_id'])
                    .order_by(Aparelho.prioridade)
                    .all())

        # --- START: Cálculos para o resumo energético e gráfico ---
        aparelhos_data = {
            "labels": [],
            "data": []
        }
        resumo_energetico = {
            "maior_consumidor": None,
            "mais_eficiente": None,
            "total_consumo_kwh": 0,
            "custo_total_reais": 0,
            "economia_possivel": 0
        }

        if aparelhos:
            aparelhos_data["labels"] = [ap.nome for ap in aparelhos]
            aparelhos_data["data"] = [ap.consumo for ap in aparelhos]

            # Ordena por consumo para facilitar a busca de min/max
            aparelhos_por_consumo = sorted(aparelhos, key=lambda x: x.consumo, reverse=True)
            
            resumo_energetico["maior_consumidor"] = aparelhos_por_consumo[0]
            resumo_energetico["mais_eficiente"] = aparelhos_por_consumo[-1]
            
            total_consumo_kwh = sum(ap.consumo for ap in aparelhos)
            custo_total_reais = total_consumo_kwh * 0.75 # Fator de custo fixo
            
            resumo_energetico["total_consumo_kwh"] = total_consumo_kwh
            resumo_energetico["custo_total_reais"] = custo_total_reais
            resumo_energetico["economia_possivel"] = custo_total_reais * 0.15 # Estimativa de 15%

        # --- END: Cálculos ---

        logger.info(f"Retrieved {len(aparelhos)} devices for user {session['usuario_id']}")
        
        return render_template(
            'aparelhos.html', 
            aparelhos=aparelhos, 
            aparelhos_data=aparelhos_data,
            resumo_energetico=resumo_energetico, # Passa o resumo para o template
            tuya_device_id=os.getenv('TUYA_DEVICE_ID')
        )
        
    except Exception as e:
        logger.error(f"Error retrieving device list: {e}")
        return render_template('aparelhos.html', aparelhos=[], aparelhos_data={"labels": [], "data": []}, resumo_energetico={})


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
        # Aceita tanto JSON quanto form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            
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
            usuario_id=session['usuario_id'],
            origem='manual'
        )
        
        db.session.add(aparelho)
        db.session.commit()

        logger.info(f"Device '{nome}' added for user {session['usuario_id']}")
        
        # Se for form data, redireciona de volta para a página
        # Fixed redirect endpoint name
        if not request.is_json:
            flash(f"Aparelho '{nome}' adicionado com sucesso!", 'success')
            return redirect(url_for('aparelhos.listar'))
        
        # Se for JSON, retorna resposta JSON
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


@aparelhos_bp.route('/aparelhos/sincronizar-tuya', methods=['POST'])
@login_required
def sincronizar_tuya():
    """Força sincronização de dispositivos Tuya criando/atualizando aparelhos."""
    try:
        # Aceita device_id explícito (form ou query) para forçar sync de único device
        device_id_forced = request.form.get('device_id') or request.args.get('device_id')
        stats = sync_tuya_devices(usuario_id=session.get('usuario_id'), force_device_id=device_id_forced)
        if 'error' in stats:
            flash(f"Falha na sincronização: {stats['error']}", 'danger')
        else:
            extra = ''
            if stats.get('force') or device_id_forced:
                extra = ' (modo device único)'
            if stats.get('novos',0) == 0 and stats.get('atualizados',0) == 0:
                flash("Nenhum dispositivo sincronizado. Verifique TUYA_DEVICE_ID ou ID informado.", 'warning')
            else:
                flash(f"Sincronização: {stats.get('novos',0)} novos, {stats.get('atualizados',0)} atualizados{extra}", 'success')
    except Exception as e:
        flash(f"Erro inesperado: {e}", 'danger')
    return redirect(url_for('aparelhos.listar'))


@aparelhos_bp.route('/aparelhos/consumo-atual/<int:aparelho_id>')
@login_required
def consumo_atual(aparelho_id: int):
    """Retorna potência estimada ou em tempo real (se ampliado no futuro)."""
    try:
        ap = Aparelho.query.filter_by(id=aparelho_id, usuario_id=session['usuario_id']).first()
        if not ap:
            return jsonify({'error': 'Aparelho não encontrado'}), 404

        # Se for Tuya (tem codigo_externo) tenta obter potência real
        if ap.codigo_externo:
            try:
                from services.tuya_client import TuyaClient
                client = TuyaClient()
                status_resp = client.get_device_status_by_id(ap.codigo_externo)
                
                # Usar o parser centralizado do TuyaClient
                metrics = client.parse_metrics(status_resp)
                
                potencia_w = metrics.get('power_w')
                switch_on = metrics.get('switch_on')

                # Atualiza o status no banco de dados local para manter a consistência
                if switch_on is not None and ap.status != switch_on:
                    ap.status = switch_on
                    db.session.commit()

                if potencia_w is not None:
                    return jsonify({
                        'potencia': round(potencia_w, 2),
                        'status': switch_on,
                        'fonte': 'tuya',
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    })
            except Exception as e:
                logger.error(f"Falha ao buscar status real da Tuya para {ap.codigo_externo}: {e}")
                # Cai para estimativa se der erro
                pass

        # Estimativa: consumo_kwh_dia -> potência média assumindo 4h ativo
        potencia_estimada = round(ap.consumo * 1000 / 4, 2)
        return jsonify({
            'potencia': potencia_estimada,
            'fonte': 'estimado',
            'status': ap.status, # Retorna o status do banco de dados
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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