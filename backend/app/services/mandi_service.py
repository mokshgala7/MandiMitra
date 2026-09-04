import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

if (BASE_DIR / "frontend" / "public" / "data").exists():
    DATA_DIR = BASE_DIR / "frontend" / "public" / "data"
elif (BASE_DIR / "public" / "data").exists():
    DATA_DIR = BASE_DIR / "public" / "data"
else:
    DATA_DIR = BASE_DIR / "public" / "data"

MANDI_MASTER_FILE = DATA_DIR / "mandi_master.json"

def calculate_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0 # Earth radius in kilometers

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

def create_mandi_id(state: str, district: str, market: str) -> str:
    import re
    s = f"{state}-{district}-{market}".lower()
    return re.sub(r'[^a-z0-9]+', '-', s)

class MandiService:
    def __init__(self):
        self.master_data = []
        self.master_map = {}
        self.load_master_data()

    def load_master_data(self):
        if MANDI_MASTER_FILE.exists():
            with open(MANDI_MASTER_FILE, "r") as f:
                self.master_data = json.load(f)
            self.master_map = {m["mandi_id"]: m for m in self.master_data}

    def get_nearby_mandis(self, crop: str, latitude: float, longitude: float, radius_km: float = 500) -> Dict[str, Any]:
        self.load_master_data() # Reload dynamically since geocoding is happening in background
        csv_path = DATA_DIR / f"{crop}.csv"
        if not csv_path.exists():
            raise ValueError(f"Data for crop '{crop}' not found.")

        # CSV has Agmarknet title row - always skip first row
        df = pd.read_csv(csv_path, skiprows=1, encoding="utf-8")
        
        # Clean columns
        df.columns = [c.strip() for c in df.columns]
        
        # Fast date sorting: convert DD-MM-YYYY to YYYYMMDD integer (avoids pd.to_datetime hang on Py3.14)
        def _date_sortable(d):
            try:
                parts = str(d).split("-")
                return int(parts[2]) * 10000 + int(parts[1]) * 100 + int(parts[0])
            except Exception:
                return 0

        df = df.copy()
        df["date_sortable"] = df["Price Date"].apply(_date_sortable)
        df["Modal Price_num"] = pd.to_numeric(
            df["Modal Price"].astype(str).str.replace(",", ""), errors="coerce"
        )
        
        # Drop rows with invalid dates or prices
        df = df[(df["date_sortable"] > 0) & df["Modal Price_num"].notna()]
        
        # Take latest price record per market (fast idxmax on integer key)
        idx = df.groupby(["State/UT", "District", "Market"])["date_sortable"].idxmax()
        latest_prices = df.loc[idx].reset_index(drop=True)
        
        results = []
        missing_coords_count = 0
        
        for _, row in latest_prices.iterrows():
            state = str(row["State/UT"]).strip()
            district = str(row["District"]).strip()
            market = str(row["Market"]).strip()
            
            stable_id = create_mandi_id(state, district, market)
            
            master_info = self.master_map.get(stable_id)
            if not master_info or master_info.get("latitude") is None:
                missing_coords_count += 1
                continue
                
            m_lat = float(master_info["latitude"])
            m_lng = float(master_info["longitude"])
            
            dist = calculate_haversine(latitude, longitude, m_lat, m_lng)
            
            if dist <= radius_km:
                results.append({
                    "mandi_id": stable_id,
                    "mandi_name": market,
                    "district": district,
                    "state": state,
                    "latitude": m_lat,
                    "longitude": m_lng,
                    "distance_km": round(dist, 2),
                    "latest_price": row["Modal Price_num"],
                    "price_unit": row.get("Price Unit", "Rs./Quintal"),
                    "price_date": str(row["Price Date"]).strip()
                })
                
        results.sort(key=lambda x: x["distance_km"])
        
        return {
            "crop": crop,
            "radius_km": radius_km,
            "farmer_location": {"latitude": latitude, "longitude": longitude},
            "meta": {
                "total_price_records_checked": len(latest_prices),
                "total_master_records": len(self.master_data),
                "records_missing_coordinates": missing_coords_count
            },
            "mandis": results
        }
