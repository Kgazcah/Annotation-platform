from sqlalchemy import text
import hashlib

def hash(password):
    h = hashlib.new('sha256')
    h.update(password.encode('utf-8'))
    return h.hexdigest()

def listAll(db):
    import sys
    sys.path.append('../')
    from model import user
    result = db.session.execute(text("SELECT user_name, user_email, user_rol FROM user"))
    userList = []
    for row in result:
        userList.append(user.User(user_name=row.user_name, user_email=row.user_email, user_rol=row.user_rol))
    return userList

def addUser(db, username, password, email, role="usuario"):
    import sys
    sys.path.append('../')
    from model import user
    u = user.User(user_name=username, user_password=hash(password), user_email=email, user_rol=role)
    db.session.add(u)
    db.session.commit()

def deleteUser(db, username):
    db.session.execute(text("DELETE FROM user WHERE user_name=:key").bindparams(key=username))
    db.session.commit()

def findUser(db, username):
    import sys
    sys.path.append('../')
    from model import user
    result = db.session.execute(text("SELECT user_email, user_rol FROM user WHERE user_name=:key").bindparams(key=username))
    for row in result:
        return user.User(user_name=username, user_email=row.user_email, user_rol=row.user_rol)
    return None

def validateUser(db, username, password):
    import sys
    sys.path.append('../')
    from model import user
    result = db.session.execute(text("SELECT user_name, user_email, user_rol FROM user WHERE user_name=:username AND user_password=:password").bindparams(username=username, password=hash(password)))
    for row in result:
        return user.User(user_name=row.user_name, user_email=row.user_email, user_rol=row.user_rol)
    return None

def updateUser(db, username, email, rol):
    db.session.execute(text("UPDATE user SET user_email=:email, user_rol=:rol WHERE user_name=:key").bindparams(email=email,rol=rol,key=username))
    db.session.commit()