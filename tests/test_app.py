import unittest
from app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        
    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
    def test_generate_citation(self):
        response = self.client.post('/generer_citation', 
                                  data={'nom': 'Test', 'categorie': 'Succès'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('citation', response.json)