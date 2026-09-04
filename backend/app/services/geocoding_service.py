import ssl
import certifi
import time
from typing import Dict, Any, Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

ctx = ssl.create_default_context(cafile=certifi.where())
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

class GeocodingService:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="mandimitra_farmer_geocoder", ssl_context=ctx)
        self.cache = {}

    def geocode_address(self, state: str, district: str, village: Optional[str] = None) -> Optional[Dict[str, float]]:
        queries = []
        if village and village.strip():
            queries.append(f"{village.strip()}, {district.strip()}, {state.strip()}, India")
        queries.append(f"{district.strip()}, {state.strip()}, India")

        for q in queries:
            if q in self.cache:
                return self.cache[q]

            try:
                time.sleep(1.0)
                location = self.geolocator.geocode(q, timeout=10)
                if location:
                    coords = {
                        "latitude": round(location.latitude, 6),
                        "longitude": round(location.longitude, 6)
                    }
                    self.cache[q] = coords
                    return coords
            except (GeocoderTimedOut, GeocoderServiceError):
                continue

        return None
