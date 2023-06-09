import sys
import enum
from sqlalchemy import Enum
from sqlalchemy.sql import func

sys.path.append('../')
from app import db

class line_status_enum(enum.Enum):
    libre = "libre"
    asignada = "asignada"
    evaluada = "evaluada"

class DatasetLines(db.Model):
    name_dataset = db.Column(db.String(255), primary_key=True)
    line = db.Column(db.String(512), primary_key=True)
    status = db.Column(Enum(line_status_enum))
    line_number = db.Column(db.BigInteger, nullable=False)
    status_update = db.Column(db.DateTime, server_default=func.now())
    def __repr__(self):
        return f'<DatasetLines {self.name_dataset}|{self.line}>'
