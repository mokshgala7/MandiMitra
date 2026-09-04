import json
import re
from datetime import datetime
from pathlib import Path
import pandas as pd
from sqlalchemy import text

# Import database connection
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database import SessionLocal, engine
from app.models import Mandi, CropPrice

DATA_DIR = BASE_DIR.parent / "public" / "data"
if not DATA_DIR.exists():
    DATA_DIR = BASE_DIR.parent / "frontend" / "public" / "data"
MANDI_MASTER_FILE = DATA_DIR / "mandi_master.json"

CROPS = ["wheat", "rice", "tomato", "cotton"]

def create_mandi_id(state: str, district: str, market: str) -> str:
    s = f"{state}-{district}-{market}".lower()
    return re.sub(r'[^a-z0-9]+', '-', s)

def seed_mandis(db):
    print("--- Seeding Mandis Master Table ---")
    if not MANDI_MASTER_FILE.exists():
        print(f"Error: {MANDI_MASTER_FILE} does not exist.")
        return

    with open(MANDI_MASTER_FILE, "r", encoding="utf-8") as f:
        mandis_data = json.load(f)

    existing_ids = set(r[0] for r in db.query(Mandi.mandi_id).all())
    new_mandis = []

    for m in mandis_data:
        mandi_id = m.get("mandi_id")
        if not mandi_id or mandi_id in existing_ids:
            continue

        lat = m.get("latitude")
        lng = m.get("longitude")
        if lat is None or lng is None:
            continue

        new_mandis.append(Mandi(
            mandi_id=mandi_id,
            name=m.get("mandi_name", ""),
            district=m.get("district", ""),
            state=m.get("state", ""),
            latitude=float(lat),
            longitude=float(lng),
            geocoding_source=m.get("geocoding_source", "osm_nominatim"),
            geocoding_confidence=m.get("geocoding_confidence", "verified")
        ))
        existing_ids.add(mandi_id)

    if new_mandis:
        db.bulk_save_objects(new_mandis)
        db.commit()
        print(f"Successfully inserted {len(new_mandis)} mandis into MySQL.")
    else:
        print(f"Mandis table already up to date ({len(existing_ids)} mandis).")

def seed_prices(db):
    print("--- Seeding Crop Prices Table ---")
    # Fetch valid mandi_ids in database
    valid_mandi_ids = set(r[0] for r in db.query(Mandi.mandi_id).all())

    for crop in CROPS:
        csv_path = DATA_DIR / f"{crop}.csv"
        if not csv_path.exists():
            print(f"Warning: {csv_path} not found.")
            continue

        print(f"Processing {crop} prices from {csv_path.name}...")
        df = pd.read_csv(csv_path, skiprows=1, encoding="utf-8")
        df.columns = [c.strip() for c in df.columns]

        # Numeric price conversion
        for p_col in ["Modal Price", "Min Price", "Max Price"]:
            df[p_col] = pd.to_numeric(df[p_col].astype(str).str.replace(",", ""), errors="coerce")

        df = df[df["Modal Price"].notna() & (df["Modal Price"] > 0)]

        price_records = []
        for _, row in df.iterrows():
            state = str(row.get("State/UT", "")).strip()
            district = str(row.get("District", "")).strip()
            market = str(row.get("Market", "")).strip()
            mandi_id = create_mandi_id(state, district, market)

            if mandi_id not in valid_mandi_ids:
                continue

            try:
                # Format: DD-MM-YYYY
                parts = str(row["Price Date"]).strip().split("-")
                p_date = datetime(int(parts[2]), int(parts[1]), int(parts[0])).date()
            except Exception:
                continue

            price_records.append({
                "mandi_id": mandi_id,
                "crop": crop,
                "variety": str(row.get("Variety", "Other")).strip(),
                "grade": str(row.get("Grade", "FAQ")).strip(),
                "price_date": p_date,
                "min_price": float(row.get("Min Price", row["Modal Price"])),
                "max_price": float(row.get("Max Price", row["Modal Price"])),
                "modal_price": float(row["Modal Price"]),
                "price_unit": str(row.get("Price Unit", "Rs./Quintal")).strip()
            })

        print(f"Inserting {len(price_records)} valid records for {crop}...")
        if price_records:
            # Batch insert in chunks of 5000
            chunk_size = 5000
            for i in range(0, len(price_records), chunk_size):
                chunk = price_records[i:i + chunk_size]
                db.bulk_insert_mappings(CropPrice, chunk)
                db.commit()

        print(f"Done seeding {crop}.")

def main():
    db = SessionLocal()
    try:
        seed_mandis(db)
        seed_prices(db)
        print("\nAll database seeding completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    main()
