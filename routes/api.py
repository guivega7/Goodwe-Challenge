from flask import Blueprint, jsonify
from models.usuario import Usuario
from extensions import db

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/status')
def status():
    return jsonify({'ok':True, 'msg': 'API rodando'})