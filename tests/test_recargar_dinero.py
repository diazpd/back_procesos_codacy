import json
from unittest import TestCase
from app import app
from faker import Faker

class TestRecargarDinero(TestCase):

    def setUp(self):
        self.data_factory = Faker()
        self.client = app.test_client()

        # crear un nuevo usuario
        nuevo_usuario = {
            "nombre": self.data_factory.name(),
            "correo": self.data_factory.email(),
            "numero_tarjeta": str(self.data_factory.random_number(digits=19, fix_len=False)),
            "usuario": self.data_factory.name(),
            "contrasena": self.data_factory.word()
        }

        # registrar el usuario y obtener el token
        solicitud_nuevo_usuario = self.client.post("/signin",
                                                   data=json.dumps(nuevo_usuario),
                                                   headers={'Content-Type': 'application/json'})
        respuesta_al_crear_usuario = json.loads(solicitud_nuevo_usuario.get_data())
        self.token = respuesta_al_crear_usuario["token"]
        self.usuario_code = respuesta_al_crear_usuario["id"]

    def test_recargar_dinero(self):
        # monto a recargar asumiendo que el saldo es cero
        monto = self.data_factory.random_int(min=1, max=1000000)
        nuevo_saldo = monto  

        # definir el endpoint y los headers de a solicitud
        endpoint_recargar_dinero = f'/usuarios/{self.usuario_code}/recargar_saldo'
        headers = {'Content-Type': 'application/json', "Authorization": f"Bearer {self.token}"}

        # enviar solicitud POST para recargar dinero
        response = self.client.post(endpoint_recargar_dinero, 
                                    data=json.dumps({'monto': monto}),
                                    headers=headers)

        # verificar la respuesta
        if response.status_code == 200:
            data = json.loads(response.get_data())

            # verificar el nuevo saldo en la respuesta
            self.assertEqual(data['nuevo_saldo'], nuevo_saldo)
        else:
            self.assertEqual(response.status_code, 400)  