from sqlalchemy import text
from sqlalchemy.sql.expression import text

def listAll(db):
    import sys
    sys.path.append('../')
    from model import dataset
    import Cifrador
    cifrador = Cifrador.Cifrador()
    result = db.session.execute(text("SELECT name_dataset, name_control, name_labeled, num_lines_dataset, num_assigned_lines, num_chunk_lines, is_fully_labeled, created_by, kappa_limit FROM dataset"))
    datasetList = []
    for row in result:
        datasetList.append((dataset.Dataset(name_dataset=row.name_dataset, name_control=row.name_control, name_labeled=row.name_labeled, num_lines_dataset=row.num_lines_dataset, num_assigned_lines=row.num_assigned_lines, num_chunk_lines=row.num_chunk_lines, is_fully_labeled=row.is_fully_labeled, created_by=row.created_by, kappa_limit=row.kappa_limit), cifrador.encrypt(row.name_dataset)))
    return datasetList

def listIncomplete(db):
    import sys
    sys.path.append('../')
    import Cifrador
    cifrador = Cifrador.Cifrador()
    result = db.session.execute(text("SELECT name_dataset FROM dataset WHERE num_lines_dataset > num_assigned_lines"))
    datasetList = []
    count = 0
    alias = "conjunto de datos {} para etiquetar"
    for row in result:
        count += 1
        name = row.name_dataset
        datasetList.append((alias.format(count), cifrador.encrypt(name)))
    return datasetList

def addDataset(db, name, control, n_lines, chunk_size, username, kappa):
    import sys
    sys.path.append('../')
    from model import dataset
    if control is None:
        d = dataset.Dataset(name_dataset=name, name_control="NO_CONTROL", name_labeled="labeled/"+name, num_lines_dataset=n_lines, num_assigned_lines=0, num_chunk_lines=chunk_size, is_fully_labeled="no", created_by=username, kappa_limit=kappa)
    else:
        d = dataset.Dataset(name_dataset=name, name_control="control/"+control, name_labeled="labeled/"+name, num_lines_dataset=n_lines, num_assigned_lines=0, num_chunk_lines=chunk_size, is_fully_labeled="no", created_by=username, kappa_limit=kappa)
    db.session.add(d)
    db.session.commit()

def deleteDataset(db, dataset, control, labeled):
    import sys
    sys.path.append('../')
    from controller import fileController
    db.session.execute(text("DELETE FROM label_dataset WHERE name_dataset=:key").bindparams(key=dataset))
    db.session.execute(text("DELETE FROM dataset WHERE name_dataset=:key").bindparams(key=dataset))
    db.session.commit()
    fileController.deleteDataset(dataset, control, labeled)

def findDataset(db, name=None, username=None):
    import sys
    sys.path.append('../')
    from model import dataset
    result = []
    res = []
    if name is None and username is not None:
        result = db.session.execute(text("SELECT name_dataset, name_control, name_labeled, num_lines_dataset, num_assigned_lines, num_chunk_lines, is_fully_labeled, created_by, kappa_limit FROM dataset WHERE created_by=:key").bindparams(key=username))
    elif name is not None and username is None:
        result = db.session.execute(text("SELECT name_dataset, name_control, name_labeled, num_lines_dataset, num_assigned_lines, num_chunk_lines, is_fully_labeled, created_by, kappa_limit FROM dataset WHERE name_dataset=:key").bindparams(key=name))
    elif name is not None and username is not None:
        result = db.session.execute(text("SELECT name_dataset, name_control, name_labeled, num_lines_dataset, num_assigned_lines, num_chunk_lines, is_fully_labeled, created_by, kappa_limit FROM dataset WHERE name_dataset=:name AND created_by=:user").bindparams(name=name, user=username))
    for row in result:
        res.append(dataset.Dataset(name_dataset=row.name_dataset, name_control=row.name_control, name_labeled=row.name_labeled, num_lines_dataset=row.num_lines_dataset, num_assigned_lines=row.num_assigned_lines, num_chunk_lines=row.num_chunk_lines, is_fully_labeled=row.is_fully_labeled, created_by=row.created_by, kappa_limit=row.kappa_limit))
    return res

def updateNumLines(db, name, new_lines):
    db.session.execute(text("UPDATE dataset SET num_assigned_lines=:lines WHERE name_dataset=:name").bindparams(lines=new_lines, name=name))
    db.session.commit()

def updateLines(db, name, new_lines):
    db.session.execute(text("UPDATE dataset SET num_lines_dataset=:lines WHERE name_dataset=:name").bindparams(lines=new_lines, name=name))
    db.session.commit()

def getCurrentLines(db, name):
    dataset = findDataset(db, name)
    if len(dataset) > 0:
        return dataset[0].num_assigned_lines
    return -1

def updateDataset(db, name, chunk, kappa):
    db.session.execute(text("UPDATE dataset SET num_chunk_lines=:chunk, kappa_limit=:kappa WHERE name_dataset=:name").bindparams(chunk=chunk, kappa=kappa, name=name))
    db.session.commit()

def existeLinea(db, name, line):
    result = db.session.execute(text("SELECT * FROM dataset_lines WHERE name_dataset=:dataset AND line=:line").bindparams(dataset=name,line=line))
    return len(result.all()) > 0

def addLines(db, name, lines):
    import sys
    sys.path.append('../')
    from model import lines_dataset
    line_num = 0
    for line in lines:
        line = line[:-1] # eliminar el salto de linea
        if not existeLinea(db, name, line):
            line_num += 1
            db.session.add(lines_dataset.DatasetLines(name_dataset=name, line=line, status="libre", line_number=line_num))
    db.session.commit()

def removeDatasetLines(db, dataset):
    db.session.execute(text("DELETE FROM dataset_lines WHERE name_dataset=:key").bindparams(key=dataset))
    db.session.commit()

def getChunk(db, datasetName):
    from datetime import datetime, timedelta, timezone
    datasetList = findDataset(db, name=datasetName)
    chunk = []
    if len(datasetList) > 0:
        dataset = datasetList[0]
        result = db.session.execute(text("SELECT * FROM dataset_lines WHERE name_dataset=:key AND status='asignada'").bindparams(key=datasetName))
        if dataset.num_chunk_lines > 15:
            # timedelta(seconds=-60 * dataset.num_chunk_lines)
            # cada frase corresponde a 60 segundos de tiempo, por lo que evaluar el chunk tomara
            # un minuto por cada frase del chunk
            limit = datetime.strptime((datetime.now(tz=timezone.utc) + timedelta(minutes=-dataset.num_chunk_lines)).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
        else:
            limit = datetime.strptime((datetime.now(tz=timezone.utc) + timedelta(minutes=-15)).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
        lines = []
        for row in result:
            update = datetime.strptime(row.status_update, '%Y-%m-%d %H:%M:%S')
            if update < limit:
                print("linea liberada:", row.line, "update:", update, "limit:", limit)
                lines.append(row.line)
        for line in lines:
            db.session.execute(text("UPDATE dataset_lines SET status='libre' WHERE status='asignada' AND name_dataset=:name AND line=:line").bindparams(name=datasetName, line=line))
            db.session.commit()
        result = db.session.execute(text("SELECT line FROM dataset_lines WHERE name_dataset=:key AND status='libre' ORDER BY line_number ASC LIMIT :chunk").bindparams(key=datasetName, chunk=dataset.num_chunk_lines))
        lines = []
        for row in result:
            #print("DB_LINE:", row.line)
            lines.append(row.line)
            chunk.append(row.line.decode("utf-8").split("\t"))
        for line in lines:
            now = datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            db.session.execute(text("UPDATE dataset_lines SET status='asignada', status_update=:now WHERE name_dataset=:name AND status='libre' AND line=:line").bindparams(now=now, name=datasetName, line=line))
            db.session.commit()
    return chunk

def markAsAsigned(db, dataset, lines=[]):
    for line in lines:
        phrase = ''
        for i, texto in enumerate(line[0]):
            if i + 1 < len(line[0]):
                phrase += texto + '\t'
            else:
                phrase += texto
        phrase = phrase.encode('utf-8')
        db.session.execute(text("UPDATE dataset_lines SET status='evaluada' WHERE name_dataset=:name AND line=:linea").bindparams(name=dataset,linea=phrase))
        db.session.commit()

def listEvaluadas(db, dataset):
    import sys
    sys.path.append('../')
    from controller import fileController
    result = db.session.execute(text("SELECT * FROM dataset_lines WHERE status='evaluada' AND name_dataset=:name").bindparams(name=dataset))
    IDs = []
    for row in result:
        id_frase = row.line.decode("utf-8").split("\t")
        IDs.append(id_frase[0])
    results = []
    if len(IDs) > 0:
        lineas = fileController.lineasEvaluadas(dataset)
        for id in IDs:
            for linea in lineas:
                if id == linea[1]:
                    results.append(linea)
                    break
    return results
