import web
from web import form
from mako.template import Template
from mako.runtime import Context
from StringIO import StringIO
import re
import anydbm
from hashlib import sha1



urls = ('/logout', 'Logout',
        '/profile', 'Profile',
        '/(.*)', 'Index'
        )

render = web.template.render('templates/')
mainTemplate = Template(filename='templates/index.html')

usersDB = anydbm.open('Users.db', 'c')
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
    try:
        if(usersDB[str(userName + ".name")]):
            return False
    except KeyError:
        return True
    
    
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
    usersDB[str(nickName) + ".name"] = str(name);
    usersDB[str(nickName) + ".surname"] = str(surname)
    usersDB[str(nickName) + ".dni"] = str(dni)
    usersDB[str(nickName) + ".email"] = str(email)
    usersDB[str(nickName) + ".day"] = str(day)
    usersDB[str(nickName) + ".month"] = str(month)
    usersDB[str(nickName) + ".year"] = str(year)
    usersDB[str(nickName) + ".address"] = str(address)
    usersDB[str(nickName) + ".payway"] = str(payWay)
    if(password):
        usersDB[str(nickName) + ".password"] = str(PasswordHash(password).pw)

def loadUser(userName):
    userName = userName.lower()
    userData = {"name" : usersDB[str(userName + ".name")],
                "surname" : usersDB[str(userName + ".surname")],
                "dni" : usersDB[str(userName + ".dni")],
                "email" : usersDB[str(userName + ".email")],
                "day" : int(usersDB[str(userName + ".day")]),
                "month" : int(usersDB[str(userName + ".month")]),
                "year" : int(usersDB[str(userName + ".year")]),
                "address" : usersDB[str(userName + ".address")],
                "payway" : usersDB[str(userName + ".payway")]
                }
    return userData
#class Formulario:
#    def GET(self): 
#        form = registerForm()
#        return render.formtest(form)
#
#    def POST(self): 
#        form = registerForm()
#        if not form.validates():
#            return render.formtest(form)
#        else:
#            session.user = "pepe"
#            web.Redirect("/")
#            return '<p>Registro llevado a cabo correctamente</p>'
        

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
    try:
        if usersDB[str(userName.lower() + ".password")] == PasswordHash(password).pw:
            return True
    except KeyError:
        return False
    
    return False

class Profile:
    def GET(self):
        if(session.user == "anonymous"):
            return "Seccion restringida"
        
        form = profileForm()
        userName = str(session.user).lower()
        
        userData = loadUser(userName)
        
        try:
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
            
            #form.validators.append(form.Validator("Las constrasenias no coiniciden", lambda x: form.d.password == None or (form.d.password != None and form.d.password == form.d.passwordConfirm)))
            
        except KeyError:
            return "Ha ocurrido un error, por favor avise a un administrador"
        
        #saveUser(form.d.nickName, form.d.name, form.d.surname, form.d.dni, form.d.email, form.d.day, form.d.month, form.d.year, form.d.address, form.d.password, form.d.payWay)
        
        content = render.formtest(form, "Guardar")
        return getContent(content)
        
    def POST(self):
        if(session.user == "anonymous"):
            return "Seccion restringida"
        
        form = profileForm()
        if form.validates():
            saveUser(session.user, form.d.name, form.d.surname, form.d.dni, form.d.email, form.d.day, form.d.month, form.d.year, form.d.address, form.d.payWay, form.d.password)
            print("LLEGOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOoo")
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
            #if session.user == "anonymous":
            #    content = render.formtest(form)
            #else:
            #    content = render.alreadyLoged()
        
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
            #if form.validates():
                #try:
                    #if usersDB[str(form.d.nickName + ".password")] == form.d.password:
                    #    session.user = form.d.nickName
                #except KeyError:
                #    print("El usuario " + session.user + " no existe en la base de datos o la contrasenia es incorrecta")
        
        
        
        
# NO QUIERE FUNCIONAR       
#        form = logForm()
#        if "nickName" in form.d:
#            if form.validates():
#                session.user = form.d.nickName
#            
#        elif name == "register":
#            form = registerForm()
#            if form.validates():
#                newUser(form.d.nickName, form.d.name, form.d.surname, form.d.dni, form.d.email, form.d.day, form.d.month, form.d.year, form.d.address, form.d.password, form.d.payWay)
#                session.user = form.d.nickName
#                raise web.seeother("/")
#            content = getRegisterForm(form)
        
        return getContent(content, registering)



#class DBManager:
#    cache = None
#    prueba = None
#    
#    def printame(self):
#        print(DBManager.prueba)
#    def open(self):
#        print("ENTRA")
#        DBManager.prueba = "LKJSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSFASF"
#        DBManager.cache = anydbm.open('Users.db', 'c')  

#class Register:
#    def GET(self):
#        form = registerForm()
#        return getForm(form)
#    def POST(self):
#        form = registerForm()
#        if form.validates():
#            session.user = form.d.nickName
#            raise web.seeother("/")
#        return getForm(form)


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
