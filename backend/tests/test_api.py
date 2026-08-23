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

    def test_get_appointments_and_filtering(self):
        res = self.client.get("/api/appointments?limit=5")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(isinstance(res.json(), list))

        res_invalid = self.client.get("/api/appointments/NON_EXISTENT_APPOINTMENT_ID")
        self.assertEqual(res_invalid.status_code, 404)

    def test_get_residents(self):
        res = self.client.get("/api/residents?limit=5")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(isinstance(res.json(), list))

    def test_get_reminders(self):
        res = self.client.get("/api/reminders?limit=5")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(isinstance(res.json(), list))

    def test_get_metrics(self):
        res = self.client.get("/api/metrics")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("delivery_rate", data)

    def test_get_audit_logs(self):
        res = self.client.get("/api/audit-logs?limit=5")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(isinstance(res.json(), list))

    def test_policies_get_and_put(self):
        res = self.client.get("/api/policies")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["id"], 1)

        update_payload = {
            "quiet_hours_start": 21,
            "quiet_hours_end": 7,
            "max_attempts": 4,
            "channel_priority": "SMS,Voice,Email"
        }
        put_res = self.client.put("/api/policies", json=update_payload)
        self.assertEqual(put_res.status_code, 200)
        self.assertEqual(put_res.json()["quiet_hours_start"], 21)
        self.assertEqual(put_res.json()["max_attempts"], 4)

    def test_run_and_retry_reminders(self):
        res = self.client.post("/api/reminders/run")
        self.assertEqual(res.status_code, 200)
        self.assertIn("summary", res.json())

if __name__ == "__main__":
    unittest.main()
