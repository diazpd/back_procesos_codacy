import datetime
from zoneinfo import ZoneInfo
from flask import request
from flask_jwt_extended import jwt_required, create_access_token
from flask_restful import Resource
from modelos.modelos import Transaccion
from sqlalchemy.exc import IntegrityError

from modelos import db, Apuesta, ApuestaSchema, Usuario, UsuarioSchema, Carrera, CarreraSchema, CompetidorSchema, \
    Competidor, ReporteSchema, Transaccion, TransaccionSchema

apuesta_schema = ApuestaSchema()
carrera_schema = CarreraSchema()
competidor_schema = CompetidorSchema()
usuario_schema = UsuarioSchema()
reporte_schema = ReporteSchema()
transaccion_schema = TransaccionSchema()

class VistaSignIn(Resource):

    def post(self):

        # Verificar si el usuario ya existe
        usuario_existente = Usuario.query.filter_by(usuario=request.json.get("usuario")).first()
        
        if usuario_existente:
            return "El nombre de usuario ya existe", 400
        
        # Verificar si el correo ya existe
        correo_existente = Usuario.query.filter_by(correo=request.json.get("correo")).first()
        
        if correo_existente:
            return "El correo ingresado ya existe", 400

        nuevo_usuario = Usuario(nombre=request.json["nombre"], correo=request.json["correo"], numero_tarjeta=request.json["numero_tarjeta"], usuario=request.json["usuario"], contrasena=request.json["contrasena"])
        db.session.add(nuevo_usuario)
        db.session.commit()
        token_de_acceso = create_access_token(identity=nuevo_usuario.id)
        return {"mensaje": "usuario creado exitosamente", "token": token_de_acceso, "id": nuevo_usuario.id}

    def put(self, id_usuario):
        usuario = db.get_or_404(Usuario, id_usuario)
        usuario.contrasena = request.json.get("contrasena", usuario.contrasena)
        db.session.commit()
        return usuario_schema.dump(usuario)

    def delete(self, id_usuario):
        usuario = db.get_or_404(Usuario, id_usuario)
        db.session.delete(usuario)
        db.session.commit()
        return '', 204

class VistaUsuario(Resource):

    def get(self, id_usuario):
        return usuario_schema.dump(Usuario.query.get_or_404(id_usuario))
    
class VistaActualizarSaldo(Resource):
    def post(self, id_usuario, nuevo_saldo):
        try:
            # Buscar el usuario o lanzar error 404
            usuario = db.get_or_404(Usuario, id_usuario)

            # Calcular el valor del cambio de saldo (retiro o aumento)
            valor =  usuario.saldo - nuevo_saldo

            # Actualizar el saldo del usuario
            usuario.saldo = nuevo_saldo

            # hora Colombia
            colombia_timezone = datetime.timezone(datetime.timedelta(hours=-5))
            fecha_utc = datetime.datetime.now(datetime.timezone.utc)
            fecha_actual_colombia = fecha_utc.astimezone(colombia_timezone)

            # Crear un objeto Transaccion para registrar el cambio de saldo
            nueva_transaccion = Transaccion(
                tipo="Retiro",  # Tipo depende si es retiro o depósito
                monto=abs(valor),  # Guardar el valor absoluto del cambio de saldo
                fecha=fecha_actual_colombia,  # Asigna la fecha actual
                usuario=id_usuario
            )

            # Agregar tanto la actualización de usuario como la transacción dentro de la sesión
            db.session.add(nueva_transaccion)

            # Confirmar todos los cambios en la base de datos
            db.session.commit()

            # Agregar la actualizacion del saldo del usuario
            db.session.add(usuario)

            # Confirmar todos los cambios en la base de datos
            db.session.commit()

            # Devolver el usuario con el saldo actualizado
            return usuario_schema.dump(usuario), 200

        except Exception as e:
            # Hacer rollback en caso de error
            db.session.rollback()
            return {'error': str(e)}, 500


class VistaLogIn(Resource):

    def post(self):
        print(db.first_or_404(db.select(Usuario).filter_by(usuario = request.json["usuario"], contrasena = request.json["contrasena"])))
        usuario = db.first_or_404(
            db.select(Usuario).filter_by(
                usuario = request.json["usuario"], 
                contrasena = request.json["contrasena"]
            )
        )
        
        db.session.commit()
        if usuario is None:
            return "El usuario no existe", 404
        else:
            token_de_acceso = create_access_token(identity=usuario.id)
            return {"mensaje": "Inicio de sesión exitoso", "token": token_de_acceso}


class VistaCarrerasUsuario(Resource):

    @jwt_required()
    def post(self, id_usuario):
        nueva_carrera = Carrera(nombre_carrera=request.json["nombre"])
        for item in request.json["competidores"]:
            cuota = round((item["probabilidad"] / (1 - item["probabilidad"])), 2)
            competidor = Competidor(nombre_competidor=item["competidor"],
                                    probabilidad=item["probabilidad"],
                                    cuota=cuota,
                                    id_carrera=nueva_carrera.id)
            nueva_carrera.competidores.append(competidor)
        usuario = db.get_or_404(Usuario, id_usuario)
        usuario.carreras.append(nueva_carrera)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return 'El usuario ya tiene un carrera con dicho nombre', 409

        return carrera_schema.dump(nueva_carrera)

    @jwt_required()
    def get(self, id_usuario):
        usuario = db.get_or_404(Usuario, id_usuario)
        return [carrera_schema.dump(carrera) for carrera in usuario.carreras]

class VistaCarreras(Resource):
    @jwt_required()
    def get(self):
        carreras = db.session.execute(db.select(Carrera))
        return [carrera_schema.dump(ca) for ca in carreras.scalars().all()]

class VistaCarrera(Resource):

    @jwt_required()
    def get(self, id_carrera):
        # Retorna la lista de todas las carreras
        return carrera_schema.dump(db.get_or_404(Carrera, id_carrera))

    @jwt_required()
    def put(self, id_carrera):
        carrera = db.get_or_404(Carrera, id_carrera)
        carrera.nombre_carrera = request.json.get("nombre", carrera.nombre_carrera)
        carrera.competidores = []

        for item in request.json["competidores"]:
            probabilidad = float(item["probabilidad"])
            cuota = round((probabilidad / (1 - probabilidad)), 2)
            competidor = Competidor(nombre_competidor=item["competidor"],
                                    probabilidad=probabilidad,
                                    cuota=cuota,
                                    id_carrera=carrera.id)
            carrera.competidores.append(competidor)

        db.session.commit()
        return carrera_schema.dump(carrera)

    @jwt_required()
    def delete(self, id_carrera):
        carrera = db.get_or_404(Carrera, id_carrera)
        db.session.delete(carrera)
        db.session.commit()
        return '', 204


class VistaApuestas(Resource):

    @jwt_required()
    def post(self):
        nueva_apuesta = Apuesta(valor_apostado=request.json["valor_apostado"],
                                nombre_apostador=request.json["nombre_apostador"],
                                id_competidor=request.json["id_competidor"], id_carrera=request.json["id_carrera"])
        db.session.add(nueva_apuesta)
        db.session.commit()
        return apuesta_schema.dump(nueva_apuesta)

    @jwt_required()
    def get(self):
        apuestas = db.session.execute(db.select(Apuesta))
        return [apuesta_schema.dump(ca) for ca in apuestas.scalars().all()]


class VistaApuesta(Resource):

    @jwt_required()
    def get(self, id_apuesta):
        return apuesta_schema.dump(db.get_or_404(Apuesta, id_apuesta))

    @jwt_required()
    def put(self, id_apuesta):
        apuesta = db.get_or_404(Apuesta, id_apuesta)
        apuesta.valor_apostado = request.json.get("valor_apostado", apuesta.valor_apostado)
        apuesta.nombre_apostador = request.json.get("nombre_apostador", apuesta.nombre_apostador)
        apuesta.id_competidor = request.json.get("id_competidor", apuesta.id_competidor)
        apuesta.id_carrera = request.json.get("id_carrera", apuesta.id_carrera)
        db.session.commit()
        return apuesta_schema.dump(apuesta)

    @jwt_required()
    def delete(self, id_apuesta):
        apuesta = db.get_or_404(Apuesta, id_apuesta)
        db.session.delete(apuesta)
        db.session.commit()
        return '', 204

class VistaApuestasUsuario(Resource):
    # Validacion de autenticacion
    @jwt_required()

    def get(self, id_usuario):
        # Obtener los datos del usuario, si el usuario no existe retornara un error 404.
        usuario = db.get_or_404(Usuario, id_usuario)
        # Obtener la lista de apuestas filtradas por el nombre del usuario actual.
        apuestas = db.session.execute(db.select(Apuesta).filter(Apuesta.nombre_apostador == usuario.nombre))
        # Retornar la lista de apuestas filtradas, si no se encuenrtran listas con el nombre
        # del apostador retornala una lista vacia.
        return [apuesta_schema.dump(ca) for ca in apuestas.scalars().all()]

class VistaTerminacionCarrera(Resource):

    def put(self, id_competidor):
        competidor = db.get_or_404(Competidor, id_competidor)
        competidor.es_ganador = True
        carrera = db.get_or_404(Carrera, competidor.id_carrera)
        carrera.abierta = False

        for apuesta in carrera.apuestas:
            if apuesta.id_competidor == competidor.id:
                apuesta.ganancia = apuesta.valor_apostado + (apuesta.valor_apostado/competidor.cuota)
                usuario=  db.session.execute(db.select(Usuario).filter(Apuesta.nombre_apostador == Usuario.nombre and Apuesta.id_competidor==competidor.id and Apuesta.id_carrera==carrera.id)).scalars().first()
                
                #print("******************")
                # hora Colombia
                colombia_timezone = datetime.timezone(datetime.timedelta(hours=-5))
                fecha_utc = datetime.datetime.now(datetime.timezone.utc)
                fecha_actual_colombia = fecha_utc.astimezone(colombia_timezone)
                
                # Crear un objeto Transaccion para registrar la ganancia
                nueva_transaccion = Transaccion(
                    tipo="Ganancia",  # Tipo depende si es retiro,depósito o ganacia
                    monto=abs(int(apuesta.ganancia)),  # Guardar el valor de ganancia 
                    fecha=fecha_actual_colombia,  # Asigna la fecha actual
                    usuario=usuario.id # Asinga id de usuario
                )

                # Agregar la actualización de la transacción dentro de la sesión
                db.session.add(nueva_transaccion)

                # Confirmar todos los cambios en la base de datos
                db.session.commit()

                #usuario_json = usuario_schema.dump(usuario)
                
                
                if(usuario.saldo!=None):
                   
                   usuario.saldo=int(usuario.saldo)+int(apuesta.ganancia)
                else:
                    
                    usuario.saldo=int(apuesta.ganancia)

                #print("***************saldo***************")
                #print(usuario.saldo)
                
                # Agregar la actualización del saldo del  usuario
                db.session.add(usuario)
                #usuario_schema.dump(usuario_json)
                # Confirmar todos los cambios en la base de datos
                db.session.commit()


            else:
                apuesta.ganancia = 0

        db.session.commit()
        return competidor_schema.dump(competidor)


class VistaReporte(Resource):

    @jwt_required()
    def get(self, id_carrera):
        carreraReporte = db.get_or_404(Carrera, id_carrera)
        ganancia_casa_final = 0

        for apuesta in carreraReporte.apuestas:
            ganancia_casa_final = ganancia_casa_final + apuesta.valor_apostado - apuesta.ganancia

        reporte = dict(carrera=carreraReporte, ganancia_casa=ganancia_casa_final)
        schema = ReporteSchema()
        return schema.dump(reporte)

# Vista para obtener el listado de apostadores
class VistaUsuarios(Resource):
    # Requiere autenticación
    @jwt_required() 
    # get
    def get(self):
        # consulta la tabla Usuario en la base de datos
        usuarios = db.session.execute(db.select(Usuario))
        # retorna un json con los usuarios 
        return [usuario_schema.dump(usuario) for usuario in usuarios.scalars().all()]

# Vista para recargar saldo apostador y registrar la transacción
class VistaRecargarSaldo(Resource):

    # Requiere autenticación
    @jwt_required()
    def post(self, id_usuario):
        # obtener el usuario o devolver 404 si no existe
        usuario = db.get_or_404(Usuario, id_usuario)
        
        # obtener el monto a recargar enviado desde el frontend
        monto = request.json.get('monto', 0)

        # validación del monto: número positivo
        if monto <= 0:
            return {'error': 'Monto inválido. Debe recargar más de cero.'}, 400

        # actualización del saldo del usuario
        if usuario.saldo is None:
            usuario.saldo = 0.0  # O cualquier valor predeterminado
        usuario.saldo += monto

        # hora Colombia
        colombia_timezone = datetime.timezone(datetime.timedelta(hours=-5))
        fecha_utc = datetime.datetime.now(datetime.timezone.utc)
        fecha_actual_colombia = fecha_utc.astimezone(colombia_timezone)

        # registro de la transacción
        nueva_transaccion = Transaccion(
            tipo='Recarga',
            monto=monto,
            # usa datetime.datetime.now() para no generar un error al importar el módulo
            fecha=fecha_actual_colombia, 
            usuario=usuario.id
        )

       # guardar los cambios en la base de datos
        try:
            db.session.add(nueva_transaccion)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'error': 'Error al guardar la transacción: ' + str(e)}, 500

        # retornar confirmación con el nuevo saldo
        return {
            'message': 'Saldo recargado exitosamente',
            'nuevo_saldo': float(usuario.saldo),
        }, 200
class VistaTransaccionesUsuario(Resource):

    @jwt_required()
    def get(self, id_usuario):
        usuario = db.get_or_404(Usuario, id_usuario)
        return [transaccion_schema.dump(transaccion) for transaccion in usuario.transacciones]
