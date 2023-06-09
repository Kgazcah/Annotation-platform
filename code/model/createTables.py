from sqlalchemy import create_engine, MetaData, Column, String, Table, Integer, Float, Enum, DateTime, BigInteger #ForeignKey
from sqlalchemy.sql import func
import enum

class role_enum(enum.Enum):
    administrador = "administrador"
    usuario = "usuario"

class yes_no_enum(enum.Enum):
    yes = "yes"
    no = "no"

class line_status_enum(enum.Enum):
    libre = "libre"
    asignada = "asignada"
    evaluada = "evaluada"

def createUserTable(app):
    engine = create_engine(app)
    metadata_obj = MetaData()
    user = Table('user', metadata_obj,
        Column('user_name', String(32), primary_key=True),
        Column('user_password',String(100), nullable=False),
        Column('user_email',String(100), unique=True, nullable=False),
        Column('user_rol',Enum(role_enum))
    )
    user.create(engine, checkfirst=True)

def createDatasetTable(app):
    engine = create_engine(app)
    metadata_obj = MetaData()
    dataset = Table('dataset', metadata_obj,
        Column('name_dataset', String(255), primary_key=True),
        Column('name_control', String(255), nullable=False),
        Column('name_labeled', String(255), nullable=False),
        Column('num_lines_dataset', Integer, nullable=False),
        Column('num_chunk_lines', Integer, nullable=False),
        Column('num_assigned_lines', Integer, nullable=False),
        Column('is_fully_labeled', Enum(yes_no_enum), nullable=False),
        Column('created_by', String(32), nullable=False), #, ForeignKey('user.user_name')
        Column('kappa_limit', Float, nullable=False)
    )
    dataset.create(engine, checkfirst=True)

def createLabelsTable(app):
    engine = create_engine(app)
    metadata_obj = MetaData()
    labels = Table('labels', metadata_obj,
        Column('label_name', String(100), primary_key=True),
        Column('label_value', Integer, nullable=False),
        Column('label_color', String(6), nullable=False),
        Column('label_text_color', String(6), nullable=False),
        Column('label_shortcut_key', Integer, nullable=False),
    )
    labels.create(engine, checkfirst=True)

def createLabelDatasetTable(app):
    engine = create_engine(app)
    metadata_obj = MetaData()
    label_dataset = Table('label_dataset', metadata_obj,
        Column('label_name', String(100), primary_key=True),
        Column('name_dataset', String(255), primary_key=True),
    )
    label_dataset.create(engine, checkfirst=True)

def createDatasetLinesTable(app):
    engine = create_engine(app)
    metadata_obj = MetaData()
    lines_dataset = Table('dataset_lines', metadata_obj,
        Column('name_dataset', String(255), primary_key=True),
        Column('line', String(512), primary_key=True),
        Column('status', Enum(line_status_enum), nullable=False),
        Column('status_update', DateTime, server_default=func.now()),
        Column('line_number', BigInteger, nullable=False),
    )
    lines_dataset.create(engine, checkfirst=True)
