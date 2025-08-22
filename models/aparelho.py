from extensions import db

class Aparelho(db.Model):
    __tablename__ = 'aparelhos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    consumo = db.Column(db.Float, nullable=False)  # consumo em kWh
    prioridade = db.Column(db.Integer, nullable=False)  # 1 (alta) a 5 (baixa)
    status = db.Column(db.Boolean, default=True)  # True = ligado
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

    def __init__(self, nome, consumo, prioridade, usuario_id):
        self.nome = nome
        self.consumo = consumo
        self.prioridade = prioridade
        self.usuario_id = usuario_id
        self.status = True  # Por padrão, aparelho começa ligado

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'consumo': self.consumo,
            'prioridade': self.prioridade,
            'status': self.status
        }

    def __repr__(self):
        return f'<Aparelho {self.nome}>'