"""
Script to generate docs/mandi-data-reference.md based on actual 2026 data.
"""

from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")
CROPS = {
    "Wheat": "wheat2026.csv",
    "Rice": "Daily Price Report-01-01-2026 to 03-09-2026 for Maharashtra.csv",
    "Tomato": "tomato2026.csv",
    "Cotton": "cotton2026.csv",
}


def generate():
    doc = []
    doc.append("# MandiMitra 2026 Mandi Data Reference Guide\n\n")
    doc.append(
        "This document provides the complete, authoritative reference of all **APMC Mandis** present in the 2026 dataset for the 4 supported crops in MandiMitra (**Wheat**, **Rice**, **Tomato**, and **Cotton**).\n\n"
    )
    doc.append(
        "> [!NOTE]\n> All data is extracted directly from the verified 2026 source CSV files in `data/raw/`. Mandi coordinates are **not present** in the source files and must be supplied by the backend/geocoding layer.\n\n"
    )

    # Summary table
    doc.append("## 1. 2026 Mandi Coverage Overview\n\n")
    doc.append(
        "| Crop | Source 2026 CSV | 2026 Records | Unique States | Unique Districts | Unique Mandis | Date Range |\n"
    )
    doc.append(
        "|------|-----------------|--------------|---------------|------------------|---------------|------------|\n"
    )

    crop_details = {}

    for crop_name, fname in CROPS.items():
        fpath = RAW_DIR / fname
        df = pd.read_csv(fpath, skiprows=1, encoding="utf-8", low_memory=False)
        df.columns = [c.strip() for c in df.columns]
        for c in df.columns:
            if df[c].dtype == object:
                df[c] = df[c].astype(str).str.strip()
        df["Price Date_dt"] = pd.to_datetime(
            df["Price Date"], format="%d-%m-%Y", errors="coerce"
        )
        for p in ["Min Price", "Max Price", "Modal Price"]:
            df[p + "_num"] = pd.to_numeric(
                df[p].str.replace(",", ""), errors="coerce"
            )

        n_records = len(df)
        n_states = df["State/UT"].nunique()
        n_districts = df["District"].nunique()
        n_mandis = df["Market"].nunique()
        min_date = df["Price Date_dt"].min().strftime("%Y-%m-%d")
        max_date = df["Price Date_dt"].max().strftime("%Y-%m-%d")

        doc.append(
            f"| **{crop_name}** | `{fname}` | {n_records:,} | {n_states} | {n_districts} | {n_mandis} | {min_date} to {max_date} |\n"
        )

        hierarchy = {}
        for st, st_df in df.groupby("State/UT"):
            hierarchy[st] = {}
            for dist, dist_df in st_df.groupby("District"):
                mandis_in_dist = []
                for mkt, mkt_df in dist_df.groupby("Market"):
                    latest_row = (
                        mkt_df.sort_values("Price Date_dt", ascending=False).iloc[
                            0
                        ]
                    )
                    mandis_in_dist.append(
                        {
                            "market": mkt,
                            "records": len(mkt_df),
                            "latest_date": latest_row[
                                "Price Date_dt"
                            ].strftime("%Y-%m-%d"),
                            "latest_modal_price": latest_row["Modal Price_num"],
                            "price_unit": latest_row["Price Unit"],
                            "variety": latest_row["Variety"],
                            "grade": latest_row["Grade"],
                        }
                    )
                hierarchy[st][dist] = sorted(
                    mandis_in_dist, key=lambda x: x["market"]
                )
        crop_details[crop_name] = hierarchy

    doc.append("\n---\n\n")

    # Detailed Mandi Listings
    doc.append("## 2. Complete Mandi Listings by Crop (2026 Data)\n\n")

    for crop_name, hierarchy in crop_details.items():
        crop_idx = list(crop_details.keys()).index(crop_name) + 1
        doc.append(f"### 2.{crop_idx} {crop_name} Mandis\n\n")
        for st, dists in hierarchy.items():
            total_mandis = sum(len(m_list) for m_list in dists.values())
            doc.append(
                f"**State:** `{st}` ({total_mandis} Mandis across {len(dists)} Districts)\n\n"
            )
            for dist, mandis in sorted(dists.items()):
                doc.append(
                    f"#### District: {dist} ({len(mandis)} Mandis)\n\n"
                )
                doc.append(
                    "| APMC Mandi / Market | 2026 Observations | Latest Reported Date | Latest Modal Price | Price Unit | Variety | Grade |\n"
                )
                doc.append(
                    "|---------------------|-------------------|----------------------|--------------------|------------|---------|-------|\n"
                )
                for m in mandis:
                    mkt_name = m["market"]
                    recs = m["records"]
                    ldate = m["latest_date"]
                    lprice = m["latest_modal_price"]
                    punit = m["price_unit"]
                    var = m["variety"]
                    grd = m["grade"]
                    doc.append(
                        f"| {mkt_name} | {recs} | {ldate} | ₹{lprice:,.0f} | {punit} | {var} | {grd} |\n"
                    )
                doc.append("\n")

    ref_content = "".join(doc)
    with open("docs/mandi-data-reference.md", "w", encoding="utf-8") as f:
        f.write(ref_content)

    print(
        f"docs/mandi-data-reference.md generated successfully ({len(ref_content)} bytes)!"
    )


if __name__ == "__main__":
    generate()
