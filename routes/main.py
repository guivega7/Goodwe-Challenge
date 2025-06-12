from flask import Blueprint, render_template, session, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    if 'usuario' in session:
        return redirect(url_for('dash.dashboard'))
    return render_template('home.html')
