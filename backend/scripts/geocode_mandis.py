import json
import time
import ssl
import certifi
import re
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

ctx = ssl.create_default_context(cafile=certifi.where())
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "public" / "data"
MASTER_FILE = DATA_DIR / "mandi_master.json"
CACHE_FILE = BASE_DIR / "backend" / "data" / "geocoding_cache.json"

# Explicit alias translations for known Agmarknet spelling variants to real geographic entities
DISTRICT_ALIASES = {
    "amarawati": "Amravati",
    "chattrapati sambhajinagar": "Chhatrapati Sambhajinagar",
    "jalana": "Jalna",
    "buldhana": "Buldhana",
}

TOWN_ALIASES = {
    "amrawati(frui & veg. market)": "Amravati",
    "apmc achalpur": "Achalpur",
    "apmc amarawati": "Amravati",
    "apmc anajngaon": "Anjangaon Surji",
    "apmc chandur bazar": "Chandurbazar",
    "apmc chandur railway": "Chandur Railway",
    "apmc chattrapati sambhajinagar": "Chhatrapati Sambhajinagar",
    "apmc daryapur": "Daryapur",
    "apmc dhamngaon-railway": "Dhamangaon Railway",
    "apmc dharni": "Dharni",
    "apmc fulmbri": "Phulambri",
    "apmc gangapur": "Gangapur",
    "apmc kannad": "Kannad",
    "apmc lasur station": "Lasur Station",
    "apmc morshi": "Morshi",
    "apmc nandgaon khandeshwar": "Nandgaon Khandeshwar",
    "apmc paithan": "Paithan",
    "apmc sillod": "Sillod",
    "apmc vaijpur": "Vaijapur",
    "apmc varud": "Warud",
    "sillod(bharadi)": "Bharadi",
    "varud(rajura bazar)": "Rajura Bazar",
    "lasalgaon(niphad)": "Lasalgaon",
    "shevgaon(bodhegaon)": "Bodhegaon",
}

def clean_mandi_query(mandi_name: str, district: str) -> list:
    queries = []
    dist_norm = district.strip().lower()
    dist_clean = DISTRICT_ALIASES.get(dist_norm, district.strip())
    
    name_norm = mandi_name.strip().lower()
    if name_norm in TOWN_ALIASES:
        town = TOWN_ALIASES[name_norm]
        queries.append(f"{town}, {dist_clean}, Maharashtra, India")
        queries.append(f"{town}, Maharashtra, India")
    
    # Strip APMC / Market / parentheses
    stripped = re.sub(r'\b(APMC|Market|Frui|Veg\.)\b', '', mandi_name, flags=re.IGNORECASE)
    stripped = re.sub(r'\(.*?\)', '', stripped).strip()
    if stripped and stripped.lower() != name_norm:
        queries.append(f"{stripped}, {dist_clean}, Maharashtra, India")
        queries.append(f"{stripped}, Maharashtra, India")
        
    # Full original query
    queries.append(f"{mandi_name}, {dist_clean}, Maharashtra, India")
    return queries

def main():
    if not MASTER_FILE.exists():
        print("Mandi master file not found at", MASTER_FILE)
        return

    with open(MASTER_FILE, "r", encoding="utf-8") as f:
        mandis = json.load(f)

    cache = {}
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)

    geolocator = Nominatim(user_agent="mandimitra_geocoder_v2", ssl_context=ctx)

    updated_count = 0
    already_valid = 0
    missing_count = 0

    for i, m in enumerate(mandis):
        if m.get("latitude") is not None and m.get("longitude") is not None:
            already_valid += 1
            continue

        queries = clean_mandi_query(m["mandi_name"], m["district"])
        resolved = False

        for q in queries:
            if q in cache and cache[q] is not None:
                m["latitude"] = cache[q]["lat"]
                m["longitude"] = cache[q]["lon"]
                m["geocoding_source"] = "osm_nominatim_cache"
                m["geocoding_confidence"] = "verified"
                resolved = True
                updated_count += 1
                break
                
            print(f"[{i+1}/{len(mandis)}] Geocoding: {q}")
            try:
                time.sleep(1.2)
                location = geolocator.geocode(q, timeout=10)
                if location:
                    m["latitude"] = round(location.latitude, 6)
                    m["longitude"] = round(location.longitude, 6)
                    m["geocoding_source"] = "osm_nominatim"
                    m["geocoding_confidence"] = "verified"
                    cache[q] = {"lat": m["latitude"], "lon": m["longitude"]}
                    resolved = True
                    updated_count += 1
                    print(f"  -> SUCCESS: ({m['latitude']}, {m['longitude']})")
                    break
                else:
                    cache[q] = None
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                print(f"  -> Service Warning: {e}")
                time.sleep(2)
                continue

        if not resolved:
            print(f"  -> UNRESOLVED: {m['mandi_name']} in {m['district']}")
            m["latitude"] = None
            m["longitude"] = None
            m["geocoding_confidence"] = "unresolved"
            missing_count += 1

        if (i + 1) % 5 == 0:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
            with open(MASTER_FILE, "w", encoding="utf-8") as f:
                json.dump(mandis, f, indent=2)

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
    with open(MASTER_FILE, "w", encoding="utf-8") as f:
        json.dump(mandis, f, indent=2)

    print("\n" + "=" * 50)
    print(f"Total Mandis: {len(mandis)}")
    print(f"Already had coordinates: {already_valid}")
    print(f"Newly resolved: {updated_count}")
    print(f"Remaining unresolved: {missing_count}")
    print("=" * 50)

if __name__ == "__main__":
    main()

