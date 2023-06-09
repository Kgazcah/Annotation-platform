import sys
import enum
from sqlalchemy import Enum #, ForeignKey

sys.path.append('../')
from app import db

class yes_no_enum(enum.Enum):
    yes = "yes"
    no = "no"

class Dataset(db.Model):
    name_dataset = db.Column(db.String(255), primary_key=True)
    name_control = db.Column(db.String(255), nullable=False)
    name_labeled = db.Column(db.String(255), nullable=False)
    num_lines_dataset = db.Column(db.Integer, nullable=False)
    num_assigned_lines = db.Column(db.Integer, nullable=False)
    num_chunk_lines = db.Column(db.Integer, nullable=False)
    is_fully_labeled = db.Column(Enum(yes_no_enum))
    created_by = db.Column(db.String(32), nullable=False)# ForeignKey('user.user_name'),
    kappa_limit = db.Column(db.Float, nullable=False)
    def __repr__(self):
        return f'<Dataset {self.name_dataset}>'

