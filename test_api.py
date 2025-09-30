from app import create_app
import json

# Criar a aplicação
app = create_app()

# Testar o endpoint internamente
with app.test_client() as client:
    response = client.get('/api/solar/status')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.get_json()}")