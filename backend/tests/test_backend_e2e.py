import unittest
import json
import sys
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.services.mandi_service import calculate_haversine

class TestMandiMitraBackend(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_01_health_check(self):
        response = self.app.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data.get("status"), "healthy")

    def test_02_haversine_distance(self):
        # Mumbai (19.0760, 72.8777) to Pune (18.5204, 73.8567) is ~120 km
        dist = calculate_haversine(19.0760, 72.8777, 18.5204, 73.8567)
        self.assertAlmostEqual(dist, 120.0, delta=15.0)

    def test_03_nearby_mandis_wheat_mumbai(self):
        # Mumbai coordinates: lat=19.076, lon=72.877
        response = self.app.get("/api/v1/mandis/nearby?crop=wheat&latitude=19.076&longitude=72.877&radius_km=500")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(data["crop"], "wheat")
        self.assertEqual(data["radius_km"], 500)
        self.assertIn("mandis", data)
        self.assertGreater(len(data["mandis"]), 0)
        
        # Verify mandis are sorted ascending by distance
        distances = [m["distance_km"] for m in data["mandis"]]
        self.assertEqual(distances, sorted(distances))
        
        # Check structure of each mandi item
        first_mandi = data["mandis"][0]
        self.assertIn("mandi_id", first_mandi)
        self.assertIn("mandi_name", first_mandi)
        self.assertIn("district", first_mandi)
        self.assertIn("latitude", first_mandi)
        self.assertIn("longitude", first_mandi)
        self.assertIn("distance_km", first_mandi)
        self.assertIn("latest_price", first_mandi)
        self.assertIn("price_date", first_mandi)
        self.assertLessEqual(first_mandi["distance_km"], 500)

    def test_04_nearby_mandis_rice_pune(self):
        # Pune coordinates: lat=18.5204, lon=73.8567
        response = self.app.get("/api/v1/mandis/nearby?crop=rice&latitude=18.5204&longitude=73.8567&radius_km=500")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["crop"], "rice")
        self.assertGreater(len(data["mandis"]), 0)

    def test_05_nearby_mandis_tomato_nagpur(self):
        # Nagpur coordinates: lat=21.1458, lon=79.0882
        response = self.app.get("/api/v1/mandis/nearby?crop=tomato&latitude=21.1458&longitude=79.0882&radius_km=500")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["crop"], "tomato")
        self.assertGreater(len(data["mandis"]), 0)

    def test_06_nearby_mandis_cotton(self):
        # Hinganghat coordinates: lat=20.5500, lon=78.8333
        response = self.app.get("/api/v1/mandis/nearby?crop=cotton&latitude=20.5500&longitude=78.8333&radius_km=500")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["crop"], "cotton")
        self.assertGreater(len(data["mandis"]), 0)

    def test_07_prediction_wheat(self):
        # First find a wheat mandi from nearby mandis
        res = self.app.get("/api/v1/mandis/nearby?crop=wheat&latitude=19.076&longitude=72.877&radius_km=500")
        mandi = json.loads(res.data)["mandis"][0]
        mandi_id = mandi["mandi_id"]

        pred_res = self.app.get(f"/api/v1/prediction?crop=wheat&mandi_id={mandi_id}")
        self.assertEqual(pred_res.status_code, 200)
        pred_data = json.loads(pred_res.data)

        self.assertEqual(pred_data["crop"], "wheat")
        self.assertEqual(pred_data["mandi_id"], mandi_id)
        self.assertIn("current_price", pred_data)
        self.assertGreater(pred_data["current_price"], 0)
        
        # Verify forecast & predictions keys
        for key in ["forecast", "predictions"]:
            self.assertIn(key, pred_data)
            self.assertIn("day_1", pred_data[key])
            self.assertIn("day_2", pred_data[key])
            self.assertIn("day_3", pred_data[key])
            self.assertGreater(pred_data[key]["day_1"], 0)
            self.assertGreater(pred_data[key]["day_2"], 0)
            self.assertGreater(pred_data[key]["day_3"], 0)
            
        self.assertIn(pred_data["trend"], ["rising", "falling", "stable"])
        self.assertIn("prediction_date", pred_data)

    def test_08_prediction_rice(self):
        res = self.app.get("/api/v1/mandis/nearby?crop=rice&latitude=18.5204&longitude=73.8567&radius_km=500")
        mandis = json.loads(res.data)["mandis"]
        
        # Test a mandi with sufficient history
        tested = False
        for mandi in mandis:
            pred_res = self.app.get(f"/api/v1/prediction?crop=rice&mandi_id={mandi['mandi_id']}")
            if pred_res.status_code == 200:
                pred_data = json.loads(pred_res.data)
                self.assertEqual(pred_data["crop"], "rice")
                self.assertIn("forecast", pred_data)
                self.assertIn("predictions", pred_data)
                self.assertGreater(pred_data["current_price"], 0)
                tested = True
                break
        self.assertTrue(tested, "At least one nearby rice mandi must produce valid predictions")

    def test_09_prediction_tomato(self):
        res = self.app.get("/api/v1/mandis/nearby?crop=tomato&latitude=19.076&longitude=72.877&radius_km=500")
        mandis = json.loads(res.data)["mandis"]
        
        tested = False
        for mandi in mandis:
            pred_res = self.app.get(f"/api/v1/prediction?crop=tomato&mandi_id={mandi['mandi_id']}")
            if pred_res.status_code == 200:
                pred_data = json.loads(pred_res.data)
                self.assertEqual(pred_data["crop"], "tomato")
                self.assertIn("forecast", pred_data)
                self.assertIn("predictions", pred_data)
                tested = True
                break
        self.assertTrue(tested, "At least one nearby tomato mandi must produce valid predictions")

    def test_10_prediction_cotton(self):
        res = self.app.get("/api/v1/mandis/nearby?crop=cotton&latitude=20.5500&longitude=78.8333&radius_km=500")
        mandis = json.loads(res.data)["mandis"]
        
        tested = False
        for mandi in mandis:
            pred_res = self.app.get(f"/api/v1/prediction?crop=cotton&mandi_id={mandi['mandi_id']}")
            if pred_res.status_code == 200:
                pred_data = json.loads(pred_res.data)
                self.assertEqual(pred_data["crop"], "cotton")
                self.assertIn("forecast", pred_data)
                self.assertIn("predictions", pred_data)
                tested = True
                break
        self.assertTrue(tested, "At least one nearby cotton mandi must produce valid predictions")

    def test_11_insufficient_historical_data_error(self):
        # Test a minor mandi that has fewer than 31 rows in Rice (e.g. Nira(Saswad))
        res = self.app.get("/api/v1/prediction?crop=rice&mandi_id=maharashtra-pune-nira-saswad-")
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertIn("Insufficient historical data", data.get("detail", ""))

    def test_12_error_handling_invalid_crop(self):
        res = self.app.get("/api/v1/mandis/nearby?crop=unsupported_crop&latitude=19.076&longitude=72.877")
        self.assertEqual(res.status_code, 404)

    def test_13_error_handling_missing_params(self):
        res = self.app.get("/api/v1/mandis/nearby?crop=wheat")
        self.assertEqual(res.status_code, 400)

    def test_14_error_handling_unknown_mandi(self):
        res = self.app.get("/api/v1/prediction?crop=wheat&mandi_id=fake-non-existent-mandi")
        self.assertEqual(res.status_code, 400)

if __name__ == "__main__":
    unittest.main()
