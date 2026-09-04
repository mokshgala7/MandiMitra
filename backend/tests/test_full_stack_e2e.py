import unittest
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app

class TestMandiMitraFullStack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_mobile = "9876543210"
        cls.test_password = "FarmerPassword@2026"
        cls.auth_token = None

    def test_01_health_check(self):
        resp = self.client.get("/api/v1/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "healthy")

    def test_02_auth_signup_and_login(self):
        # Signup
        signup_payload = {
            "full_name": "Ramesh Patil",
            "email": "ramesh.patil.farmer@example.com",
            "mobile": self.test_mobile,
            "password": self.test_password,
            "state": "Maharashtra",
            "district": "Pune",
            "village": "Manjri",
            "primary_crop": "Wheat",
            "latitude": 18.5204,
            "longitude": 73.8567
        }
        # If user exists from previous test, login directly; else signup
        signup_resp = self.client.post("/api/v1/auth/signup", json=signup_payload)
        if signup_resp.status_code == 201:
            data = signup_resp.json()
            self.assertIn("access_token", data)
            self.assertEqual(data["user"]["full_name"], "Ramesh Patil")
            self.__class__.auth_token = data["access_token"]
        else:
            # Login
            login_resp = self.client.post("/api/v1/auth/login", json={
                "username": self.test_mobile,
                "password": self.test_password
            })
            if login_resp.status_code != 200:
                login_resp = self.client.post("/api/v1/auth/login", json={
                    "username": self.test_mobile,
                    "password": "password123"
                })
            self.assertEqual(login_resp.status_code, 200)
            data = login_resp.json()
            self.assertIn("access_token", data)
            self.__class__.auth_token = data["access_token"]

        # Test GET /api/v1/auth/me
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        me_resp = self.client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(me_resp.status_code, 200)
        me_data = me_resp.json()
        self.assertEqual(me_data["mobile"], self.test_mobile)

    def test_03_auth_invalid_password(self):
        resp = self.client.post("/api/v1/auth/login", json={
            "username": self.test_mobile,
            "password": "WrongPassword123"
        })
        self.assertEqual(resp.status_code, 401)

    def test_04_nearby_mandis_wheat(self):
        # Pune (18.5204, 73.8567)
        resp = self.client.get("/api/v1/mandis/nearby?crop=wheat&latitude=18.5204&longitude=73.8567&radius_km=500")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["crop"], "wheat")
        self.assertGreater(len(data["mandis"]), 0)
        
        # Verify distance sort
        distances = [m["distance_km"] for m in data["mandis"]]
        self.assertEqual(distances, sorted(distances))
        self.assertLessEqual(distances[-1], 500.0)

    def test_05_nearby_mandis_all_supported_crops(self):
        crops = ["rice", "tomato", "cotton"]
        for crop in crops:
            resp = self.client.get(f"/api/v1/mandis/nearby?crop={crop}&latitude=19.076&longitude=72.877&radius_km=500")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["crop"], crop)
            self.assertGreater(len(data["mandis"]), 0)

    def test_06_historical_prices_periods(self):
        periods = ["1D", "1W", "3W", "1M", "6M", "YTD"]
        for p in periods:
            resp = self.client.get(f"/api/v1/prices/history?crop=wheat&period={p}")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["period"], p)
            self.assertGreater(len(data["data_points"]), 0)

    def test_07_ml_prediction_wheat(self):
        # Find wheat mandi
        m_resp = self.client.get("/api/v1/mandis/nearby?crop=wheat&latitude=19.076&longitude=72.877&radius_km=500")
        mandi_id = m_resp.json()["mandis"][0]["mandi_id"]

        pred_resp = self.client.get(f"/api/v1/prediction?crop=wheat&mandi_id={mandi_id}")
        self.assertEqual(pred_resp.status_code, 200)
        data = pred_resp.json()
        self.assertEqual(data["crop"], "wheat")
        self.assertIn("forecast", data)
        self.assertIn("day_1", data["forecast"])
        self.assertIn("day_2", data["forecast"])
        self.assertIn("day_3", data["forecast"])
        self.assertIn(data["trend"], ["rising", "falling", "stable"])

    def test_08_ml_prediction_all_crops(self):
        crops = ["rice", "tomato", "cotton"]
        for crop in crops:
            m_resp = self.client.get(f"/api/v1/mandis/nearby?crop={crop}&latitude=19.076&longitude=72.877&radius_km=500")
            mandis = m_resp.json()["mandis"]
            tested = False
            for m in mandis:
                pred_resp = self.client.get(f"/api/v1/prediction?crop={crop}&mandi_id={m['mandi_id']}")
                if pred_resp.status_code == 200:
                    data = pred_resp.json()
                    self.assertEqual(data["crop"], crop)
                    self.assertGreater(data["current_price"], 0)
                    tested = True
                    break
            self.assertTrue(tested, f"Failed prediction for {crop}")

    def test_09_recommendation_engine(self):
        payload = {
            "crop": "wheat",
            "quantity_kg": 1000.0,  # 10 Quintals
            "latitude": 19.0760,
            "longitude": 72.8777,
            "has_middleman": True,
            "middleman_price": 2400.0,
            "middleman_commission": 200.0,
            "middleman_other": 100.0,
            "radius_km": 500.0
        }
        resp = self.client.post("/api/v1/recommendation", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(data["recommendation"], ["SELL TODAY", "HOLD FOR 2–3 DAYS"])
        self.assertEqual(data["quantity_quintals"], 10.0)
        self.assertIsNotNone(data["best_mandi"])
        self.assertIsNotNone(data["middleman"])
        self.assertGreater(data["current_net_value"], 0)
        self.assertIn("weather_advisory", data)

    def test_10_search_history_persistence(self):
        headers = {"Authorization": f"Bearer {self.__class__.auth_token}"}
        search_payload = {
            "crop": "wheat",
            "quantity_kg": 1000.0,
            "latitude": 18.5204,
            "longitude": 73.8567,
            "selected_mandi_id": "maharashtra-pune-apmc-pune",
            "has_middleman": False,
            "recommendation": "SELL TODAY"
        }
        # Post search
        create_resp = self.client.post("/api/v1/search-history", json=search_payload, headers=headers)
        self.assertEqual(create_resp.status_code, 201)

        # Get user search history
        get_resp = self.client.get("/api/v1/search-history", headers=headers)
        self.assertEqual(get_resp.status_code, 200)
        searches = get_resp.json()
        self.assertGreater(len(searches), 0)
        self.assertEqual(searches[0]["crop"], "wheat")

    def test_11_weather_endpoint(self):
        resp = self.client.get("/api/v1/weather?latitude=18.5204&longitude=73.8567&location_name=Pune")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["location"], "Pune")
        self.assertIn("temperature", data)
        self.assertIn("condition", data)
        self.assertIn("icon", data)

if __name__ == "__main__":
    unittest.main()
