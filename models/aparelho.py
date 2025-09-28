"""
Modelo Aparelho - Sistema SolarMind

Define a estrutura dos aparelhos eletrônicos monitorados
pelo sistema de automação residencial.
"""

from extensions import db


class Aparelho(db.Model):
    """
    Modelo para aparelhos eletrônicos do sistema de automação.
    
    Representa dispositivos que podem ser controlados remotamente
    e têm seu consumo energético monitorado.
    """
    
    __tablename__ = 'aparelhos'

    # Campos da tabela
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, index=True)
    consumo = db.Column(db.Float, nullable=False)  # Consumo em kWh
    prioridade = db.Column(db.Integer, nullable=False)  # 1 (alta) a 5 (baixa)
    status = db.Column(db.Boolean, default=True, nullable=False)  # True = ligado
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    # Identificador externo (ex: ID Tuya) para sincronização idempotente
    codigo_externo = db.Column(db.String(100), index=True, nullable=True)
    # Origem/Fonte do dispositivo (ex: 'tuya', 'manual', 'goodwe')
    origem = db.Column(db.String(30), index=True, nullable=True)

    def __init__(self, nome, consumo, prioridade, usuario_id, codigo_externo=None, origem=None):
        """
        Inicializa um novo aparelho.
        
        Args:
            nome (str): Nome identificador do aparelho
            consumo (float): Consumo energético em kWh
            prioridade (int): Prioridade de 1 (alta) a 5 (baixa)
            usuario_id (int): ID do usuário proprietário
        """
        self.nome = nome
        self.consumo = consumo
        self.prioridade = prioridade
        self.usuario_id = usuario_id
        self.status = True
        self.codigo_externo = codigo_externo
        self.origem = origem

    def ligar(self):
        """Liga o aparelho."""
        self.status = True

    def desligar(self):
        """Desliga o aparelho."""
        self.status = False

    def alternar_status(self):
        """Alterna o status do aparelho (liga/desliga)."""
        self.status = not self.status

    def to_dict(self):
        """
        Converte o aparelho para dicionário.
        
        Returns:
            dict: Representação em dicionário do aparelho
        """
        return {
            'id': self.id,
            'nome': self.nome,
            'consumo': self.consumo,
            'prioridade': self.prioridade,
            'status': self.status,
            'usuario_id': self.usuario_id,
            'codigo_externo': self.codigo_externo,
            'origem': self.origem
        }

    def __repr__(self):
        """Representação string do aparelho."""
        status_str = "ligado" if self.status else "desligado"
        return f'<Aparelho {self.nome} ({status_str})>'