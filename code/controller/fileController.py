def getLinesFromDataset(db, name):
    from controller import datasetController
    dataset = datasetController.findDataset(db, name)
    res = []
    if len(dataset) > 0:
        dataset = dataset[0]
        lines = open("./db/{}".format(dataset.name_dataset), "r", encoding="utf-8").readlines()
        if dataset.num_assigned_lines + dataset.num_chunk_lines < dataset.num_lines_dataset:
            for line in lines[dataset.num_assigned_lines:dataset.num_chunk_lines+dataset.num_assigned_lines]:
                res.append(line[:-1].split("\t"))
        else:
            for line in lines[dataset.num_assigned_lines:]:
                res.append(line[:-1].split("\t"))
    return res

def getControlLinesFromDataset(db, name):
    from controller import datasetController
    dataset = datasetController.findDataset(db, name)
    res = []
    if len(dataset) > 0:
        dataset = dataset[0]
        if dataset.name_control == "NO_CONTROL":
            return dataset.name_control
        for line in open("./db/{}".format(dataset.name_control), "r", encoding="utf-8").readlines():
            res.append(line[:-1].split("\t"))
    return res

def saveLabeledLines(db, name, lines=[]):
    from controller import datasetController
    if(len(lines) > 0):
        dataset = datasetController.findDataset(db, name)
        if len(dataset) > 0:
            dataset = dataset[0]
            datasetController.markAsAsigned(db, name, lines)
            datasetController.updateNumLines(db, name, dataset.num_assigned_lines + len(lines))
            csv = open("./db/{}".format(dataset.name_labeled), "a", encoding="utf-8")
            for line in lines:
                # los datos etiquetados se guardan con el formato:
                # <clase><tab><ID><tab><texto><salto-de-linea>
                csv.write("{}\t{}\t{}\n".format(line[-1], line[0][0], line[0][1]))
            csv.close()
            return True
    return False

def getFileURL(db, name):
    from controller import datasetController
    dataset = datasetController.findDataset(db, name)
    if len(dataset) > 0:
        import sys
        sys.path.append('../')
        import Cifrador
        cifrador = Cifrador.Cifrador()
        URL = cifrador.encrypt(name)
        return URL
    return "/"

def getNameURL(db, URL):
    from controller import datasetController
    import sys
    sys.path.append('../')
    import Cifrador
    cifrador = Cifrador.Cifrador()
    name = cifrador.decrypt(URL)
    dataset = datasetController.findDataset(db, name)
    if len(dataset) > 0:
        return name
    return None

def getNumLinesFromDataset(db, name):
    from controller import datasetController
    dataset = datasetController.findDataset(db, name)
    if len(dataset) > 0:
        dataset = dataset[0]
        return len(open("./db/{}".format(dataset.name_dataset), "r", encoding="utf-8").readlines())
    return -1

def deleteDataset(dataset, control, labeled):
    import os
    file_path = "./db/{}".format(dataset)
    if os.path.exists(file_path):
        os.remove(file_path)
    if control != "NO_CONTROL":
        file_path = "./db/{}".format(control)
        if os.path.exists(file_path):
            os.remove(file_path)
    file_path = "./db/{}".format(labeled)
    if os.path.exists(file_path):
        os.remove(file_path)

def lineasEvaluadas(dataset):
    import os
    lineas = []
    file_path = "./db/labeled/{}".format(dataset)
    if os.path.exists(file_path):
        for linea in open(file_path, 'r', encoding="utf-8").readlines():
            x = linea.strip(" \r\n")
            if x:
                lineas.append(x.split("\t"))
    return lineas