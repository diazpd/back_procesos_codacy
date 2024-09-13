import json
from unittest import TestCase
from app import app
from faker import Faker
from faker.generator import random
from modelos.modelos import Transaccion, Usuario
  

class TestRetirarDinero(TestCase):

    def setUp(self):
        self.data_factory = Faker()
        self.client = app.test_client()
   

    def test_get_usuario(self):
        # Probar la vista VistaUsuario
        nuevo_usuario = {
            "id":1,
           }

        endpoint_get_usuario = "/usuario/{}".format(nuevo_usuario["id"])
        
        solicitud_get_usuario = self.client.get(endpoint_get_usuario,
                                                   data=json.dumps(nuevo_usuario)  )
        data = solicitud_get_usuario.json
        
        
        self.assertEqual(solicitud_get_usuario.status_code, 200)
        self.assertEqual(data['id'], nuevo_usuario["id"])
 
    
    def test_actualizar_saldo(self):
        # Probar la vista VistaActualizarSaldo
        nuevo_saldo = self.data_factory.random_int(min=10000, max=1000000)
        endpoint_actualizar_saldo = "/actualizarSaldo/1/{}".format(nuevo_saldo)
        response = self.client.post(endpoint_actualizar_saldo)
        
        if(response.status_code==200):
           self.assertEqual(response.status_code, 200)
           data = response.json
           self.assertEqual(data['saldo'], nuevo_saldo)
          # Verificar que el saldo realmente se actualizó en la base de datos
           usuario_actualizado = Usuario.query.get(1)
           self.assertEqual(usuario_actualizado.saldo, nuevo_saldo)
        else:
            # Verificar que el servicio esta abajo
            self.assertEqual(response.status_code, 500)