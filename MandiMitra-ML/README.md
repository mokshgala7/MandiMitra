# MandiMitra ML System

## 1. What MandiMitra ML does
The MandiMitra ML repository provides a forecasting and decision support module that takes a specific crop, APMC mandi, and today's price, and predicts the expected future price of that crop in that mandi.

## 2. What ML predicts
The system predicts the `Modal Price` (₹/quintal) for approximately the next 2–3 market reporting observations (days).

## 3. What ML does NOT do
The ML module **does NOT** make hardcoded business decisions without context. It does not compute transport costs, net revenues, or rank markets based on distance directly inside the ML training loops. The ML module provides price forecasts and price-direction signals. **The backend is responsible for combining forecasts with farmer location, transport costs, middleman offers, and external factors to render the final SELL/HOLD decision.**

## 4. Supported crops
The ML module currently supports four crops:
- `Wheat`
- `Rice`
- `Tomato`
- `Cotton`

## 5. Forecast horizon
The model predicts expected prices for a **2–3 day horizon** (approximately 3 market reporting observations in the future).

## 6. Current forecasting methods
The system evaluates ML models against baseline methods using chronological out-of-sample testing. For highly volatile or sticky APMC markets, a "persistence" baseline (where the future price is predicted based on recent observations) often outperforms complex ML models. The system automatically selects the method with the lowest Mean Absolute Error (MAE) or employs directional ensemble models.

## 7. Model files
Trained model files (`*.joblib`) and their respective metadata (`*.json`) are stored in the `models/` directory.

## 8. Historical-data dependency
**Does inference require historical datasets?**
**YES, HISTORICAL DATA IS UTILIZED.** To support feature engineering (e.g. 7-day, 14-day, 30-day moving averages, momentum, and rolling volatilities), inference routines read the processed feature stores in `data/processed/` to build context for queried mandis.

## 9. Installation
Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```

## 10. Usage Examples
```python
from src.inference import predict_price

# Real examples across supported crops
predict_price(crop="wheat", market="APMC Latur", current_price=2650, date="2026-09-03")
predict_price(crop="rice", market="APMC Alibagh", current_price=3500, date="2026-09-03")
predict_price(crop="tomato", market="APMC Kamthi", current_price=2770, date="2026-09-03")
predict_price(crop="cotton", market="APMC Hinganghat", current_price=7900, date="2026-08-14")
```

---

# MandiMitra Data & Backend Integration Requirements

## Supported Crops
The MandiMitra system supports the following 4 primary crops:
1. **Wheat** (`Wheat` in source datasets)
2. **Rice** (`Rice` in source datasets)
3. **Tomato** (`Tomato` in source datasets)
4. **Cotton** (`Cotton` in source datasets)

---

## Source CSV Files
The ML project utilizes historical daily APMC price data for the state of **Maharashtra** spanning 2024 to 2026. All source files are located in `data/raw/`:

| Crop | File Name | Size (Bytes) | Total Rows | Columns | Date Range |
|------|-----------|--------------|------------|---------|------------|
| **Wheat** | `wheat2024.csv` | 2,206,035 | 18,338 | 12 | 2024-01-01 to 2024-12-31 |
| **Wheat** | `wheat2025.csv` | 2,619,222 | 21,703 | 12 | 2025-01-01 to 2025-12-31 |
| **Wheat** | `wheat2026.csv` | 2,205,065 | 17,914 | 12 | 2026-01-01 to 2026-09-03 |
| **Rice** | `Daily Price Report-01-01-2024 to 31-12-2024 for Maharashtra.csv` | 328,541 | 2,870 | 12 | 2024-01-01 to 2024-12-31 |
| **Rice** | `Daily Price Report-01-01-2025 to 31-12-2025 for Maharashtra.csv` | 369,197 | 3,176 | 12 | 2025-01-01 to 2025-12-31 |
| **Rice** | `Daily Price Report-01-01-2026 to 03-09-2026 for Maharashtra.csv` | 332,693 | 2,863 | 12 | 2026-01-01 to 2026-09-03 |
| **Tomato** | `tomato2024.csv` | 1,248,184 | 10,508 | 12 | 2024-01-01 to 2024-12-31 |
| **Tomato** | `tomato2025.csv` | 1,308,327 | 11,006 | 12 | 2025-01-01 to 2025-12-31 |
| **Tomato** | `tomato2026.csv` | 909,220 | 7,560 | 12 | 2026-01-01 to 2026-09-03 |
| **Cotton** | `cotton2024.csv` | 626,277 | 4,979 | 12 | 2024-01-01 to 2024-12-31 |
| **Cotton** | `cotton2025.csv` | 567,865 | 4,403 | 12 | 2025-01-01 to 2025-12-31 |
| **Cotton** | `cotton2026.csv` | 378,175 | 2,933 | 12 | 2026-01-01 to 2026-08-14 |

*Note: In all raw files, Row 0 contains an Agmarknet report banner title, and Row 1 contains the 12 column headers.*

---

## Dataset Summary

The table below summarizes the actual verified 2026 data coverage across all 4 crops:

| Crop | Dataset | 2026 Records | Unique Mandis | First 2026 Date | Latest 2026 Date |
|------|---------|--------------|---------------|-----------------|------------------|
| **Wheat** | `wheat2026.csv` | 17,914 | 222 | 2026-01-01 | 2026-09-03 |
| **Rice** | `Daily Price Report-01-01-2026 to 03-09-2026 for Maharashtra.csv` | 2,863 | 20 | 2026-01-01 | 2026-09-03 |
| **Tomato** | `tomato2026.csv` | 7,560 | 51 | 2026-01-01 | 2026-09-03 |
| **Cotton** | `cotton2026.csv` | 2,933 | 67 | 2026-01-01 | 2026-08-14 |

---

## 2026 Data Coverage

Analysis of records from `2026-01-01` through the actual maximum dates present in the source files:

1. **Wheat (`wheat2026.csv`)**:
   - First available 2026 date: `2026-01-01`
   - Latest available 2026 date: `2026-09-03`
   - Total 2026 records: `17,914`
   - Unique Mandis: `222`
   - Unique Districts: `30`
   - Unique States: `1` (`Maharashtra`)
   - Modal Price Range: `₹1,500` to `₹5,150` / quintal (Mean: `₹2,500.61`, Median: `₹2,419.00`)

2. **Rice (`Daily Price Report-01-01-2026 to 03-09-2026 for Maharashtra.csv`)**:
   - First available 2026 date: `2026-01-01`
   - Latest available 2026 date: `2026-09-03`
   - Total 2026 records: `2,863`
   - Unique Mandis: `20`
   - Unique Districts: `12`
   - Unique States: `1` (`Maharashtra`)
   - Modal Price Range: `₹2,050` to `₹11,100` / quintal (Mean: `₹4,709.59`, Median: `₹4,450.00`)

3. **Tomato (`tomato2026.csv`)**:
   - First available 2026 date: `2026-01-01`
   - Latest available 2026 date: `2026-09-03`
   - Total 2026 records: `7,560`
   - Unique Mandis: `51`
   - Unique Districts: `18`
   - Unique States: `1` (`Maharashtra`)
   - Modal Price Range: `₹300` to `₹5,500` / quintal (Mean: `₹1,686.01`, Median: `₹1,500.00`)

4. **Cotton (`cotton2026.csv`)**:
   - First available 2026 date: `2026-01-01`
   - Latest available 2026 date: `2026-08-14` *(Note: Cotton trading in Maharashtra mandis concludes seasonally by mid-August)*
   - Total 2026 records: `2,933`
   - Unique Mandis: `67`
   - Unique Districts: `17`
   - Unique States: `1` (`Maharashtra`)
   - Modal Price Range: `₹5,000` to `₹9,850` / quintal (Mean: `₹7,843.94`, Median: `₹7,849.00`)

---

## Mandi Coverage

For complete, detailed tables of all mandis grouped by `State → District → Mandi` with observation counts and latest 2026 prices, see the dedicated reference file:
👉 **[docs/mandi-data-reference.md](file:///Users/moksh/Desktop/MandiMitra-ML/docs/mandi-data-reference.md)**

### Mandi Distribution by Crop & District (2026 Overview):
- **Wheat (222 Mandis across 30 Districts)**: Ahilyanagar (17), Akola (6), Amarawati (12), Beed (9), Bhandara (1), Buldhana (15), Chandrapur (9), Chattrapati Sambhajinagar (11), Dharashiv (8), Dhule (5), Hingoli (3), Jalgaon (21), Jalna (8), Kolhapur (1), Latur (9), Mumbai (2), Nagpur (13), Nanded (10), Nandurbar (6), Nashik (16), Palghar (1), Parbhani (4), Pune (9), Raigad (1), Sangli (1), Satara (5), Solapur (4), Thane (1), Wardha (6), Washim (6), Yavatmal (7).
- **Rice (20 Mandis across 12 Districts)**: Chandrapur (1), Dharashiv (1), Gadchiroli (1), Kolhapur (1), Mumbai (2), Nagpur (4), Nashik (1), Palghar (1), Pune (4), Raigad (2), Solapur (1), Thane (1).
- **Tomato (51 Mandis across 18 Districts)**: Ahilyanagar (4), Amarawati (1), Chandrapur (1), Chattrapati Sambhajinagar (4), Dharashiv (1), Jalgaon (2), Kolhapur (2), Mumbai (2), Nagpur (2), Nandurbar (2), Nashik (7), Pune (10), Raigad (2), Ratnagiri (1), Sangli (1), Satara (5), Solapur (3), Thane (1).
- **Cotton (67 Mandis across 17 Districts)**: Ahilyanagar (1), Akola (3), Amarawati (11), Beed (4), Buldhana (6), Chandrapur (7), Chattrapati Sambhajinagar (1), Gadchiroli (1), Hingoli (1), Jalgaon (9), Jalna (3), Nagpur (5), Nanded (2), Nandurbar (1), Parbhani (2), Wardha (5), Yavatmal (5).

### Mandi Naming Characteristics & Variations:
- **APMC Prefix**: The majority of markets are prefixed with `APMC` (e.g. `APMC Latur`, `APMC Karjat`, `APMC Akola`).
- **Sub-Markets & Secondary Yards**: Specific sub-yards are identified with parenthetical suffixes (e.g., `Karjat(Rashin)`, `Rahuri(Vambori)`, `Pune(Manjri)`, `Pune(Moshi)`, `Junnar(Otur)`, `Kolhapur(Laxmipuri)`).
- **Special Cooperatives**: Private and cooperative markets appear with formal names (e.g., `Omchatinya Multi State Agro Purpose Co-Op Society, Dist Ahilyanagar`, `M/S Kalpana Agri Commodities Marketing, Nagpur`).
- **Trailing Whitespaces**: Many raw entries contain leading or trailing whitespaces that must be stripped during ingestion.

---

## Mandi Location Requirements

The source CSV files contain only administrative division names:
- `State/UT` (Available: `Maharashtra`)
- `District` (Available: 31 unique districts across crops)
- `Market` (Available: APMC mandi name)

**Fields NOT present in the source CSVs:**
- `Taluka` (Not present)
- `Village` (Not present)
- `Area` (Not present)
- `Latitude` (Not present)
- `Longitude` (Not present)

> [!IMPORTANT]
> **Mandi coordinates are not present in the source CSV and must be mapped/added by the backend/data layer.**
> To compute one-way driving distances and transport costs, the backend or database layer must maintain a geocoding reference table mapping `(State, District, Market)` to exact `(latitude, longitude)`.

---

## Price Columns

Each source dataset contains three price fields in Indian Rupees:
1. **`Min Price`** (`float`): The minimum auction transaction price recorded on that trading day.
2. **`Max Price`** (`float`): The highest auction transaction price recorded on that trading day.
3. **`Modal Price`** (`float`): The most frequent (mode) price at which the majority of trade lots were settled in the mandi.

### Primary Price Selection: `Modal Price`
- **Reasoning**: `Modal Price` is selected as the primary mandi price for MandiMitra models and backend services. `Min Price` and `Max Price` reflect extreme tails (e.g., low-grade, damaged produce or small premium-quality sample lots), whereas `Modal Price` accurately reflects the bulk market-clearing price at which an average farmer will sell their crop.
- **Unit**: Stated as `Rs./Quintal` across all datasets (1 Quintal = 100 kg).

---

## Latest Mandi Price

For each active mandi, the backend serves the latest available record to represent today's market price:
- **Wheat**: 222 mandis reporting up to `2026-09-03`.
- **Rice**: 20 mandis reporting up to `2026-09-03`.
- **Tomato**: 51 mandis reporting up to `2026-09-03`.
- **Cotton**: 67 mandis reporting up to `2026-08-14`.

The backend retrieves the latest record per mandi containing `(Crop, State, District, Market, Latest Date, Modal Price, Min Price, Max Price, Price Unit, Variety, Grade)`.

---

## Historical Price Data

To power interactive stock-market style price trend charts and ML feature engineering, historical price series are constructed by querying:
- **Date**: `Price Date` (parsed from `DD-MM-YYYY` to ISO format `YYYY-MM-DD`)
- **Price**: `Modal Price` (Numeric ₹/quintal)
- **Filters**: `Market` (Mandi Name) and `Commodity` (Crop)
- **Time Range**: `2024-01-01` through `2026-09-03` (or `2026-08-14` for Cotton).

---

## Arrival Data

- **Inspection Finding**: Mandi arrival quantities (e.g., `Arrivals (Tonnes)` or `Arrival Quantity`) are **NOT present** in the 12 raw Agmarknet CSV files.
- **Design Accommodation**: The ML models and pipelines operate self-contained on price and calendar features. Optional external arrival information (e.g. daily arrival volume in tonnes) can be ingested via the `src/supply_features.py` module if provided by external APIs, but is not required for baseline inference.

---

## Data Dictionary

The table below describes all 12 columns found in the raw CSV files:

| Source Column | Data Type | Meaning / Description | Used By |
|---------------|-----------|-----------------------|---------|
| `State/UT` | `string` | State or Union Territory name (e.g., `Maharashtra`) | ML / Backend filtering |
| `District` | `string` | Administrative district of the mandi | ML / Backend geocoding |
| `Market` | `string` | Official APMC Mandi / Market yard name | ML grouping / Backend key |
| `Commodity Group` | `string` | Broad category (e.g., `Cereals`, `Vegetables`, `Fibres`) | Reference |
| `Commodity` | `string` | Crop name (`Wheat`, `Rice`, `Tomato`, `Cotton`) | ML model selection / Backend |
| `Variety` | `string` | Specific botanical or trade variety (e.g., `Lokwan`, `Deshi`, `Other`) | ML segmenting / Baseline |
| `Grade` | `string` | Quality grade assigned in APMC auction (`FAQ`, `Non-FAQ`, `Local`) | ML segmenting / Filtering |
| `Min Price` | `numeric (str)` | Minimum price recorded on date (₹/quintal) | Range analytics |
| `Max Price` | `numeric (str)` | Maximum price recorded on date (₹/quintal) | Range analytics |
| `Modal Price` | `numeric (str)` | Modal (most frequent) price on date (₹/quintal) | **Primary ML Target & Price** |
| `Price Unit` | `string` | Unit of measurement (`Rs./Quintal`) | Quantity conversions |
| `Price Date` | `date (str)` | Date of auction / reporting (`DD-MM-YYYY`) | ML time-series index |

---

## ML Training Inputs

The ML model pipeline uses the following features engineered from raw historical observations:
1. **Target Variable**: Future `Modal Price` (₹/quintal) at horizon $t+3$ market days.
2. **Historical Price Lags**: $P_{t-1}, P_{t-2}, P_{t-3}, P_{t-7}, P_{t-14}, P_{t-30}$.
3. **Rolling Statistics**: 7-day, 14-day, and 30-day Rolling Mean, Rolling Standard Deviation, Rolling Min, Rolling Max, and Volatility.
4. **Price Momentum**: Percentage price changes over 1-day, 3-day, and 7-day windows.
5. **Calendar & Seasonality Features**: Day of week, Month, Day of year, Is weekend.
6. **Market & Variety Encodings**: Target-encoded or grouped APMC Market, Variety, and Grade identifiers.
7. **Chronological 80/20 Train-Test Split**: Models are trained on past chronological data (80%) and evaluated strictly out-of-sample on recent observations (20%).

---

## ML Prediction Output

The ML prediction interface produces structured forecasts for the next 2–3 market days:

```json
{
  "crop": "Wheat",
  "market": "APMC Latur",
  "current_price": 2650.0,
  "date": "2026-09-03",
  "price_unit": "Rs./Quintal",
  "forecast_horizon_days": 3,
  "predictions": [
    {
      "day": 1,
      "horizon_date": "2026-09-04",
      "predicted_price": 2660.0
    },
    {
      "day": 2,
      "horizon_date": "2026-09-05",
      "predicted_price": 2675.0
    },
    {
      "day": 3,
      "horizon_date": "2026-09-06",
      "predicted_price": 2685.0
    }
  ],
  "expected_direction": "UP",
  "confidence": 0.82
}
```

---

## Distance Calculation Requirement

- The backend calculates the straight-line or road distance (in Kilometers) between the **Farmer Location** and each candidate **Mandi Location**:
  $$\text{Distance (KM)} = \text{Geodesic}(\text{Farmer Lat/Lon}, \text{Mandi Lat/Lon})$$
- As coordinates are not in the raw CSVs, the backend must supply Mandi coordinates from its internal location master table.

---

## Transportation Cost

- **Rate**: **₹10 per KM** (One-Way transportation).
- **Formula**:
  $$\text{Transportation Cost (₹)} = \text{Distance (KM)} \times 10$$
- Transportation cost is trip-based and subtracted from the total gross revenue.

---

## Farmer Quantity Calculation

Farmers enter their harvest quantity in **Kilograms (KG)**, while mandi prices are reported per **Quintal**:
1. **Unit Conversion**:
   $$\text{Quantity (Quintals)} = \frac{\text{Quantity (KG)}}{100}$$
2. **Gross Mandi Revenue**:
   $$\text{Gross Value (₹)} = \text{Quantity (Quintals)} \times \text{Mandi Price (₹/Quintal)}$$
3. **Net Mandi Return**:
   $$\text{Net Mandi Return (₹)} = \text{Gross Value (₹)} - \text{Transportation Cost (₹)}$$

---

## Middleman Comparison

The system compares the net financial return of traveling to an APMC Mandi versus selling locally to a middleman / village aggregator:
1. **Farmer Inputs**:
   - Middleman offered price (₹/Quintal)
   - Middleman commission / handling fee (₹/Quintal or flat ₹)
   - Other local deductions (weighing fees, loading charges)
2. **Effective Middleman Net**:
   $$\text{Effective Middleman Price (₹/Quintal)} = \text{Offered Price} - \text{Commission} - \text{Charges}$$
   $$\text{Net Middleman Return (₹)} = \text{Effective Middleman Price} \times \text{Quantity (Quintals)}$$
3. **Net Benefit Analysis**:
   $$\Delta_{\text{Net}} = \text{Net Mandi Return} - \text{Net Middleman Return}$$
   If $\Delta_{\text{Net}} > 0$, selling at the APMC Mandi yields higher net profit even after transportation expenses.

---

## Sell vs Hold Recommendation

The recommendation engine outputs one of two core actions:
1. **`SELL TODAY`**: Advised when the current price is at or near recent cyclical peaks, or when predicted future price movement is flat/downward ($\Delta P \le 0$), or when holding costs/perishability risks exceed expected price gains.
2. **`HOLD FOR 2–3 DAYS`**: Advised when the ML model predicts a clear upward price momentum ($\Delta P > 0$) that exceeds transportation and holding thresholds.

*Note: Weather forecasts (e.g., rain, high humidity) are presented as **informational risk alerts** in the application interface to warn farmers about transport disruptions or crop spoilage, and do NOT directly modify the underlying ML price prediction equations.*

---

## Backend Integration Requirements

The backend application layer requires the following 11 data elements from the ML and data subsystems:
1. **Crop**: Selected crop entity (`Wheat`, `Rice`, `Tomato`, `Cotton`).
2. **Mandi**: Target APMC mandi name matching the standardized reference catalog.
3. **Current / Latest Price**: Most recent reported `Modal Price` (₹/Quintal).
4. **Historical Prices**: Time series of `(Date, Modal Price)` for trend charting.
5. **Predicted Prices**: 2–3 day forecast values generated by ML / baseline engine.
6. **Mandi Location**: Administrative identifiers (`State`, `District`, `Market`).
7. **Mandi Coordinates**: Backend-provided `(Latitude, Longitude)` for each mandi.
8. **Farmer Location**: Geocoded user origin coordinates `(Latitude, Longitude)`.
9. **Distance**: Computed one-way distance in Kilometers between farmer and mandi.
10. **Transportation Cost**: Calculated at ₹10/KM one-way.
11. **Middleman Comparison Data**: Computed net difference between mandi return and middleman offer.

---

## Data Cleaning & Quality Notes

During inspection of the raw Agmarknet datasets, the following data characteristics and edge cases were identified:
1. **Header Banner Row**: All raw CSV files contain a metadata banner in row 0. Ingestion scripts must execute with `skiprows=1`.
2. **Comma-Formatted Numbers**: Numeric price strings frequently contain thousands commas (e.g. `"2,650"`). All loaders must sanitize strings by removing commas prior to numeric type conversion.
3. **Date Formats**: Date strings follow day-first formatting (`DD-MM-YYYY`).
4. **Cotton Seasonality**: Cotton 2026 observations end on `2026-08-14` due to seasonal closure of cotton market arrivals.
5. **Mandi Naming Quirks**: Sub-markets include parenthetical district or area specifications (e.g. `Karjat(Rashin)`, `APMC Karjat(Raigad)`). Names should be preserved verbatim as per the reference catalog.
6. **Absence of Coordinates**: No latitude or longitude coordinates exist in the raw CSVs.
7. **Absence of Arrival Volumes**: No arrival quantity columns exist in the raw price CSVs.
8. **Duplicate Rows**: Verified 0 exact duplicate rows across all 12 raw files.
