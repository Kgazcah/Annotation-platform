import sys
import enum
from sqlalchemy import Enum

sys.path.append('../')
from app import db

class role_enum(enum.Enum):
    administrador = "administrador"
    usuario = "usuario"

class User(db.Model):
    user_name = db.Column(db.String(32), primary_key=True)
    user_password = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(100), unique=True, nullable=False)
    user_rol = db.Column(Enum(role_enum))
    def __repr__(self):
        return f'<User {self.user_name}>'

