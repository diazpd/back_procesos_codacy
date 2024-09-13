import json
from unittest import TestCase

from faker import Faker
from faker.generator import random

from app import app

# Pruebas usuario
class TestUsuario(TestCase):

    def setUp(self):
        self.data_factory = Faker()
        self.client = app.test_client()

        nuevo_usuario = {
            "nombre": self.data_factory.name(),
            "correo": self.data_factory.email(),
            "numero_tarjeta": str(self.data_factory.random_number(digits=19, fix_len=False)),
            "usuario": self.data_factory.name(),
            "contrasena": self.data_factory.word()
        }

        solicitud_nuevo_usuario = self.client.post("/signin",
                                                   data=json.dumps(nuevo_usuario),
                                                   headers={'Content-Type': 'application/json'})

        respuesta_al_crear_usuario = json.loads(solicitud_nuevo_usuario.get_data())

        self.token = respuesta_al_crear_usuario["token"]
        self.usuario_code = respuesta_al_crear_usuario["id"]

    def test_obtener_transacciones(self):
        endpoint_transacciones = "/usuario/{}/carreras".format(str(self.usuario_code))
        headers = {'Content-Type': 'application/json', "Authorization": "Bearer {}".format(self.token)}

        solicitud_transacciones = self.client.get(endpoint_transacciones,headers=headers)
        transacciones_obtenidas = json.loads(solicitud_transacciones.get_data())

        self.assertEqual(solicitud_transacciones.status_code, 200)
        self.assertEqual(transacciones_obtenidas, [])
