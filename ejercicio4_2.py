import web
from web import form
from mako.template import Template
from mako.runtime import Context
from StringIO import StringIO
import re
from hashlib import sha1
from pymongo import MongoClient



urls = ('/logout', 'Logout',
        '/profile', 'Profile',
        '/(.*)', 'Index'
        )

render = web.template.render('templates/')
mainTemplate = Template(filename='templates/index.html')

mongoClient = MongoClient()
mongoDB = mongoClient.daiDB1

RESTRICTEDUSERS = ["anonymous", "admin", "root"]
app = web.application(urls, globals())

if web.config.get('_session') is None:
    session = web.session.Session(app, web.session.DiskStore('sessions'),initializer={'user': 'anonymous','pag1' : '','pag2' : '','pag3' : ''})
    web.config._session = session
else:
    session = web.config._session

def dia():
    dia = []
    for i in range(1, 32):
        dia.append((i, i))
    return dia

def mes():
    mes = []
    for i in range(1, 13):
        mes.append((i, i))
    return mes

def anio():
    anio = []
    for i in range(1980, 2014):
        anio.append((i, i))
    return anio

def checkAvail(userName):
    
    if userName in RESTRICTEDUSERS:
        return False
    if(loadUser(userName) == None):
        return True
    
    return False
    
    
def confirmarFecha(dia, mes, anio):
    meses30 = [4,6,9,11]
    meses28 = 2
    if dia <= 28:
        return True
    for i in meses30:
        if mes == i and dia > 30:
            return False
    if mes == meses28:
        if anio%4 != 0 :
            return False
        else: 
            if dia > 29:
                return False
    return True

def confirmarTarjeta(tarjeta):
    a = re.compile(r'([0-9]{4}) ([0-9]{4}) ([0-9]{4}) ([0-9]{4})|([0-9]{4})-([0-9]{4})-([0-9]{4})-([0-9]{4})') 
    return a.match(tarjeta)

def confirmarEmail(email):
    a = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}\b') 
    return a.match(email)

logForm = form.Form(
                    form.Textbox("nickName", form.notnull, description = "Nick"),
                    form.Password("password", form.Validator("La contrasenia debe tener mas de 7 caracteres", lambda i: len(i)>7), description = "Contrasenia"),
                    form.Button("Login"),
                    validators = [form.Validator("EL nombre de usuario o contrasenia son incorrectos", lambda i: checkAuth(i.nickName, i.password))]
                    )

registerForm = form.Form( 
    form.Textbox("nickName", form.Validator("El nombre de usuario debe tener al menos 5 caracteres", lambda i: len(i) > 4), form.Validator("Nombre de usuario no disponible", lambda i: checkAvail(i)), description = "Nick"),
    form.Textbox("name", form.notnull, description = "Nombre"),
    form.Textbox("surname", form.notnull, description = "Apellidos"), 
    form.Textbox("dni", form.notnull, description = "D.N.I."),
    form.Textbox("email", form.Validator("Direccion de correo incorrecta", lambda i: confirmarEmail(i)), description = "E-mail"),
    form.Dropdown('day', dia(), description = "Dia de nacimiento"),
    form.Dropdown('month', mes(), description = "Mes de nacimiento"),
    form.Dropdown('year', anio(), description = "Anio de nacimiento"),
    form.Textarea("address", form.notnull, description = "Direccion"),
    form.Password("password", form.Validator("La contrasenia debe tener mas de 7 caracteres", lambda i: len(i)>7), description = "Contrasenia"),
    form.Password("passwordConfirm", description = "Repite contrasenia"),
    #form.Textbox("nTarjeta", form.Validator("Numero de tarjeta incorrecto", lambda i: confirmarTarjeta(i)), description = "Numero de tarjeta"),
    form.Checkbox("accept", form.Validator("Debes aceptar la clausula", lambda i:"accept" not in i)),
    form.Radio("payWay", ["Visa", "Paypal"], form.Validator("Debe elegir la forma de pago", lambda i: len(i) > 0), description = "Forma de pago"),
    validators = [form.Validator("Fecha de nacimiento incorrecta", lambda i: confirmarFecha(int(i.day), int(i.month), int(i.year)) == True),
                  form.Validator("Las constrasenias no coiniciden", lambda i: i.password == i.passwordConfirm)]
                         )

profileForm = form.Form( 
    form.Textbox("nickName", disabled = "on", description = "Nick"),
    form.Textbox("name", form.notnull, description = "Nombre"),
    form.Textbox("surname", form.notnull, description = "Apellidos"), 
    form.Textbox("dni", form.notnull, description = "D.N.I."),
    form.Textbox("email", form.Validator("Direccion de correo incorrecta", lambda i: confirmarEmail(i)), description = "E-mail"),
    form.Dropdown('day', dia(), description = "Dia de nacimiento"),
    form.Dropdown('month', mes(), description = "Mes de nacimiento"),
    form.Dropdown('year', anio(), description = "Anio de nacimiento"),
    form.Textarea("address", form.notnull, description = "Direccion"),
    form.Password("password", description = "Contrasenia"),
    form.Password("passwordConfirm", description = "Repite contrasenia"),
    #form.Textbox("nTarjeta", form.Validator("Numero de tarjeta incorrecto", lambda i: confirmarTarjeta(i)), description = "Numero de tarjeta"),
    #form.Checkbox("accept", "checked", disabled = "on", form.Validator("Debes aceptar la clausula", lambda i:"accept" not in i)),
    form.Radio("payWay", ["Visa", "Paypal"], form.Validator("Debe elegir la forma de pago", lambda i: len(i) > 0), description = "Forma de pago"),
    validators = [form.Validator("Fecha de nacimiento incorrecta", lambda i: confirmarFecha(int(i.day), int(i.month), int(i.year)) == True),
                  form.Validator("Las constrasenias no coiniciden", lambda i: not i.password or i.password == i.passwordConfirm)]
                         )

def saveUser(nick, name, surname, dni, email, day, month, year, address, payWay, password=False):
    #usersDB[str(nick)] = str(nick)
    print("GUARDO A: " + str(nick))
    print("de Name: " + str(name))
    nickName = str(nick).lower()
    
    if not mongoDB.users.find_one({"nickName":nickName}):     
        userData = {
                    "nickName" : nickName,
                    "name" : str(name),
                    "surname" : str(surname),
                    "dni" : str(dni),
                    "email" : str(email),
                    "day" : str(day),
                    "month" : str(month),
                    "year" : str(year),
                    "address" : str(address),
                    "payway" : str(payWay),
                    "password" : str(PasswordHash(password).pw)
                    }
        
        
        
        mongoDB.users.insert(userData)
    else:
        print("LKJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJj")
        userData = {
                    "name" : str(name),
                    "surname" : str(surname),
                    "dni" : str(dni),
                    "email" : str(email),
                    "day" : str(day),
                    "month" : str(month),
                    "year" : str(year),
                    "address" : str(address),
                    "payway" : str(payWay)
                }
        if(password):
            userData["password"] = str(PasswordHash(password).pw)
            
        mongoDB.users.update(
                             {"nickName" : nickName},
                                {"$set" : userData
                                 }
                             )

def loadUser(userName):
    userName = userName.lower()
    return mongoDB.users.find_one({"nickName" : userName})
        

def getRegisterForm(form):
    if session.user == "anonymous":
        content = render.formtest(form)
    else:
        content = render.alreadyLoged()
    
    return content
    #return getContent(content)

def getHistory():
    separator = ' -> '
    nav = session.pag1

    if(session.pag2 != ''):
        nav =  session.pag2 + separator + nav
    if(session.pag3 != ''):
        nav = session.pag3 + separator + nav

    return nav

def getContent(content, registering=False):
    form = logForm()
    buffer = StringIO()
    if(registering):
        contexto = Context(buffer, name=session.user, logo="static/images/logo.png", nav=getHistory(), data=content, logModule="")
    else:
        contexto = Context(buffer, name=session.user, logo="static/images/logo.png", nav=getHistory(), data=content, logModule=render.logModule(session.user, form))
    mainTemplate.render_context(contexto)
    return buffer.getvalue()

def addHistory(name):
    if(session.user != "anonymous"):
        session.pag3 = session.pag2
        session.pag2 = session.pag1
        session.pag1 = '<a href="' + web.ctx.home + "/" + name + '">' + name.split('.', 1)[0] + '</a>';

def checkAuth(userName, password):
    userData = loadUser(userName)
    
    if userData != None and userData["password"] == PasswordHash(password).pw:
        return True
    
    return False

class Profile:
    def GET(self):
        if(session.user == "anonymous"):
            return "Seccion restringida"
        
        form = profileForm()
        userName = str(session.user).lower()
        
        userData = loadUser(userName)
        
        form.get("nickName").value = session.user
        form.get("name").value = userData["name"]
        form.get("surname").value = userData["surname"]
        form.get("dni").value = userData["dni"]
        form.get("email").value = userData["email"]
        form.get("day").value = int(userData["day"])
        form.get("month").value = int(userData["month"])
        form.get("year").value = int(userData["year"])
        form.get("address").value = userData["address"]
        form.get("payWay").value = userData["payway"]
        form.get("password").value = ""
        form.get("passwordConfirm").value = ""
        
        content = render.formtest(form, "Guardar")
        return getContent(content)
        
    def POST(self):
        if(session.user == "anonymous"):
            return "Seccion restringida"
        
        form = profileForm()
        if form.validates():
            saveUser(session.user, form.d.name, form.d.surname, form.d.dni, form.d.email, form.d.day, form.d.month, form.d.year, form.d.address, form.d.payWay, form.d.password)
            #content = render.formtest(form, "Guardar")
            return self.GET()
        else:            
            content = render.formtest(form, "Guardar")
        
        return getContent(content)
        
class Index:
    def GET(self, name):
        registering = False;
            
        addHistory(name)
        
        content = render.defaultContent()
        
        if name == "register":
            form = registerForm()
            content = getRegisterForm(form)
            registering = True
        
        return getContent(content, registering)
    def POST(self, name):
        registering = False
        content = render.defaultContent()
        if name == "register":
            registering = True
            form = registerForm()
            if form.validates():
                saveUser(form.d.nickName, form.d.name, form.d.surname, form.d.dni, form.d.email, form.d.day, form.d.month, form.d.year, form.d.address, form.d.payWay, form.d.password)
                session.user = form.d.nickName
                #newUser(form.d.nickName, form.d.name, form.d.surname, form.d.dni, form.d.email, form.d.day, form.d.month, form.d.year, form.d.address, form.d.password, form.d.payWay)
                raise web.seeother("/")
            else:
                content = getRegisterForm(form)
        else:
            form = logForm()
            if(form.validates()):
                session.user = form.d.nickName
        
        return getContent(content, registering)






# Puede ser sustituida por una funcion, actualmente no se aproveche la clase
class PasswordHash(object):
    def __init__(self, password):
        self.pw = sha1(password).hexdigest()
    def check_password(self, password):
        return self.pw == sha1(password).hexdigest()
        

class Logout:
    def GET(self):
        session.kill()
        raise web.seeother("/")
        
if __name__=="__main__":
    web.internalerror = web.debugerror
#    DBManager().open()
    app.run()
