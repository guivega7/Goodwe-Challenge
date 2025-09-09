"""
Blueprint para chat com IA Gemini.

Implementa interface de chat para perguntas sobre:
- Sistema solar e energia
- Projeto SolarMind
- Análises técnicas

Histórico salvo por usuário no banco.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from extensions import db
from services.gemini_client import gemini_client
from utils.logger import get_logger

logger = get_logger(__name__)

chat_bp = Blueprint('chat', __name__)


class ChatMessage(db.Model):
    """Modelo para histórico de mensagens do chat."""
    
    __tablename__ = 'chat_message'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' ou 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }


@chat_bp.route('/chat')
@login_required
def chat_page():
    """Página principal do chat."""
    return render_template('chat.html')


@chat_bp.route('/api/chat/messages')
@login_required
def get_messages():
    """Retorna histórico de mensagens do usuário."""
    try:
        messages = ChatMessage.query.filter_by(
            usuario_id=current_user.id
        ).order_by(ChatMessage.timestamp.desc()).limit(50).all()
        
        # Reverter para ordem cronológica
        messages.reverse()
        
        return jsonify({
            'status': 'sucesso',
            'messages': [msg.to_dict() for msg in messages]
        })
    except Exception as e:
        logger.error(f"Erro ao buscar mensagens: {e}")
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


@chat_bp.route('/api/chat/send', methods=['POST'])
@login_required
def send_message():
    """Envia mensagem e recebe resposta da IA."""
    try:
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'status': 'erro',
                'mensagem': 'Mensagem não pode estar vazia'
            }), 400
        
        # Salva mensagem do usuário
        user_msg = ChatMessage(
            usuario_id=current_user.id,
            role='user',
            content=user_message
        )
        db.session.add(user_msg)
        
        # Busca contexto das últimas mensagens
        recent_messages = ChatMessage.query.filter_by(
            usuario_id=current_user.id
        ).order_by(ChatMessage.timestamp.desc()).limit(10).all()
        
        context = [{'role': msg.role, 'content': msg.content} for msg in reversed(recent_messages)]
        
        # Gera resposta da IA
        ai_response = gemini_client.chat_response(user_message, context)
        
        # Salva resposta da IA
        ai_msg = ChatMessage(
            usuario_id=current_user.id,
            role='assistant',
            content=ai_response
        )
        db.session.add(ai_msg)
        db.session.commit()
        
        return jsonify({
            'status': 'sucesso',
            'user_message': user_msg.to_dict(),
            'ai_response': ai_msg.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro no chat: {e}")
        return jsonify({
            'status': 'erro',
            'mensagem': f'Erro interno: {str(e)}'
        }), 500


@chat_bp.route('/api/chat/clear', methods=['POST'])
@login_required
def clear_chat():
    """Limpa histórico de chat do usuário."""
    try:
        ChatMessage.query.filter_by(usuario_id=current_user.id).delete()
        db.session.commit()
        
        return jsonify({
            'status': 'sucesso',
            'mensagem': 'Histórico limpo com sucesso'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao limpar chat: {e}")
        return jsonify({
            'status': 'erro',
            'mensagem': f'Erro interno: {str(e)}'
        }), 500
