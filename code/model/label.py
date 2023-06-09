import sys

sys.path.append('../')
from app import db

class Labels(db.Model):
    label_name = db.Column(db.String(100), primary_key=True)
    label_value = db.Column(db.Integer, nullable=False)
    label_color = db.Column(db.String(6), nullable=False)
    label_text_color = db.Column(db.String(6), nullable=False)
    label_shortcut_key = db.Column(db.Integer, nullable=False)
    def __repr__(self):
        return f'<Label {self.label_name}>'

class LabelDataset(db.Model):
    label_name = db.Column(db.String(100), primary_key=True)
    name_dataset = db.Column(db.String(255), primary_key=True)
    def __repr__(self):
        return f'<LabelDataset {self.label_name},{self.name_dataset}>'
