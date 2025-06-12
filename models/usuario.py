from werkzeug.security import generate_password_hash, check_password_hash

class Usuario:
    def __init__(self, nome, senha):
        self.nome = nome
        self._senha_hash = generate_password_hash(senha)

    def checar_senha(self, senha):
        return check_password_hash(self._senha_hash, senha)
    
usuarios = {}