import Papa from 'papaparse';

/**
 * Clean up the CSV text by removing the Agmarknet banner row if it exists.
 * The actual headers should start with 'State/UT'.
 */
const cleanCsvText = (text) => {
  const lines = text.split('\n');
  if (lines.length > 0 && !lines[0].startsWith('State/UT')) {
    // If the first line is the banner, remove it
    lines.shift();
  }
  return lines.join('\n');
};

/**
 * Parse a localized price string like "5,700.00" into a float.
 */
const parsePrice = (priceStr) => {
  if (!priceStr) return 0;
  // Remove commas and spaces
  const cleanStr = String(priceStr).replace(/,/g, '').trim();
  const val = parseFloat(cleanStr);
  return isNaN(val) ? 0 : val;
};

/**
 * Parse date string "DD-MM-YYYY" into a JS Date object.
 */
const parseDate = (dateStr) => {
  if (!dateStr) return null;
  const parts = dateStr.split('-');
  if (parts.length !== 3) return null;
  // parts[0] is DD, parts[1] is MM, parts[2] is YYYY
  return new Date(`${parts[2]}-${parts[1]}-${parts[0]}`);
};

/**
 * Fetch and parse a crop CSV file from public/data/
 */
export const fetchCropData = async (cropId) => {
  try {
    const response = await fetch(`/data/${cropId}.csv`);
    if (!response.ok) {
      throw new Error(`Failed to load ${cropId}.csv`);
    }
    
    let csvText = await response.text();
    csvText = cleanCsvText(csvText);

    return new Promise((resolve, reject) => {
      Papa.parse(csvText, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          const rawData = results.data;
          
          // Map to a cleaner internal format
          const formattedData = rawData
            .filter(row => row['Modal Price']) // only keep rows with prices
            .map(row => ({
              state: row['State/UT']?.trim(),
              district: row['District']?.trim(),
              market: row['Market']?.trim(),
              variety: row['Variety']?.trim(),
              grade: row['Grade']?.trim(),
              minPrice: parsePrice(row['Min Price']),
              maxPrice: parsePrice(row['Max Price']),
              modalPrice: parsePrice(row['Modal Price']),
              priceUnit: row['Price Unit']?.trim(),
              priceDate: parseDate(row['Price Date']),
              rawDateString: row['Price Date']
            }))
            .filter(row => row.priceDate && row.modalPrice > 0);
            
          // Sort by date ascending (oldest to newest)
          formattedData.sort((a, b) => a.priceDate - b.priceDate);
          
          resolve(formattedData);
        },
        error: (error) => {
          reject(error);
        }
      });
    });
  } catch (error) {
    console.error('Error fetching crop data:', error);
    return [];
  }
};

/**
 * Extracts unique mandis from the dataset with their latest available modal price.
 */
export const extractMandisFromData = (data) => {
  const mandiMap = new Map();
  
  data.forEach(row => {
    // Unique key for a mandi
    const key = `${row.market}-${row.district}-${row.state}`;
    
    // Since data is sorted ascending by date, replacing existing keys 
    // will ensure we have the latest record for each mandi.
    mandiMap.set(key, {
      mandi_id: key,
      mandi_name: row.market,
      district: row.district,
      state: row.state,
      latest_price: row.modalPrice,
      price_unit: row.priceUnit,
      price_date: row.rawDateString,
      timestamp: row.priceDate.getTime()
    });
  });
  
  // Return as array, sorted alphabetically by mandi name
  return Array.from(mandiMap.values()).sort((a, b) => 
    a.mandi_name.localeCompare(b.mandi_name)
  );
};

/**
 * Generate chart data aggregated by date (average modal price across all mandis for a given day)
 * This creates a simplified "Global" price trend for the crop.
 */
export const generateChartData = (data, period) => {
  if (!data || data.length === 0) return [];

  // Group by date string (e.g. "DD-MM-YYYY")
  const dateMap = new Map();
  data.forEach(row => {
    const ds = row.rawDateString;
    if (!dateMap.has(ds)) {
      dateMap.set(ds, { sum: 0, count: 0, dateObj: row.priceDate });
    }
    const entry = dateMap.get(ds);
    entry.sum += row.modalPrice;
    entry.count += 1;
  });
  
  let chartData = Array.from(dateMap.entries()).map(([ds, entry]) => ({
    date: ds,
    timestamp: entry.dateObj.getTime(),
    price: Math.round(entry.sum / entry.count) // Average modal price for the day
  }));
  
  // Sort by date ascending
  chartData.sort((a, b) => a.timestamp - b.timestamp);
  
  if (chartData.length === 0) return [];
  
  // Apply time period filtering
  const latestTimestamp = chartData[chartData.length - 1].timestamp;
  let cutoffTimestamp = 0;
  
  const dayMs = 24 * 60 * 60 * 1000;
  
  switch(period) {
    case '1D':
      cutoffTimestamp = latestTimestamp - (1 * dayMs);
      break;
    case '1W':
      cutoffTimestamp = latestTimestamp - (7 * dayMs);
      break;
    case '3W':
      cutoffTimestamp = latestTimestamp - (21 * dayMs);
      break;
    case '1M':
      cutoffTimestamp = latestTimestamp - (30 * dayMs);
      break;
    case '6M':
      cutoffTimestamp = latestTimestamp - (180 * dayMs);
      break;
    case 'YTD':
    default:
      // YTD: From Jan 1 of the latest year in dataset
      const latestDate = new Date(latestTimestamp);
      cutoffTimestamp = new Date(`${latestDate.getFullYear()}-01-01`).getTime();
      break;
  }
  
  chartData = chartData.filter(d => d.timestamp >= cutoffTimestamp);
  
  return chartData;
};

/**
 * Fetch historical prices directly from FastAPI backend /api/v1/prices/history
 */
export const fetchHistoricalPriceApi = async (cropId, period = 'YTD', mandiId = null) => {
  try {
    let url = `http://localhost:8000/api/v1/prices/history?crop=${cropId}&period=${period}`;
    if (mandiId) {
      url += `&mandi_id=${mandiId}`;
    }
    const resp = await fetch(url);
    if (resp.ok) {
      const result = await resp.json();
      return result.data_points || [];
    }
  } catch (err) {
    console.warn('Backend price history API unreachable, fallback to client parsing:', err);
  }
  return null;
};

