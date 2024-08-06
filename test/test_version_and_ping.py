import unittest
from flask import Flask
from app.routes.main import main_bp

class MainRoutesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.app = Flask(__name__)
        self.app.register_blueprint(main_bp, url_prefix='/api')
        self.client = self.app.test_client()

    def test_get_version(self) -> None:
        response = self.client.get('/api/version')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"version": "v1.0.0"})

    def test_ping(self) -> None:
        response = self.client.get('/api/ping')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": 200, "message": "pong!"})

if __name__ == '__main__':
    unittest.main()