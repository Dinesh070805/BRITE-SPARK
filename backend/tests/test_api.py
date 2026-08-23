import unittest
from fastapi.testclient import TestClient
from backend.app.main import app

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

    def test_get_dashboard(self):
        res = self.client.get("/api/dashboard")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("appointments", data)
        self.assertIn("reach_rate", data)

    def test_get_appointments(self):
        res = self.client.get("/api/appointments?limit=5")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(isinstance(res.json(), list))

    def test_get_policies(self):
        res = self.client.get("/api/policies")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["id"], 1)

if __name__ == "__main__":
    unittest.main()
