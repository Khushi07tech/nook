import unittest
from app import app, get_db

class NookTestCase(unittest.TestCase):
    def setUp(self):
        """Runs before every test: configure test mode."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_homepage_loads(self):
        """Test that index loads successfully."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_invalid_route_404(self):
        """Test custom 404 handler for nonexistent routes."""
        response = self.client.get('/this-route-does-not-exist')
        self.assertEqual(response.status_code, 404)

    def test_create_idea(self):
        """Test idea creation flow."""
        response = self.client.post('/ideas', data={
            'raw_content': 'Test automated idea entry'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test automated idea entry", response.data)

if __name__ == '__main__':
    unittest.main()