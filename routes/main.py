from flask import Blueprint, render_template, session, redirect, url_for
from models.usuario import Usuario
from extensions import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('home.html')