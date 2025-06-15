from flask import Blueprint, render_template, session, redirect, url_for
from models.usuario import Usuario
from extensions import db

dash_bp = Blueprint('dash', __name__)

@dash_bp.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for("auth.login"))
    return render_template('dashboard.html')