import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Footer from '../components/Footer';
import {
  MapPin, LogOut, Check, RefreshCw, BarChart2, Navigation, AlertCircle, Info,
  Sparkles, TrendingUp, TrendingDown, Minus, CloudSun, CloudRain, Sun,
  Truck, DollarSign, History, User, ArrowRight, ShieldCheck, Scale, Award
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

import wheatImg from '../assets/illustrations/wheat.jpg';
import riceImg from '../assets/illustrations/rice.jpg';
import tomatoImg from '../assets/illustrations/tomato.jpg';
import cottonImg from '../assets/illustrations/cotton.jpg';

import { fetchCropData, extractMandisFromData, generateChartData, fetchHistoricalPriceApi } from '../services/dataService';
import { getUserLocation } from '../services/locationService';
import { getNearbyMandis } from '../services/mandiService';
import { getMandiPrediction } from '../services/predictionService';
import { getSellingRecommendation } from '../services/recommendationService';
import { getLocalWeather } from '../services/weatherService';
import { getRecentSearches, saveSearchHistory } from '../services/searchService';
import { getCurrentUser, getStoredUser, logout } from '../services/authService';

// ─── CONSTANTS & DATA ─────────────────────────────────────

const CROPS = [
  { id: 'wheat', name: 'Wheat', hindiName: 'गेहूँ', img: wheatImg },
  { id: 'rice', name: 'Rice', hindiName: 'चावल', img: riceImg },
  { id: 'tomato', name: 'Tomato', hindiName: 'टमाटर', img: tomatoImg },
  { id: 'cotton', name: 'Cotton', hindiName: 'कपास', img: cottonImg },
];

const PERIODS = ['1D', '1W', '3W', '1M', '6M', 'YTD'];

// ─── SUB-COMPONENTS ───────────────────────────────────────

const StepTitle = ({ number, title, subtitle }) => (
  <div className="mb-4">
    <div className="flex items-center gap-2.5">
      <span className="w-7 h-7 rounded-lg bg-primary-600 text-white font-bold text-sm flex items-center justify-center shadow-sm">
        {number}
      </span>
      <h2 className="text-lg sm:text-xl font-extrabold text-gray-900 tracking-tight">{title}</h2>
    </div>
    {subtitle && <p className="text-xs sm:text-sm text-gray-500 mt-1 ml-9">{subtitle}</p>}
  </div>
);

// ─── MAIN COMPONENT ───────────────────────────────────────

const FarmerDashboard = () => {
  const navigate = useNavigate();
  const forecastRef = useRef(null);
  const recommendationRef = useRef(null);

  // User Profile State
  const [currentUser, setCurrentUser] = useState(null);

  // Crop & Data State
  const [selectedCrop, setSelectedCrop] = useState(null);
  const [isLoadingData, setIsLoadingData] = useState(false);
  const [dataError, setDataError] = useState('');
  const [parsedRawData, setParsedRawData] = useState([]);
  const [parsedMandis, setParsedMandis] = useState([]);

  // Quantity State (Default: 1000 kg = 10 Quintals)
  const [quantityKg, setQuantityKg] = useState(1000);
  const quintals = (parseFloat(quantityKg) || 0) / 100;

  // Middleman State
  const [hasMiddleman, setHasMiddleman] = useState(false);
  const [middlemanPrice, setMiddlemanPrice] = useState('');
  const [middlemanCommission, setMiddlemanCommission] = useState('2'); // percent
  const [middlemanOther, setMiddlemanOther] = useState('0'); // rupees

  // Chart State
  const [chartData, setChartData] = useState([]);
  const [chartPeriod, setChartPeriod] = useState('YTD');

  // Location State
  const [isLocating, setIsLocating] = useState(false);
  const [location, setLocation] = useState(null);
  const [locationError, setLocationError] = useState('');

  // Weather State
  const [weather, setWeather] = useState(null);
  const [isLoadingWeather, setIsLoadingWeather] = useState(false);

  // Nearby Mandis Search State
  const [isSearchingMandis, setIsSearchingMandis] = useState(false);
  const [nearbyMandisResponse, setNearbyMandisResponse] = useState(null);
  const [sortBy, setSortBy] = useState('net_value'); // 'net_value' | 'nearest' | 'highest_price'

  // Prediction State
  const [predictionState, setPredictionState] = useState({
    status: 'idle', // 'idle' | 'loading' | 'success' | 'error'
    errorMsg: '',
    data: null,
    targetMandi: null
  });

  // Recommendation State
  const [recommendation, setRecommendation] = useState(null);
  const [isLoadingRecommendation, setIsLoadingRecommendation] = useState(false);

  // Recent Searches State
  const [recentSearches, setRecentSearches] = useState([]);

  // 1. Initialize user and recent searches on mount
  useEffect(() => {
    const user = getStoredUser();
    if (user) {
      setCurrentUser(user);
      if (user.latitude && user.longitude) {
        setLocation({
          latitude: user.latitude,
          longitude: user.longitude,
          address: user.address || `${user.district || ''}, ${user.state || ''}`.trim()
        });
      }
    }
    getCurrentUser().then(fresh => {
      if (fresh) {
        setCurrentUser(fresh);
        if (fresh.latitude && fresh.longitude && !user) {
          setLocation({
            latitude: fresh.latitude,
            longitude: fresh.longitude,
            address: fresh.address || `${fresh.district || ''}, ${fresh.state || ''}`.trim()
          });
        }
      }
    });
    loadRecentSearches();
  }, []);

  const loadRecentSearches = async () => {
    try {
      const searches = await getRecentSearches();
      setRecentSearches(searches || []);
    } catch (err) {
      console.warn('Could not load recent searches', err);
    }
  };

  // 2. Fetch Live Weather whenever Location changes
  useEffect(() => {
    if (location?.latitude && location?.longitude) {
      setIsLoadingWeather(true);
      getLocalWeather(location.latitude, location.longitude, location.address || 'Your Farm')
        .then(data => setWeather(data))
        .catch(err => console.warn('Weather fetch error', err))
        .finally(() => setIsLoadingWeather(false));
    }
  }, [location?.latitude, location?.longitude]);

  // 3. Handle Crop Selection & Data Loading
  const handleSelectCrop = async (crop) => {
    setSelectedCrop(crop);
    setIsLoadingData(true);
    setDataError('');
    setNearbyMandisResponse(null);
    setPredictionState({ status: 'idle', errorMsg: '', data: null, targetMandi: null });
    setRecommendation(null);

    try {
      // Try fetching historical price via API first
      const apiHistory = await fetchHistoricalPriceApi(crop.id, chartPeriod);
      if (apiHistory && apiHistory.length > 0) {
        setChartData(apiHistory);
      }

      // Load client CSV for fallback and mandi extraction
      const data = await fetchCropData(crop.id);
      if (data.length > 0) {
        setParsedRawData(data);
        const mandis = extractMandisFromData(data);
        setParsedMandis(mandis);
        if (!apiHistory || apiHistory.length === 0) {
          const newChartData = generateChartData(data, chartPeriod);
          setChartData(newChartData);
        }
      }
    } catch (err) {
      setDataError(err.message || 'Error loading crop data.');
    } finally {
      setIsLoadingData(false);
    }
  };

  // 4. Handle Chart Period Change
  useEffect(() => {
    if (selectedCrop) {
      fetchHistoricalPriceApi(selectedCrop.id, chartPeriod).then(apiHistory => {
        if (apiHistory && apiHistory.length > 0) {
          setChartData(apiHistory);
        } else if (parsedRawData.length > 0) {
          const newChartData = generateChartData(parsedRawData, chartPeriod);
          setChartData(newChartData);
        }
      });
    }
  }, [chartPeriod, selectedCrop]);

  // 5. Handle Location Detection
  const handleGetLocation = async () => {
    setIsLocating(true);
    setLocationError('');
    try {
      const coords = await getUserLocation();
      setLocation(coords);
    } catch (err) {
      setLocationError(err || 'Failed to detect location');
    } finally {
      setIsLocating(false);
    }
  };

  // 6. Handle 500 KM Mandi Search & Economic Calculation
  const handleSearchNearbyMandis = async () => {
    if (!selectedCrop || !location) return;

    setIsSearchingMandis(true);
    setPredictionState({ status: 'idle', errorMsg: '', data: null, targetMandi: null });
    setRecommendation(null);

    try {
      const response = await getNearbyMandis({
        crop: selectedCrop.id,
        latitude: location.latitude,
        longitude: location.longitude,
        radiusKm: 500,
        parsedData: parsedMandis
      });
      setNearbyMandisResponse(response);

      // Trigger automatic comprehensive recommendation calculation
      await triggerRecommendation(selectedCrop.id, response);

      // Persist search to MySQL
      saveSearchHistory({
        crop: selectedCrop.id,
        quantity_kg: parseFloat(quantityKg) || 1000,
        latitude: location.latitude,
        longitude: location.longitude,
        has_middleman: hasMiddleman,
        middleman_price: hasMiddleman ? parseFloat(middlemanPrice) || null : null,
        middleman_commission: hasMiddleman ? parseFloat(middlemanCommission) || null : null,
        middleman_other: hasMiddleman ? parseFloat(middlemanOther) || null : null,
        radius_km: 500
      }).then(() => loadRecentSearches());

    } catch (err) {
      console.error('Mandi search error:', err);
    } finally {
      setIsSearchingMandis(false);
    }
  };

  // 7. Trigger Recommendation API
  const triggerRecommendation = async (cropId, mandisResp) => {
    if (!location) return;
    setIsLoadingRecommendation(true);
    try {
      const payload = {
        crop: cropId,
        quantity_kg: parseFloat(quantityKg) || 1000,
        latitude: location.latitude,
        longitude: location.longitude,
        has_middleman: hasMiddleman,
        middleman_price: hasMiddleman && middlemanPrice ? parseFloat(middlemanPrice) : null,
        middleman_commission: hasMiddleman && middlemanCommission ? parseFloat(middlemanCommission) : null,
        middleman_other: hasMiddleman && middlemanOther ? parseFloat(middlemanOther) : null,
        radius_km: 500
      };
      const rec = await getSellingRecommendation(payload);
      setRecommendation(rec);
    } catch (err) {
      console.warn('Recommendation calculation failed:', err);
    } finally {
      setIsLoadingRecommendation(false);
    }
  };

  // 8. Handle Forecast Request for a Mandi
  const handleRequestForecast = async (mandi) => {
    setPredictionState({
      status: 'loading',
      errorMsg: '',
      data: null,
      targetMandi: mandi
    });

    setTimeout(() => {
      forecastRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);

    try {
      const prediction = await getMandiPrediction(selectedCrop.id, mandi.mandi_id, 'Other', 'FAQ');
      setPredictionState({
        status: 'success',
        errorMsg: '',
        data: prediction,
        targetMandi: mandi
      });
    } catch (err) {
      setPredictionState({
        status: 'error',
        errorMsg: err.message || "Price forecast is temporarily unavailable.",
        data: null,
        targetMandi: mandi
      });
    }
  };

  // 9. Economics calculations for mandi list
  const getEnrichedMandis = () => {
    if (!nearbyMandisResponse?.mandis) return [];
    const q = quintals > 0 ? quintals : 10;

    const enriched = nearbyMandisResponse.mandis.map((m) => {
      const gross = Math.round(m.latest_price * q);
      const transport = Math.round(m.distance_km * 10); // ₹10/km
      const net = Math.round(gross - transport);
      return {
        ...m,
        gross_value: gross,
        transport_cost: transport,
        net_value: net
      };
    });

    // Find highest net value to mark the Best Option
    let maxNet = -Infinity;
    enriched.forEach(m => {
      if (m.net_value > maxNet) maxNet = m.net_value;
    });

    return enriched.map(m => ({
      ...m,
      is_best: m.net_value === maxNet && maxNet > 0
    }));
  };

  // 10. Sorted Mandis
  const getSortedMandis = () => {
    const list = getEnrichedMandis();
    if (sortBy === 'net_value') {
      return list.sort((a, b) => b.net_value - a.net_value);
    } else if (sortBy === 'highest_price') {
      return list.sort((a, b) => b.latest_price - a.latest_price);
    } else if (sortBy === 'nearest') {
      return list.sort((a, b) => a.distance_km - b.distance_km);
    }
    return list;
  };

  // 11. Middleman Net Calculation Preview
  const calculateMiddlemanNet = () => {
    if (!hasMiddleman || !middlemanPrice) return null;
    const price = parseFloat(middlemanPrice) || 0;
    const commPct = parseFloat(middlemanCommission) || 0;
    const other = parseFloat(middlemanOther) || 0;
    const gross = price * (quintals > 0 ? quintals : 10);
    const commAmt = (gross * commPct) / 100;
    const net = Math.max(0, gross - commAmt - other);
    return { gross: Math.round(gross), commission: Math.round(commAmt), other: Math.round(other), net: Math.round(net) };
  };
  const middlemanCalc = calculateMiddlemanNet();

  // 12. Load previous search
  const handleSelectRecentSearch = (item) => {
    const cropObj = CROPS.find(c => c.id === item.crop.toLowerCase());
    if (cropObj) {
      handleSelectCrop(cropObj);
    }
    if (item.quantity_kg) setQuantityKg(item.quantity_kg);
    if (item.latitude && item.longitude) {
      setLocation({ latitude: item.latitude, longitude: item.longitude });
    }
    if (item.has_middleman) {
      setHasMiddleman(true);
      if (item.middleman_price) setMiddlemanPrice(String(item.middleman_price));
      if (item.middleman_commission) setMiddlemanCommission(String(item.middleman_commission));
      if (item.middleman_other) setMiddlemanOther(String(item.middleman_other));
    } else {
      setHasMiddleman(false);
    }
  };

  const handleLogout = () => {
    logout();
    setCurrentUser(null);
    navigate('/');
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F8FAF6] text-gray-800 font-sans antialiased">
      {/* ─── NAVBAR ─── */}
      <nav className="bg-white/95 backdrop-blur-md shadow-xs sticky top-0 z-50 border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16 sm:h-20">
            <Link to="/" className="flex items-center space-x-2.5">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary-600 to-primary-400 flex items-center justify-center text-white text-xl shadow-md">
                🌾
              </div>
              <div>
                <div className="text-xl sm:text-2xl font-black text-gray-900 tracking-tight">
                  Mandi<span className="text-primary-600">Mitra</span>
                </div>
                <div className="text-[10px] sm:text-xs text-gray-400 font-medium leading-none">Smart Farmer Selling Portal</div>
              </div>
            </Link>

            <div className="flex items-center gap-3">
              {currentUser ? (
                <div className="flex items-center gap-3">
                  <div className="hidden sm:flex items-center gap-2 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-full text-xs font-semibold text-emerald-800">
                    <User size={14} className="text-emerald-600" />
                    <span>{currentUser.full_name}</span>
                    {currentUser.district && <span className="text-emerald-600 text-[10px]">({currentUser.district})</span>}
                  </div>
                  <button
                    onClick={handleLogout}
                    className="flex items-center gap-1.5 text-gray-500 hover:text-red-600 px-3 py-1.5 rounded-xl hover:bg-red-50 transition-colors text-xs sm:text-sm font-medium border border-gray-200"
                  >
                    <LogOut size={15} />
                    <span>Logout</span>
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Link
                    to="/login"
                    className="text-xs sm:text-sm font-semibold text-primary-600 hover:text-primary-700 px-3 py-1.5"
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/signup"
                    className="bg-primary-600 hover:bg-primary-700 text-white text-xs sm:text-sm font-semibold px-4 py-1.5 rounded-xl shadow-xs"
                  >
                    Register
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-7">

        {/* ─── HERO & WEATHER BANNER ─── */}
        <div className="relative overflow-hidden bg-gradient-to-br from-emerald-900 via-primary-800 to-emerald-700 rounded-3xl p-6 sm:p-8 text-white shadow-xl">
          <div className="relative z-10 flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
            <div className="max-w-2xl">
              <span className="inline-flex items-center gap-1.5 bg-emerald-700/50 border border-emerald-500/40 text-emerald-200 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider mb-2">
                <ShieldCheck size={14} /> AI Decision Support Engine
              </span>
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black tracking-tight text-white mb-2">
                {currentUser ? `Welcome, ${currentUser.full_name.split(' ')[0]}!` : 'Welcome, Farmer!'} 🌾
              </h1>
              <p className="text-emerald-100 text-xs sm:text-sm leading-relaxed max-w-xl">
                Compare real Mandi prices within 500 KM with ₹10/km transport deduction, evaluate middleman offers, and inspect ML price forecasts to choose the most profitable selling strategy.
              </p>
            </div>

            {/* LIVE WEATHER WIDGET */}
            {weather && (() => {
              const rawTemp = weather.temperature ?? weather.temperature_c ?? 28;
              const temp = !isNaN(Number(rawTemp)) ? Math.round(Number(rawTemp)) : 28;
              const rawPrecip = weather.precipitation_probability ?? weather.precipitation_prob ?? 0;
              const precipProb = !isNaN(Number(rawPrecip)) ? Math.round(Number(rawPrecip)) : 0;
              const condition = weather.condition || 'Fair';
              const advisory = weather.advisory || weather.alert || 'Favorable conditions for market transport.';
              const wCode = weather.weather_code ?? 0;

              return (
                <div className="w-full lg:w-auto bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-4 sm:p-5 flex items-center gap-4 text-white shadow-lg">
                  <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center text-amber-300">
                    {wCode <= 2 ? <Sun size={28} /> : wCode < 60 ? <CloudSun size={28} /> : <CloudRain size={28} />}
                  </div>
                  <div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-2xl font-black">{temp}°C</span>
                      <span className="text-xs text-emerald-200 capitalize font-medium">{condition}</span>
                    </div>
                    <div className="text-[11px] text-emerald-100 mt-0.5">
                      Rain Risk: <span className="font-bold">{precipProb}%</span> • {advisory}
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        </div>

        {/* ─── RECENT SEARCHES QUICK-BAR ─── */}
        {recentSearches.length > 0 && (
          <div className="bg-white rounded-2xl p-4 shadow-xs border border-gray-100 flex items-center gap-3 overflow-x-auto">
            <div className="flex items-center gap-1.5 text-xs font-bold text-gray-500 whitespace-nowrap">
              <History size={15} /> Recent:
            </div>
            <div className="flex gap-2">
              {recentSearches.slice(0, 5).map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelectRecentSearch(item)}
                  className="flex items-center gap-2 bg-gray-50 hover:bg-emerald-50 hover:border-emerald-300 border border-gray-200 px-3 py-1.5 rounded-xl text-xs font-semibold text-gray-700 hover:text-emerald-800 transition-all whitespace-nowrap"
                >
                  <span className="capitalize">{item.crop}</span>
                  <span className="text-gray-400">({item.quantity_kg} kg)</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ─── STEP 1: CROP SELECTION ─── */}
        <section className="bg-white rounded-3xl p-5 sm:p-7 shadow-xs border border-gray-100">
          <StepTitle
            number="1"
            title="Choose Your Harvest Crop"
            subtitle="Select one of the 4 supported crops to load Agmarknet market data"
          />

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mt-4">
            {CROPS.map((crop) => {
              const isSelected = selectedCrop?.id === crop.id;
              return (
                <button
                  key={crop.id}
                  onClick={() => handleSelectCrop(crop)}
                  disabled={isLoadingData}
                  className={`group relative flex flex-col items-center text-center p-3 sm:p-4 rounded-2xl border-2 transition-all duration-200 overflow-hidden ${
                    isSelected
                      ? 'border-primary-600 bg-emerald-50/60 shadow-md ring-2 ring-primary-500/20'
                      : 'border-gray-200 hover:border-primary-300 hover:shadow-xs bg-white'
                  } ${isLoadingData ? 'opacity-70 cursor-not-allowed' : ''}`}
                >
                  {isSelected && (
                    <div className="absolute top-2.5 right-2.5 w-6 h-6 bg-primary-600 rounded-full flex items-center justify-center text-white shadow">
                      <Check size={14} strokeWidth={3} />
                    </div>
                  )}
                  <div className="w-full aspect-square max-w-[130px] rounded-xl overflow-hidden mb-3 bg-gray-100 shadow-inner">
                    <img
                      src={crop.img}
                      alt={crop.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  </div>
                  <div className="w-full">
                    <h3 className="font-bold text-gray-900 text-base sm:text-lg leading-tight">
                      {crop.name}
                    </h3>
                    <p className="text-xs text-gray-400 font-medium">{crop.hindiName}</p>
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {/* LOADING & ERRORS */}
        {isLoadingData && (
          <div className="flex items-center justify-center p-8 text-primary-600 font-bold gap-3">
            <RefreshCw className="animate-spin" size={24} />
            Loading {selectedCrop?.name} market data...
          </div>
        )}

        {dataError && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-5 py-4 rounded-2xl flex items-center gap-3">
            <AlertCircle size={20} />
            <span className="font-semibold text-sm">{dataError}</span>
          </div>
        )}

        {/* ─── STEP 2: QUANTITY & MIDDLEMAN OPTION ─── */}
        {selectedCrop && !isLoadingData && (
          <section className="bg-white rounded-3xl p-5 sm:p-7 shadow-xs border border-gray-100">
            <StepTitle
              number="2"
              title="Harvest Quantity & Selling Options"
              subtitle="Enter the weight of your produce and optionally configure middleman offers"
            />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-4">
              {/* QUANTITY INPUT */}
              <div className="bg-gray-50 border border-gray-200 rounded-2xl p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-2 text-gray-700 font-bold text-sm">
                    <Scale size={18} className="text-primary-600" />
                    <span>Total Produce Weight (in Kilograms)</span>
                  </div>
                  <p className="text-xs text-gray-500 mb-4">
                    Enter the amount in KG. Our system automatically converts to Quintals for mandi comparison (1 Quintal = 100 KG).
                  </p>

                  <div className="relative">
                    <input
                      type="number"
                      min="1"
                      value={quantityKg}
                      onChange={(e) => setQuantityKg(e.target.value)}
                      className="w-full text-2xl font-black text-gray-900 bg-white border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                      placeholder="1000"
                    />
                    <span className="absolute right-4 top-4 text-sm font-bold text-gray-400">KG</span>
                  </div>
                </div>

                <div className="mt-4 bg-emerald-50 border border-emerald-200 rounded-xl p-3.5 flex items-center justify-between">
                  <div className="text-xs text-emerald-800 font-medium">Standard Market Units:</div>
                  <div className="text-base font-extrabold text-emerald-900">
                    {quintals.toFixed(2)} Quintals
                  </div>
                </div>
              </div>

              {/* MIDDLEMAN TOGGLE & FORM */}
              <div className="bg-amber-50/40 border border-amber-200/70 rounded-2xl p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <DollarSign size={18} className="text-amber-600" />
                    <span className="font-bold text-gray-900 text-sm">Local Middleman / Trader Offer?</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setHasMiddleman(!hasMiddleman)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                      hasMiddleman ? 'bg-amber-600' : 'bg-gray-300'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        hasMiddleman ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <p className="text-xs text-gray-500 mb-4">
                  {hasMiddleman
                    ? "Enter middleman's offered rate to see if travelling to a mandi yields higher net profit."
                    : "Toggle ON if a local trader/middleman offered to buy at your doorstep without transport."}
                </p>

                {hasMiddleman ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div>
                        <label className="text-[11px] font-bold text-gray-600 block mb-1">Price (₹ / Quintal)</label>
                        <input
                          type="number"
                          placeholder="e.g. 2300"
                          value={middlemanPrice}
                          onChange={(e) => setMiddlemanPrice(e.target.value)}
                          className="w-full text-sm font-bold bg-white border border-gray-300 rounded-lg p-2.5 focus:ring-1 focus:ring-amber-500"
                        />
                      </div>
                      <div>
                        <label className="text-[11px] font-bold text-gray-600 block mb-1">Commission (%)</label>
                        <input
                          type="number"
                          placeholder="e.g. 2"
                          value={middlemanCommission}
                          onChange={(e) => setMiddlemanCommission(e.target.value)}
                          className="w-full text-sm font-bold bg-white border border-gray-300 rounded-lg p-2.5 focus:ring-1 focus:ring-amber-500"
                        />
                      </div>
                      <div>
                        <label className="text-[11px] font-bold text-gray-600 block mb-1">Other Deductions (₹)</label>
                        <input
                          type="number"
                          placeholder="e.g. 100"
                          value={middlemanOther}
                          onChange={(e) => setMiddlemanOther(e.target.value)}
                          className="w-full text-sm font-bold bg-white border border-gray-300 rounded-lg p-2.5 focus:ring-1 focus:ring-amber-500"
                        />
                      </div>
                    </div>

                    {middlemanCalc && middlemanCalc.net > 0 && (
                      <div className="bg-white border border-amber-200 rounded-xl p-3 flex justify-between items-center text-xs">
                        <span className="text-gray-600 font-medium">Middleman Net Payout:</span>
                        <span className="text-base font-black text-amber-700">₹{middlemanCalc.net.toLocaleString('en-IN')}</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="bg-white/60 border border-dashed border-gray-300 rounded-xl p-4 text-center text-xs text-gray-400">
                    No middleman configured. You will compare Mandi net values directly.
                  </div>
                )}
              </div>
            </div>
          </section>
        )}

        {/* ─── STEP 3: PRICE TREND CHART ─── */}
        {selectedCrop && chartData.length > 0 && !isLoadingData && (
          <section className="bg-white rounded-3xl p-5 sm:p-7 shadow-xs border border-gray-100">
            <div className="bg-gray-50/50 border border-gray-200 rounded-2xl p-4 sm:p-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                <div className="flex items-center gap-2">
                  <BarChart2 className="text-primary-600" size={24} />
                  <div>
                    <h3 className="font-bold text-gray-900 text-lg">{selectedCrop.name} Historical Price Trend</h3>
                    <p className="text-xs text-gray-400">Agmarknet weighted average modal prices (₹ / Quintal)</p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-1.5 bg-white p-1 rounded-xl border border-gray-200 shadow-2xs">
                  {PERIODS.map(period => (
                    <button
                      key={period}
                      onClick={() => setChartPeriod(period)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                        chartPeriod === period
                          ? 'bg-primary-600 text-white shadow-xs'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      {period}
                    </button>
                  ))}
                </div>
              </div>

              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                    <XAxis
                      dataKey="date"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#9ca3af', fontSize: 12 }}
                      minTickGap={30}
                    />
                    <YAxis
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#9ca3af', fontSize: 12 }}
                      tickFormatter={(val) => `₹${val}`}
                      domain={['auto', 'auto']}
                    />
                    <Tooltip
                      contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                      formatter={(value) => [`₹${value}`, 'Modal Price / Quintal']}
                      labelStyle={{ fontWeight: 'bold', color: '#374151', marginBottom: '4px' }}
                    />
                    <Line
                      type="monotone"
                      dataKey="price"
                      stroke="#16a34a"
                      strokeWidth={3}
                      dot={false}
                      activeDot={{ r: 6, fill: '#16a34a', stroke: '#fff', strokeWidth: 2 }}
                      name="Agmarknet Price"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>
        )}

        {/* ─── STEP 4: GEOGRAPHIC LOCATION & 500 KM SEARCH ─── */}
        {selectedCrop && !isLoadingData && (
          <section className="bg-white rounded-3xl p-5 sm:p-7 shadow-xs border border-gray-100">
            <StepTitle
              number="3"
              title="📍 Farm Location & 500 KM Mandi Discovery"
              subtitle="Find all registered Agmarknet mandis within 500 KM with real distance calculation"
            />

            <div className="flex flex-col sm:flex-row gap-6 mt-4">
              <div className="flex-1 bg-emerald-50/50 border border-emerald-100 rounded-2xl p-5 sm:p-6 flex flex-col items-start justify-center">
                <button
                  onClick={handleGetLocation}
                  disabled={isLocating}
                  className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-6 py-3.5 rounded-xl shadow-md transition-all active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed text-sm"
                >
                  {isLocating ? (
                    <><RefreshCw size={18} className="animate-spin" /> Detecting Location...</>
                  ) : (
                    <><Navigation size={18} /> Detect My Location</>
                  )}
                </button>

                {locationError && (
                  <p className="mt-3 text-xs font-semibold text-red-600 flex items-center gap-1.5">
                    <AlertCircle size={15} /> {locationError}
                  </p>
                )}

                {location && (
                  <div className="mt-4 bg-white px-4 py-3 rounded-xl border border-emerald-200 shadow-xs w-full">
                    <div className="text-xs font-bold text-emerald-700 flex items-center gap-1.5">
                      <Check size={16} /> Location Set: {location.address || 'GPS Coordinates'}
                    </div>
                    <div className="mt-1 text-[11px] text-gray-500 font-mono">
                      Lat: {location.latitude.toFixed(4)}, Lng: {location.longitude.toFixed(4)}
                    </div>
                  </div>
                )}
              </div>

              <div className="flex-1 flex flex-col justify-center">
                <button
                  onClick={handleSearchNearbyMandis}
                  disabled={!location || isSearchingMandis}
                  className={`w-full font-bold px-6 py-4 rounded-xl shadow-md transition-all flex items-center justify-center gap-2 text-base sm:text-lg ${
                    !location
                      ? 'bg-gray-200 text-gray-400 cursor-not-allowed shadow-none'
                      : isSearchingMandis
                      ? 'bg-gray-300 text-gray-600'
                      : 'bg-primary-600 hover:bg-primary-700 text-white shadow-emerald-600/20 active:scale-98'
                  }`}
                >
                  {isSearchingMandis ? (
                    <><RefreshCw size={20} className="animate-spin" /> Analyzing 500 KM Mandis & Forecast...</>
                  ) : (
                    <><Truck size={20} /> Find Mandis & Get Recommendation</>
                  )}
                </button>
                <div className="mt-2 text-center text-xs text-gray-400">
                  Transits calculated at flat ₹10 / km one-way. Best option dynamically highlighted.
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ─── MANDI RESULTS WITHIN 500 KM ─── */}
        {nearbyMandisResponse && (
          <section className="bg-white rounded-3xl p-5 sm:p-7 shadow-xs border border-gray-100">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
              <StepTitle
                number="4"
                title={`Mandis Within 500 KM (${nearbyMandisResponse.mandis.length} found)`}
                subtitle={`Showing verified mandis for ${selectedCrop.name} with transport deductions for ${quintals.toFixed(2)} quintals`}
              />

              <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl p-1">
                <span className="text-xs font-bold text-gray-500 pl-2">Sort:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="bg-transparent text-xs font-bold text-gray-800 focus:outline-none border-none py-1 pr-6 cursor-pointer"
                >
                  <option value="net_value">⭐ Highest Net Value ▼</option>
                  <option value="highest_price">Highest Mandi Price ▼</option>
                  <option value="nearest">Nearest Distance ▼</option>
                </select>
              </div>
            </div>

            {nearbyMandisResponse.mandis.length === 0 ? (
              <div className="bg-gray-50 border border-gray-200 p-8 rounded-2xl flex flex-col items-center justify-center text-center">
                <MapPin className="text-gray-400 mb-3" size={32} />
                <h4 className="text-lg font-bold text-gray-800 mb-2">No Active Mandis Within 500 KM</h4>
                <p className="text-sm text-gray-500 max-w-lg">
                  No mandis trading {selectedCrop.name} were located within 500 km of your current coordinates. Try selecting another crop or testing with a different location.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {getSortedMandis().map((mandi, idx) => (
                  <div
                    key={idx}
                    className={`relative rounded-2xl p-5 transition-all duration-200 bg-white shadow-xs flex flex-col justify-between ${
                      mandi.is_best
                        ? 'border-2 border-amber-400 ring-2 ring-amber-400/20 bg-gradient-to-b from-amber-50/20 to-white'
                        : 'border border-gray-200 hover:border-emerald-300 hover:shadow-sm'
                    }`}
                  >
                    {/* BEST OPTION BADGE */}
                    {mandi.is_best && (
                      <div className="absolute -top-3 left-4 bg-gradient-to-r from-amber-500 to-amber-600 text-white text-[11px] font-black px-3 py-0.5 rounded-full shadow-md flex items-center gap-1 uppercase tracking-wider">
                        <Award size={13} /> ⭐ BEST OPTION
                      </div>
                    )}

                    <div>
                      <div className="flex justify-between items-start gap-2">
                        <div>
                          <h4 className="font-bold text-gray-900 text-base sm:text-lg leading-tight mb-0.5">
                            {mandi.mandi_name}
                          </h4>
                          <div className="text-xs text-gray-500">{mandi.district}, {mandi.state}</div>
                        </div>
                        <div className="flex items-center gap-1 text-emerald-700 font-bold text-xs bg-emerald-50 px-2 py-1 rounded-lg shrink-0">
                          <MapPin size={13} /> {Math.round(mandi.distance_km)} km
                        </div>
                      </div>

                      {/* FINANCIAL BREAKDOWN */}
                      <div className="mt-4 bg-gray-50 rounded-xl p-3 space-y-1.5 text-xs">
                        <div className="flex justify-between text-gray-600">
                          <span>Mandi Price:</span>
                          <span className="font-bold text-gray-900">₹{mandi.latest_price} / Qtl</span>
                        </div>
                        <div className="flex justify-between text-gray-600">
                          <span>Gross Value ({quintals.toFixed(1)} Q):</span>
                          <span className="font-semibold text-gray-800">₹{mandi.gross_value.toLocaleString('en-IN')}</span>
                        </div>
                        <div className="flex justify-between text-red-600">
                          <span>Transport ({Math.round(mandi.distance_km)} km × ₹10):</span>
                          <span className="font-semibold">-₹{mandi.transport_cost.toLocaleString('en-IN')}</span>
                        </div>
                        <div className="border-t border-gray-200 pt-1.5 flex justify-between items-baseline font-black">
                          <span className="text-gray-800">Net Mandi Value:</span>
                          <span className="text-base text-emerald-700">₹{mandi.net_value.toLocaleString('en-IN')}</span>
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-gray-100 flex gap-2">
                      <button
                        onClick={() => handleRequestForecast(mandi)}
                        className={`w-full py-2 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-colors border ${
                          predictionState.targetMandi?.mandi_id === mandi.mandi_id
                            ? 'bg-amber-100 text-amber-800 border-amber-300'
                            : 'bg-white text-gray-700 border-gray-200 hover:bg-emerald-50 hover:border-emerald-300'
                        }`}
                      >
                        <Sparkles size={14} className={predictionState.targetMandi?.mandi_id === mandi.mandi_id ? 'text-amber-600' : 'text-primary-600'} />
                        <span>AI Price Forecast</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* ─── STEP 5: FINAL SELLING RECOMMENDATION ENGINE CARD ─── */}
        {recommendation && (
          <section ref={recommendationRef} className="bg-white rounded-3xl p-6 sm:p-8 shadow-md border border-emerald-100">
            <StepTitle
              number="5"
              title="🎯 MandiMitra Recommendation Engine"
              subtitle="Algorithmic selling decision comparing Mandi Net, Middleman Offer & ML Forecast"
            />

            <div className={`mt-4 rounded-3xl p-6 sm:p-8 border-2 ${
              recommendation.recommendation === 'SELL TODAY'
                ? 'bg-emerald-50/50 border-emerald-500 ring-2 ring-emerald-500/10'
                : 'bg-amber-50/50 border-amber-500 ring-2 ring-amber-500/10'
            }`}>
              <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
                <div>
                  <div className="flex items-center gap-3">
                    <span className={`px-4 py-1.5 rounded-full text-sm font-black tracking-wide uppercase shadow-xs ${
                      recommendation.recommendation === 'SELL TODAY'
                        ? 'bg-emerald-600 text-white'
                        : 'bg-amber-600 text-white'
                    }`}>
                      {recommendation.recommendation}
                    </span>
                    <span className="text-xs text-gray-500 font-semibold">
                      Produce: {recommendation.quantity_kg} KG ({recommendation.quantity_quintals} Quintals)
                    </span>
                  </div>

                  <h3 className="text-2xl sm:text-3xl font-black text-gray-900 mt-3 leading-tight">
                    {recommendation.reason}
                  </h3>

                  {recommendation.weather_advisory && (
                    <div className="mt-3 flex items-center gap-2 text-xs font-semibold text-gray-700 bg-white/70 px-3 py-2 rounded-xl border border-gray-200/60 w-fit">
                      <CloudSun size={16} className="text-amber-600" />
                      <span>Weather factor: {recommendation.weather_advisory}</span>
                    </div>
                  )}
                </div>

                {/* COMPARISON METRICS PILL */}
                <div className="w-full lg:w-auto bg-white rounded-2xl p-5 border border-gray-200 shadow-xs space-y-3 min-w-[280px]">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-gray-500">Current Best Net:</span>
                    <span className="font-extrabold text-gray-900 text-sm">
                      ₹{Math.round(recommendation.current_net_value).toLocaleString('en-IN')}
                    </span>
                  </div>

                  <div className="flex justify-between items-center text-xs">
                    <span className="text-gray-500">Predicted Future Net:</span>
                    <span className="font-extrabold text-primary-700 text-sm">
                      ₹{Math.round(recommendation.expected_future_net_value).toLocaleString('en-IN')}
                    </span>
                  </div>

                  <div className="border-t border-gray-100 pt-2 flex justify-between items-center text-xs">
                    <span className="text-gray-500">Expected Difference:</span>
                    <span className={`font-black text-sm ${recommendation.potential_difference >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                      {recommendation.potential_difference >= 0 ? '+' : ''}₹{Math.round(recommendation.potential_difference).toLocaleString('en-IN')}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ─── STEP 6: ML PRICE FORECAST DETAILS ─── */}
        {predictionState.status !== 'idle' && predictionState.targetMandi && (
          <section ref={forecastRef} className="bg-white rounded-3xl p-5 sm:p-7 shadow-xs border border-amber-200">
            <StepTitle
              number="6"
              title="📈 2-3 Day ML Price Forecast"
              subtitle={`Machine learning model inference for ${predictionState.targetMandi.mandi_name} (${selectedCrop.name})`}
            />

            {predictionState.status === 'loading' && (
              <div className="bg-amber-50 border border-amber-100 rounded-2xl p-8 flex flex-col items-center justify-center">
                <RefreshCw size={32} className="animate-spin text-amber-500 mb-4" />
                <h4 className="font-bold text-amber-900 text-lg">Running Gradient Boosting Regressor...</h4>
                <p className="text-amber-700 text-xs mt-2 max-w-md text-center">
                  Calculating 40 temporal features, 30-day price lags and rolling aggregations for {predictionState.targetMandi.mandi_name}.
                </p>
              </div>
            )}

            {predictionState.status === 'error' && (
              <div className="bg-red-50 border border-red-200 p-6 rounded-2xl flex flex-col items-center justify-center text-center">
                <AlertCircle className="text-red-500 mb-3" size={32} />
                <h4 className="text-lg font-bold text-red-800 mb-2">ML Inference Notice</h4>
                <p className="text-xs text-red-700 max-w-lg">
                  {predictionState.errorMsg}
                </p>
              </div>
            )}

            {predictionState.status === 'success' && predictionState.data && (
              <div className="bg-amber-50/60 border border-amber-200 rounded-2xl p-6">
                <div className="flex flex-col sm:flex-row gap-6">
                  <div className="flex-1">
                    <div className="text-xs uppercase font-bold text-amber-800 mb-1">Current Modal Price</div>
                    <div className="text-3xl font-black text-amber-950 mb-4">
                      ₹{predictionState.data.current_price} <span className="text-sm font-semibold text-amber-800">/ Quintal</span>
                    </div>

                    <div className="text-xs uppercase font-bold text-amber-800 mb-3">Expected 3-Day Prices</div>
                    <div className="grid grid-cols-3 gap-3">
                      <div className="bg-white p-3.5 rounded-xl border border-amber-200 shadow-2xs text-center">
                        <div className="text-[10px] uppercase font-bold text-gray-400 mb-1">Tomorrow</div>
                        <div className="text-lg font-extrabold text-gray-900">₹{predictionState.data.forecast.day_1}</div>
                      </div>
                      <div className="bg-white p-3.5 rounded-xl border border-amber-200 shadow-2xs text-center">
                        <div className="text-[10px] uppercase font-bold text-gray-400 mb-1">Day 2</div>
                        <div className="text-lg font-extrabold text-gray-900">₹{predictionState.data.forecast.day_2}</div>
                      </div>
                      <div className="bg-white p-3.5 rounded-xl border border-amber-200 shadow-2xs text-center">
                        <div className="text-[10px] uppercase font-bold text-gray-400 mb-1">Day 3</div>
                        <div className="text-lg font-extrabold text-gray-900">₹{predictionState.data.forecast.day_3}</div>
                      </div>
                    </div>
                  </div>

                  <div className="w-full sm:w-48 bg-white rounded-xl border border-amber-200 shadow-2xs p-4 flex flex-col justify-center items-center">
                    <div className="text-xs uppercase font-bold text-gray-400 mb-2">Price Trend</div>
                    {predictionState.data.trend === 'rising' && <TrendingUp size={44} className="text-emerald-600 mb-2" />}
                    {predictionState.data.trend === 'falling' && <TrendingDown size={44} className="text-red-500 mb-2" />}
                    {predictionState.data.trend === 'stable' && <Minus size={44} className="text-blue-500 mb-2" />}
                    <div className="font-black text-lg text-gray-900 capitalize">{predictionState.data.trend}</div>
                  </div>
                </div>
              </div>
            )}
          </section>
        )}

      </main>

      <Footer />
    </div>
  );
};

export default FarmerDashboard;
