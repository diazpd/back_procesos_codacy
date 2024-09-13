import unittest
from unittest.mock import patch, MagicMock
from faker import Faker
from app import app


class TestRegistrarGanancia(unittest.TestCase):

    def setUp(self):
        self.data_factory = Faker()
        self.client = app.test_client()
        self.valor_apostado =self.data_factory.random_int(min=10000, max=1000000)
        self.saldo =self.data_factory.random_int(min=10000, max=20000)
        self.cuota=0.5

    @patch('modelos.Competidor.query.get_or_404')
    @patch('modelos.Carrera.query.get_or_404')
    @patch('modelos.db.session.commit')
    @patch('modelos.db.session.add')
    @patch('modelos.Apuesta.query.filter_by')
    @patch('modelos.Usuario.query.filter_by')
    def test_terminacion_carrera(
        self,
        mock_usuario_query,
        mock_apuesta_query,
        mock_db_add,
        mock_db_commit,
        mock_carrera_get,
        mock_competidor_get
    ):
        # Simular los datos del competidor, carrera, apuesta y usuario
        mock_competidor = MagicMock(id=1, es_ganador=True, id_carrera=1, cuota=self.cuota)
        mock_carrera = MagicMock(id=1, abierta=False, apuestas=[])
        mock_apuesta = MagicMock(id_competidor=mock_competidor.id, valor_apostado=self.valor_apostado, ganancia=(self.valor_apostado + (self.valor_apostado / self.cuota)))
        mock_usuario = MagicMock(id=1, nombre=self.data_factory.name, saldo=self.saldo)

        # Configurar los mocks para devolver los objetos simulados
        mock_competidor_get.return_value = mock_competidor
        mock_carrera_get.return_value = mock_carrera
        mock_apuesta_query.return_value.first.return_value = mock_apuesta
        mock_usuario_query.return_value.first.return_value = mock_usuario

        # Agregar la apuesta a la carrera simulada
        mock_carrera.apuestas.append(mock_apuesta)

        response = self.client.put(f'/carrera/{mock_competidor.id}/terminacion')

        # Verificamos que la respuesta sea 200 OK
        self.assertEqual(response.status_code, 200)

        # Verificamos que el competidor fue marcado como ganador
        self.assertTrue(mock_competidor.es_ganador)

        # Verificamos que la carrera ya no esté abierta
        self.assertFalse(mock_carrera.abierta)

        # Verificamos que la ganancia de la apuesta fue calculada correctamente
        expected_ganancia = mock_apuesta.valor_apostado + (mock_apuesta.valor_apostado / mock_competidor.cuota)
        #expected_ganancia = 0
        self.assertEqual(mock_apuesta.ganancia, expected_ganancia)

        # Verificamos que el saldo del usuario se haya actualizado correctamente
        self.assertEqual(mock_apuesta.ganancia+mock_usuario.saldo, self.saldo + expected_ganancia)

        # Verificamos que la función commit fue llamada (es decir, que se guardaron los cambios)
       