from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api

from modelos import db
from vistas import VistaApuestas, VistaApuesta, VistaSignIn, VistaLogIn, VistaCarrerasUsuario, \
    VistaCarrera, VistaTerminacionCarrera, VistaReporte, VistaApuestasUsuario, \
    VistaUsuarios, VistaRecargarSaldo, VistaTransaccionesUsuario, VistaUsuario, VistaActualizarSaldo, \
    VistaCarreras

from flask_migrate import Migrate

app = Flask(__name__)
migrate = Migrate(app, db)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eporra.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'frase-secreta'
app.config['PROPAGATE_EXCEPTIONS'] = True

app_context = app.app_context()
app_context.push()

db.init_app(app)
db.create_all()

cors = CORS(app)

api = Api(app)
api.add_resource(VistaSignIn, '/signin')
api.add_resource(VistaLogIn, '/login')
# Microservicio para consultar las carreras disponibles apostador.
api.add_resource(VistaCarreras, '/carreras')
api.add_resource(VistaCarrerasUsuario, '/usuario/<int:id_usuario>/carreras')
api.add_resource(VistaCarrera, '/carrera/<int:id_carrera>')
api.add_resource(VistaApuestas, '/apuestas')
api.add_resource(VistaApuesta, '/apuesta/<int:id_apuesta>')
# Microservicio para consultar las aspuestas de un apostador.
api.add_resource(VistaApuestasUsuario, '/apuestas/<int:id_usuario>')
api.add_resource(VistaTerminacionCarrera, '/carrera/<int:id_competidor>/terminacion')
api.add_resource(VistaReporte, '/carrera/<int:id_carrera>/reporte')
api.add_resource(VistaUsuarios, '/usuarios') # API para consultar la lista de usuarios 
api.add_resource(VistaRecargarSaldo, '/usuarios/<int:id_usuario>/recargar_saldo') # API para recargar dinero
api.add_resource(VistaTransaccionesUsuario, '/usuario/<int:id_usuario>/transacciones')
api.add_resource(VistaUsuario,'/usuario/<int:id_usuario>')
api.add_resource(VistaActualizarSaldo,'/actualizarSaldo/<int:id_usuario>/<int:nuevo_saldo>')

jwt = JWTManager(app)
