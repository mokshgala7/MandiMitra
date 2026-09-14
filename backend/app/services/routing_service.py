import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CACHE_FILE = BASE_DIR / "data" / "osrm_cache.json"

ROAD_DETOUR_FACTOR = 1.22  # Typical Indian road winding / detour index vs straight-line


class RoutingService:
    def __init__(self):
        self.cache: Dict[str, float] = {}
        self._load_cache()

    def _load_cache(self):
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
            except Exception:
                self.cache = {}

    def _save_cache(self):
        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cache, f)
        except Exception:
            pass

    def _cache_key(self, origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> str:
        # Precision to ~110m (3 decimals) is optimal for road cache hits
        return f"{round(origin_lat, 3)},{round(origin_lng, 3)}->{round(dest_lat, 3)},{round(dest_lng, 3)}"

    def calculate_road_distances(
        self,
        origin_lat: float,
        origin_lng: float,
        destinations: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculates road network distances using OpenStreetMap OSRM Table API in batches.
        Falls back smoothly to Haversine * 1.22 detour factor if OSRM is unavailable.

        Each destination dict must have 'mandi_id', 'latitude', 'longitude', and 'aerial_distance_km'.
        Returns dict mapping mandi_id -> road_distance_km.
        """
        results: Dict[str, float] = {}
        pending_destinations: List[Tuple[int, Dict[str, Any]]] = []

        # 1. Check cache first
        for idx, dest in enumerate(destinations):
            m_id = dest["mandi_id"]
            d_lat = float(dest["latitude"])
            d_lng = float(dest["longitude"])
            aerial = float(dest.get("aerial_distance_km", 0.0))

            ckey = self._cache_key(origin_lat, origin_lng, d_lat, d_lng)
            if ckey in self.cache:
                results[m_id] = self.cache[ckey]
            else:
                pending_destinations.append((idx, dest))

        if not pending_destinations:
            return results

        # 2. Batch pending destinations (up to 40 per OSRM Table request for URL safety)
        batch_size = 40
        cache_updated = False

        for i in range(0, len(pending_destinations), batch_size):
            batch = pending_destinations[i : i + batch_size]
            coords_list = [f"{round(origin_lng, 5)},{round(origin_lat, 5)}"]
            for _, d in batch:
                coords_list.append(f"{round(float(d['longitude']), 5)},{round(float(d['latitude']), 5)}")

            coords_str = ";".join(coords_list)
            url = f"http://router.project-osrm.org/table/v1/driving/{coords_str}?sources=0&annotations=distance"

            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "MandiMitra-FarmerPlatform/1.0"}
                )
                with urllib.request.urlopen(req, timeout=4) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    if data.get("code") == "Ok" and "distances" in data:
                        matrix = data["distances"][0]  # First row is origin to all destinations
                        for b_idx, (_, d) in enumerate(batch):
                            m_id = d["mandi_id"]
                            d_lat = float(d["latitude"])
                            d_lng = float(d["longitude"])
                            # matrix[0] is origin->origin, matrix[b_idx + 1] is origin->dest
                            dist_meters = matrix[b_idx + 1] if len(matrix) > b_idx + 1 else None
                            if dist_meters is not None and dist_meters > 0:
                                road_km = round(float(dist_meters) / 1000.0, 1)
                            else:
                                # Fallback if OSRM returned null for specific point
                                road_km = round(float(d.get("aerial_distance_km", 0.0)) * ROAD_DETOUR_FACTOR, 1)

                            results[m_id] = road_km
                            ckey = self._cache_key(origin_lat, origin_lng, d_lat, d_lng)
                            self.cache[ckey] = road_km
                            cache_updated = True
                        continue
            except Exception:
                # OSRM failed / timed out - fallback to detour factor
                pass

            # Fallback for this batch if OSRM call failed
            for _, d in batch:
                m_id = d["mandi_id"]
                aerial = float(d.get("aerial_distance_km", 0.0))
                road_km = round(aerial * ROAD_DETOUR_FACTOR, 1)
                results[m_id] = road_km

        if cache_updated:
            self._save_cache()

        return results
