import sys
from sqlalchemy import text
sys.path.append('../')
from model import label

def listAll(db):
    result = db.session.execute(text("SELECT label_name, label_value, label_color, label_text_color, label_shortcut_key FROM labels"))
    labelList = []
    for row in result:
        if row.label_shortcut_key == -1:
            labelList.append(label.Labels(label_name=row.label_name, label_value=row.label_value, label_color=row.label_color, label_text_color=row.label_text_color, label_shortcut_key='Sin asignar'))
        else:
            labelList.append(label.Labels(label_name=row.label_name, label_value=row.label_value, label_color=row.label_color, label_text_color=row.label_text_color, label_shortcut_key=chr(row.label_shortcut_key)))
    return labelList

def listAllbyDataset(db, name):
    result = db.session.execute(text("SELECT label_name FROM label_dataset WHERE name_dataset=:key").bindparams(key=name))
    labels = []
    for row in result:
        labels.append(getLabel(db, row.label_name))
    return labels

def listAllbyLabel(db, name):
    result = db.session.execute(text("SELECT name_dataset FROM label_dataset WHERE label_name=:key").bindparams(key=name))
    datasets = []
    for row in result:
        datasets.append(row.name_dataset)
    return datasets

def addLabel(db, name, value, color, text_color, key):
    if getLabel(db, name) is None:
        l = label.Labels(label_name=name, label_value=int(value), label_color=color, label_text_color=text_color, label_shortcut_key=int(key))
        db.session.add(l)
        db.session.commit()

def addDatasetToLabel(db, name, dataset):
    sys.path.append('../')
    from controller import datasetController
    if len(datasetController.findDataset(db, name=dataset)) > 0 and getLabel(db, name) is not None:
        ld = label.LabelDataset(label_name=name, name_dataset=dataset)
        db.session.add(ld)
        db.session.commit()

def getLabel(db, name):
    result = db.session.execute(text("SELECT label_value, label_color, label_text_color, label_shortcut_key FROM labels WHERE label_name=:key").bindparams(key=name))
    for row in result:
        return label.Labels(label_name=name, label_value=row.label_value, label_color=row.label_color, label_text_color=row.label_text_color, label_shortcut_key=row.label_shortcut_key)
    return None

def editLabel(db, name, value, color, text_color, shortcut):
    if getLabel(db, name) is not None:
        db.session.execute(text("UPDATE labels SET label_value=:value, label_color=:color, label_text_color=:text_color, label_shortcut_key=:shortcut WHERE label_name=:key").bindparams(value=value, color=color, text_color=text_color, shortcut=int(shortcut), key=name))
        db.session.commit()
        return True
    else:
        return False

def deleteLabel(db, name):
    db.session.execute(text("DELETE FROM label_dataset WHERE label_name=:key").bindparams(key=name))
    db.session.execute(text("DELETE FROM labels WHERE label_name=:key").bindparams(key=name))
    db.session.commit()
