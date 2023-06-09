import os
from flask import Flask, render_template, redirect, url_for, session, request, send_file
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import numpy as np
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from datetime import timedelta


application = Flask(__name__)
with application.app_context():
########################## CONFIG APP ##########################
    basedir = os.path.abspath(os.path.dirname(__file__))
    application.secret_key = b'f744ec1787c0997b4409e7e28425fc84dddf867a8a72edaed82954986d31dfab'
    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db/database.db')
    application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    application.config['SESSION_TYPE'] = 'filesystem'
    application.config['SESSION_FILE_DIR'] = os.path.join(basedir, 'bin/sessions/')
    db = SQLAlchemy(application)
    Session(application)

@application.before_request
def before_request():
    session.permanent = True
    application.permanent_session_lifetime = timedelta(minutes=10)
    delete_session_files()
    session.modified = True

########################## RUTAS PRINCIPALES ##########################

@application.route('/')
@application.route('/home')
def home():
    session['page'] = 'index'
    if 'username' in session and 'rol' in session:
        return redirect(url_for("datasetList"))
    session.clear()
    return render_template('index.html')

@application.route('/instructions')
def instructions():
    secret_name = request.args.get('dataset', None)
    if secret_name is not None:
        name = fileController.getNameURL(db, secret_name)
        session["read_instructions"] = True
        session["secret"] = secret_name
        session["labels"] = labelController.listAllbyDataset(db, name)
        #session.modified = True
        return render_template('instructions.html', labels=session["labels"])
    else:
        return redirect(url_for('not_found'))

@application.route('/thanks')
def thanks():
    user = None
    if 'username' in session:
        user = session['username']
    session["dataset"] = None
    session["dataset_labels"] = None
    session["dataset_name"] = None
    session["secret"] = None
    session['read_instructions'] = False
    session["labels"] = None
    session["times"] = None
    session["kappa"] = None
    if user is not None:
        session['username'] = user
    #session.modified = True
    return render_template('thanks.html')

@application.errorhandler(HTTPException)
def page_not_found(error=None):
    return redirect(url_for('not_found'))

@application.route('/not_found')
def not_found():
    return render_template('page_not_found.html'), 404

########################## RUTAS PARA USUARIOS ##########################

@application.route('/login', methods=['POST'])
def login():
    user = validate_login(username=request.form['username'], password=request.form['password'])
    if user is None:
        return render_template('index.html', msg_header='Failed to login', msg_error='Invalid username/password')
    else:
        session["username"]=user.user_name
        session["rol"]=user.user_rol
        session["email"]=user.user_email
        #session.modified = True
        return redirect(url_for('datasetList'))

@application.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    #session.modified = True
    return redirect(url_for('home'))

@application.route('/register', methods=['POST'])
def register():
    user = save_user(username=request.form['username'], password=request.form['password'], email=request.form['email'])
    if user:
        if session.get("username") is None:
            session["username"]=user.user_name
            session["rol"]=user.user_rol
            session["email"]=user.user_email
            #session.modified = True
        else:
            return redirect(url_for('usersList'))
    return redirect(url_for('home'))

@application.route('/users')
def users():
    session["page"] = "users"
    if 'username' in session and 'rol' in session and session["rol"] == "administrador":
        return render_template('users.html')
    else:
        return redirect(url_for("not_found"))

@application.route('/usersList')
def usersList():
    session["page"] = "users"
    if 'username' in session and 'rol' in session and session["rol"] == "administrador":
        return render_template("list.html", list=userController.listAll(db))
    else:
        return redirect(url_for("not_found"))

########################## RUTAS PARA DATASETS ##########################

@application.route('/dataset', methods=['POST', 'GET'])
def dataset():
    session["page"] = "dataset"
    if 'username' in session and 'rol' in session and session["rol"] == "administrador":
        if request.method == 'POST':
            dataset = request.files['dataset']
            dataset_name = secure_filename(dataset.filename)
            datasetList = datasetController.findDataset(db, name=dataset_name)
            if len(datasetList) > 0:
                # el dataset ya estaba guardado en la base de datos, enviarlo a la direccion que le corresponde
                URL_NAME = fileController.getFileURL(db, dataset_name)
                URL_NAME = "{}?dataset={}".format(url_for('instructions'), URL_NAME)
                return render_template('dataset.html', msg_header='Datos guardados!', msg_error='Para evaluar el dataset, comparte la siguiente URL:\n', msg_url=URL_NAME)
            print("checkbox:",request.form.get('no_control'))
            if request.form.get('no_control') is None:
                datasetController.addDataset(db, name=dataset_name, control=None, n_lines=0, chunk_size=int(request.form['num_lines_per_evaluation']), username=session["username"], kappa=float(request.form['kappa_limit_value']))
            else:
                control = request.files['control']
                control_name = secure_filename(control.filename)
                datasetController.addDataset(db, name=dataset_name, control=control_name, n_lines=0, chunk_size=int(request.form['num_lines_per_evaluation']), username=session["username"], kappa=float(request.form['kappa_limit_value']))
            datasetList = datasetController.findDataset(db, name=dataset_name)
            if len(datasetList) > 0:
                # dataset se acaba de guardar en la base de datos, guardar los archivos en el disco y enviarlo a la URL correspondiente
                URL_NAME = fileController.getFileURL(db, dataset_name)
                URL_NAME = "{}?dataset={}".format(url_for('instructions'), URL_NAME)
                # dataset.save(os.path.join("./db", datasetList[0].name_dataset))
                lines = dataset.readlines()
                datasetController.addLines(db, dataset_name, lines)
                if request.form.get('no_control') is not None:
                    control.save(os.path.join("./db", datasetList[0].name_control))
                datasetController.updateLines(db, dataset_name, len(lines))
                return render_template('dataset.html', msg_header='Datos guardados!', msg_error='Para evaluar el dataset, comparte la siguiente URL:\n', msg_url=URL_NAME)
            else:
                return render_template('dataset.html', msg_header='Error!', msg_error='No se han podido guardar los archivos seleccionados.')
        return render_template('dataset.html')
    else:
        return redirect(url_for("not_found"))

@application.route('/annotation', methods=['POST'])
def annotation():
    session["page"] = "dataset"
    secret_name = request.args.get('dataset', None)
    if session.get("dataset") is not None and session.get("dataset_labels") is not None and session.get("dataset_name") is not None and session.get("secret") is not None:
        name = fileController.getNameURL(db, secret_name)
        if session.get("dataset_name") != name:
            session["dataset"] = None
            session["dataset_labels"] = None
            session["dataset_name"] = None
            session["secret"] = None
            session['read_instructions'] = False
            session["labels"] = labelController.listAllbyDataset(db, name)
            session["times"] = np.zeros(len(session["labels"]))
            session["kappa"] = None
            #session.modified = True
            return redirect(url_for('annotation', dataset=secret_name), code=307)
        idx = request.args.get('phrase', None)
        if idx is None:
            idx = 0
        else:
            idx = int(idx)
        session["times"][idx] += float(request.args.get('clic', 0.)) / 1000 # time in seconds ...
        label = request.args.get('label', None)
        if label is not None:
            session["dataset_labels"][idx] = int(label)
            idx += 1
        p = sum(1 if x != -1 else 0 for x in session["dataset_labels"])
        if session.get("kappa") is not None:
            progress = int(((p + session["num_control"]) * 100.) / session["total_evals"])
        else:
            progress = int((p * 100.) / session["num_control"])
        if idx == len(session["dataset"]):
            idx = len(session["dataset"])-1
        #session.modified = True
        if progress == 100:
            return redirect(url_for('send_answers'), code=307)
        if idx == 0:
            if idx + 1 == len(session["dataset"]):
                return render_template('annotation.html', progress=session.get("kappa") is not None, labels=session["labels"], lab=session["dataset_labels"][idx], phrase=session["dataset"][idx][1], per=progress, URL=secret_name, idx=idx, prev_idx=-1, next_idx=-1)
            return render_template('annotation.html', progress=session.get("kappa") is not None, labels=session["labels"], lab=session["dataset_labels"][idx], phrase=session["dataset"][idx][1], per=progress, URL=secret_name, idx=idx, next_idx=1, prev_idx=-1)
        elif idx + 1 == len(session["dataset"]):
            return render_template('annotation.html', progress=session.get("kappa") is not None, labels=session["labels"], lab=session["dataset_labels"][idx], phrase=session["dataset"][idx][1], per=progress, URL=secret_name, idx=idx, prev_idx=idx-1, next_idx=-1)
        else:
            return render_template('annotation.html', progress=session.get("kappa") is not None, labels=session["labels"], lab=session["dataset_labels"][idx], phrase=session["dataset"][idx][1], per=progress, URL=secret_name, idx=idx, next_idx=idx+1, prev_idx=idx-1)
    else:
        if secret_name is None:
            return redirect(url_for("not_found"))
        name, control_dataset = getControlDatasetFromSecret(secret_name)
        if name is None or control_dataset is None:
            return redirect(url_for("not_found"))
        if control_dataset != "NO":
            session["kappa"] = None
            session["dataset"] = control_dataset
            num_times = len(control_dataset)
            session["dataset_labels"] = [-1 for _ in range(num_times)]
            session["dataset_name"] = name
            session["secret"] = secret_name
            session["labels"] = labelController.listAllbyDataset(db, name)
            session["num_control"] = num_times
            session["total_evals"] = datasetController.findDataset(db, name=name)[0].num_chunk_lines + num_times
        else:
            session["kappa"] = 1.
            session["num_control"] = 0
            session["dataset_name"] = name
            session["secret"] = secret_name
            session["labels"] = labelController.listAllbyDataset(db, name)
            session["dataset"], session["dataset_labels"] = getChunkDataset(session["dataset_name"])
            num_times = len(session["dataset_labels"])
            session["total_evals"] = num_times
        if num_times == 0:
            session["dataset"] = None
            session["dataset_labels"] = None
            session["dataset_name"] = None
            session["secret"] = None
            session['read_instructions'] = False
            session["labels"] = None
            session["times"] = None
            session["kappa"] = None
            return render_template('index.html', msg_header='¡Gracias por participar!', msg_error='Gracias por tu aporte, actualmente no hay datos disponibles. Si quieres seguir colaborando, puedes registrarte')
        session["times"] = np.zeros(num_times) # para guardar el tiempo entre clic de cada pregunta
        #session.modified = True
        return render_template('annotation.html', progress=session.get("kappa") is not None, labels=session["labels"], lab=session["dataset_labels"][0], phrase=session["dataset"][0][1], per=0, URL=secret_name, idx=0, next_idx=1, prev_idx=-1)

@application.route('/send_answers', methods=["POST"])
def send_answers():
    if session.get("dataset") is not None and session.get("dataset_labels") is not None and session.get("dataset_name") is not None and session.get("secret") is not None:
        for i in session["dataset_labels"]:
            if i == -1:
                return redirect(url_for('annotation', dataset=session["secret"]), code=307)
        mean_time = round(session["times"].mean(), 3)
        print("Tiempos por pregunta (en segundos):", session["times"])
        print("Tiempo promedio (en segundos):", mean_time)
        if session.get("kappa") is None:
            expert = [int(session["dataset"][i][-1]) for i in range(len(session["dataset"]))]
            k = kappa(expert, session["dataset_labels"])
            limit = getKappaLimit(session["dataset_name"])
            print("El valor Kappa obtenido es de:", round(k,3))
            saveTimes(True, session["dataset_name"], session["dataset"], session["dataset_labels"], session["times"], mean_time, expert, k)
            session["times"] = None
            #session.modified = True
            if k >= limit:
                session["kappa"] = k
                session["dataset"], session["dataset_labels"] = getChunkDataset(session["dataset_name"])
                dataset = datasetController.findDataset(db, name=session["dataset_name"])[0]
                num_lines = len(session["dataset_labels"])
                if num_lines != dataset.num_chunk_lines:
                    session["total_evals"] -= dataset.num_chunk_lines
                    session["total_evals"] += num_lines
                session["times"] = np.zeros(len(session["dataset"])) # para guardar el tiempo entre clic de cada pregunta
                #session.modified = True
                return redirect(url_for('annotation', dataset=session["secret"]), code=307)
        else:
            saveLabels(session["dataset_name"], session["dataset"], session["dataset_labels"])
            saveTimes(False, session["dataset_name"], session["dataset"], session["dataset_labels"], session["times"], mean_time)
            session["times"] = None
            #session.modified = True
    return redirect(url_for('thanks'))

@application.route('/datasetList')
def datasetList():
    session["page"] = "dataset"
    if 'username' in session and 'rol' in session:
        if session["rol"] == "administrador":
            return render_template("listDatasets.html", list=datasetController.listAll(db))
        else:
            return render_template("listDatasets.html", list=datasetController.listIncomplete(db))
    else:
        return redirect(url_for("not_found"))

@application.route('/results')
def results():
    session["page"] = "dataset"
    if 'username' in session and 'rol' in session:
        if session["rol"] == "administrador":
            return render_template("listEvaluadas.html", list=datasetController.listEvaluadas(db, request.args.get('dataset', None)))
    else:
        return redirect(url_for("not_found"))

@application.route('/download')
def downloadFile():
    session["page"] = "dataset"
    if 'username' in session and 'rol' in session:
        if session["rol"] == "administrador":
            if request.args.get('dataset') is not None:
                file_path = "./db/labeled/{}".format(request.args.get('dataset'))
                return send_file(file_path, as_attachment=True)
    return redirect(url_for("not_found"))

############################ RUTAS PARA LABELS ############################

@application.route('/labels', methods=["POST", "GET"])
def labels():
    session["page"] = "labels"
    if 'username' in session and 'rol' in session and session["rol"] == "administrador":
        if request.method == 'POST':
            if request.form['shortcut'] == 'sin_asignar':
                labelController.addLabel(db, name=request.form['name'], value=request.form['value'], color=request.form['color'], text_color=request.form['color_text'], key=-1)
            else:
                labelController.addLabel(db, name=request.form['name'], value=request.form['value'], color=request.form['color'], text_color=request.form['color_text'], key=request.form['shortcut'])
            return render_template("labeled.html", msg_header='Datos guardados!', msg_error='La etiqueta se ha creado correctamente.')
        return render_template("labeled.html")
    else:
        return redirect(url_for("not_found"))

@application.route('/labelsList')
def labelsList():
    session["page"] = "labels"
    if 'username' in session and 'rol' in session and session["rol"] == "administrador":
        return render_template("listLabels.html", list=labelController.listAll(db))
    else:
        return redirect(url_for("not_found"))

@application.route('/addDataset', methods=["GET", "POST"])
def addDatasetToLabel():
    session["page"] = "labels"
    label_name = request.args.get('label', None)
    if 'username' in session and 'rol' in session and session["rol"] == "administrador" and label_name is not None:
        if request.method == 'POST':
            for dataset in request.form.getlist('dataset'):
                labelController.addDatasetToLabel(db, name=label_name, dataset=dataset)
            return redirect(url_for("labelsList"))
        datasets = datasetController.listAll(db)
        list_added = labelController.listAllbyLabel(db, label_name)
        no_added = []
        for dataset in datasets:
            if dataset[0].name_dataset not in list_added:
                no_added.append(dataset)
        return render_template("label_dataset.html", label_name=label_name, list=no_added)
    else:
        return redirect(url_for("not_found"))

############################ ACCIONES COMUNES ############################

@application.route('/delete', methods=["POST"])
def delete():
    if "rol" not in session or session["rol"] != "administrador":
        return redirect(url_for("not_found"))
    label = request.form.get('label')
    if label is not None:
        if labelController.getLabel(db, name=label) is not None:
            labelController.deleteLabel(db, name=label)
        return redirect(url_for('labelsList'))
    dataset = request.form.get('dataset')
    if dataset is not None:
        dataset = datasetController.findDataset(db, name=dataset)
        if len(dataset) > 0:
            datasetController.deleteDataset(db, dataset[0].name_dataset, dataset[0].name_control, dataset[0].name_labeled)
            datasetController.removeDatasetLines(db, dataset[0].name_dataset)
        return redirect(url_for('datasetList'))
    user = request.form.get('user')
    if user is not None:
        if userController.findUser(db, username=user) is not None:
            userController.deleteUser(db, username=user)
        return redirect(url_for('usersList'))
    return redirect(url_for('home'))

@application.route('/edit', methods=["GET", "POST"])
def edit():
    if "rol" not in session or session["rol"] != "administrador":
        return redirect(url_for("not_found"))
    label = request.args.get('label')
    if label is not None:
        label = labelController.getLabel(db, name=label)
        if label is not None:
            if request.method == 'POST':
                labelController.editLabel(db, name=label.label_name, value=request.form['value'], color=request.form['color'], text_color=request.form['color_text'], shortcut=request.form['shortcut'])
            else:
                return render_template('edit.html', label=label)
        return redirect(url_for('labelsList'))
    dataset = request.args.get('dataset')
    if dataset is not None:
        dataset = datasetController.findDataset(db, name=dataset)
        if len(dataset) > 0:
            if request.method == 'POST':
                datasetController.updateDataset(db, name=dataset[0].name_dataset, chunk=int(request.form['num_lines_per_evaluation']), kappa=float(request.form['kappa_limit_value']))
            else:
                return render_template('edit.html', dataset=dataset[0])
        return redirect(url_for('datasetList'))
    user = request.args.get('user')
    if user is not None:
        user = userController.findUser(db, username=user)
        if user is not None:
            if request.method == 'POST':
                userController.updateUser(db, username=user.user_name, email=request.form['email'], rol=request.form['rol'])
            else:
                return render_template('edit.html', user=user)
        return redirect(url_for("usersList"))
    return redirect(url_for("not_found"))

############################ LOGICA DE APLICACION ############################

def kappa(y_true, y_pred):
    from sklearn.metrics import cohen_kappa_score
    k = cohen_kappa_score(y_true, y_pred)
    return k

def validate_login(username, password):
    return userController.validateUser(db, username=username, password=password)

def save_user(username, password, email):
    user = userController.findUser(db, username=username)
    if user is None:
        userController.addUser(db, username=username, password=password, email=email)
        user = userController.findUser(db, username=username)
    return user

def getControlDatasetFromSecret(URL):
    name = fileController.getNameURL(db, URL)
    if name is not None:
        control_dataset = fileController.getControlLinesFromDataset(db, name)
        if control_dataset != "NO_CONTROL":
            np.random.shuffle(control_dataset)
            return name, control_dataset
        else:
            return name, "NO"
    return None, None

def getChunkDataset(name):
    #chunk = fileController.getLinesFromDataset(db, name)
    chunk = datasetController.getChunk(db, name)
    # np.random.shuffle(chunk)
    return chunk, [-1 for _ in chunk]

def getKappaLimit(name):
    dataset = datasetController.findDataset(db, name=name)
    if len(dataset) > 0:
        return dataset[0].kappa_limit
    return -1

def saveLabels(name, values, labels):
    lines = [(values[i], x) for i, x in enumerate(labels)]
    fileController.saveLabeledLines(db, name, lines)

def delete_session_files():
    millisec = time.time() * 1000
    with application.app_context():
        for path in os.listdir(application.config['SESSION_FILE_DIR']):
            try:
                f_name = os.path.join(application.config['SESSION_FILE_DIR'], path)
                if os.path.exists(f_name):
                    diff = millisec - (os.path.getmtime(f_name) * 1000)
                    # eliminar archivos de sesión con tiempo mayor o igual a 15 minutes in milliseconds
                    if diff >= 900000:
                        print("Delete session file:", path)
                        os.remove(f_name)
            except:
                pass

def saveTimes(isControl, name_dataset, data, labels, times, mean_time, experts=None, kappa=None):
    dataset = datasetController.findDataset(db, name=name_dataset)
    if len(dataset) == 0:
        return False
    dataset = dataset[0]
    path = os.path.join(basedir, 'times/')
    if isControl:
        name = dataset.name_control.replace("control/","",1)
        f = open("{}/control/{}".format(path, name), "a")
        for i, t in enumerate(times):
            f.write("{}\t".format(data[i][0])) # ID
            f.write("{:.3f}\t".format(t)) # Time in Seconds
            f.write("{}\t".format(labels[i])) # Label
            f.write("{}\n".format(experts[i])) # Label expert
        q = open("{}/avg_control.txt".format(path), "a")
        q.write("{}\t{}\t{}\n".format(name, mean_time, kappa)) # mean time
    else:
        name = dataset.name_dataset
        f = open("{}/answers/{}".format(path, name), "a")
        for i, t in enumerate(times):
            f.write("{}\t".format(data[i][0])) # ID
            f.write("{:.3f}\t".format(t)) # Time in Seconds
            f.write("{}\n".format(labels[i])) # Label
        q = open("{}/avg_answers.txt".format(path), "a")
        q.write("{}\t{}\n".format(name, mean_time)) # mean time
    f.close()
    q.close()
    return True

########################## LANZAR LA APP ##########################

if __name__ == "__main__":
    import time
    from controller import userController, datasetController, fileController, labelController
    from model.createTables import createUserTable, createDatasetTable, createLabelsTable, createLabelDatasetTable, createDatasetLinesTable
    with application.app_context():
        createUserTable(application.config['SQLALCHEMY_DATABASE_URI'])
        createDatasetTable(application.config['SQLALCHEMY_DATABASE_URI'])
        createLabelsTable(application.config['SQLALCHEMY_DATABASE_URI'])
        createLabelDatasetTable(application.config['SQLALCHEMY_DATABASE_URI'])
        createDatasetLinesTable(application.config['SQLALCHEMY_DATABASE_URI'])
        admin = userController.findUser(db, username="admin")
        if admin is None:
            userController.addUser(db, username="admin", password="root", email="example@example.com", role="administrador")
        delete_session_files()
    application.run(debug=False, host='0.0.0.0', port=80)
