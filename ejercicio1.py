import web
from web import form
import re

urls = ('/(.*)', 'Formulario')
render = web.template.render('templates/')

app = web.application(urls, globals())

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

registerForm = form.Form( 
    form.Textbox("name", form.notnull, description = "Nombre"),
    form.Textbox("surname", form.notnull, description = "Apellidos"), 
    form.Textbox("dni", form.notnull, description = "D.N.I."),
    form.Textbox("email", form.Validator("Direccion de correo incorrecta", lambda i: confirmarEmail(i)), description = "E-mail"),
    form.Dropdown('day', dia(), description = "Dia de nacimiento"),
    form.Dropdown('month', mes(), description = "Mes de nacimiento"),
    form.Dropdown('year', anio(), description = "Anio de nacimiento"),
    form.Textarea("address", form.notnull, description = "Direccion"),
    form.Password("password", form.Validator("La contrasenia debe tener mas de 7 caracteres", lambda i: len(i)>7), description = "Contrasenia"),
    form.Password("passwordConfirm", form.Validator("Las constrasenias no coiniciden", lambda i: i.password == i), description = "Repite contrasenia"),
    form.Textbox("nTarjeta", form.Validator("Numero de tarjeta incorrecto", lambda i: confirmarTarjeta(i)), description = "Numero de tarjeta"),
    form.Checkbox("accept", form.Validator("Debes aceptar la clausula", lambda i:"accept" not in i)),
    form.Radio("payWay", ["Visa", "Paypal"], form.Validator("Debe elegir la forma de pago", lambda i: len(i) > 0), description = "Forma de pago"),
    validators = [form.Validator("Fecha de nacimiento incorrecta", lambda i: confirmarFecha(int(i.day), int(i.month), int(i.year)) == True)],
    )

class Formulario:
    def GET(self, name): 
        form = registerForm()
        return render.formtest(form)

    def POST(self, name): 
        form = registerForm()
        if not form.validates():
            return render.formtest(form)
        else:
            return '<p>Registro llevado a cabo correctamente</p>'
        
if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()