import fs from 'fs';
import path from 'path';
import Papa from 'papaparse';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const dataDir = path.join(__dirname, '../public/data');
const crops = ['wheat', 'rice', 'tomato', 'cotton'];

// Helper to clean Agmarknet banner
const cleanCsvText = (text) => {
  const lines = text.split('\n');
  if (lines.length > 0 && !lines[0].startsWith('State/UT')) {
    lines.shift();
  }
  return lines.join('\n');
};

const mandiMap = new Map();

crops.forEach(crop => {
  const filePath = path.join(dataDir, `${crop}.csv`);
  if (!fs.existsSync(filePath)) {
    console.warn(`File not found: ${filePath}`);
    return;
  }
  
  let text = fs.readFileSync(filePath, 'utf-8');
  text = cleanCsvText(text);
  
  const results = Papa.parse(text, { header: true, skipEmptyLines: true });
  
  results.data.forEach(row => {
    const state = row['State/UT']?.trim();
    const district = row['District']?.trim();
    const market = row['Market']?.trim();
    
    if (!state || !district || !market) return;
    
    // Stable ID based on hierarchy
    const idStr = `${state}-${district}-${market}`.toLowerCase().replace(/[^a-z0-9]+/g, '-');
    
    if (!mandiMap.has(idStr)) {
      mandiMap.set(idStr, {
        mandi_id: idStr,
        mandi_name: market,
        district: district,
        state: state,
        latitude: null, // Deliberately null to enforce NO FAKE DATA rule
        longitude: null // Deliberately null
      });
    }
  });
});

const sortedMandis = Array.from(mandiMap.values()).sort((a, b) => a.mandi_name.localeCompare(b.mandi_name));

const outputPath = path.join(dataDir, 'mandi_master.json');
fs.writeFileSync(outputPath, JSON.stringify(sortedMandis, null, 2));

console.log(`Generated mandi_master.json with ${sortedMandis.length} unique mandis.`);
