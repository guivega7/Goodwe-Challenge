import pytest
from app import create_app
from extensions import db

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_login_page(client):
    rv = client.get('/login')
    assert rv.status_code == 200
    assert b'Entrar' in rv.data