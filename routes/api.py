from flask import Blueprint, jsonify

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/status')
def status():
    return jsonify({'ok':True, 'msg': 'API rodando'})