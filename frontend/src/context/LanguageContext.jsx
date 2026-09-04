import React, { createContext, useContext, useState, useEffect } from 'react';

const LanguageContext = createContext();

export const translations = {
  en: {
    // Navigation
    appName: "MandiMitra",
    tagline: "Smart Farmer Selling Portal",
    home: "Home",
    howItWorks: "How It Works",
    aboutUs: "About Us",
    contactUs: "Contact Us",
    signIn: "Sign In",
    signUp: "Sign Up",
    register: "Register",
    dashboard: "Dashboard",
    logout: "Logout",
    exit: "Exit",

    // Hero Banner
    welcomeTitle: "Welcome to MandiMitra 🌾",
    welcomeFarmer: "Welcome, {name}! 🌾",
    aiDecisionEngine: "AI Decision Support Engine",
    heroSubtitle: "Compare real Mandi prices within 500 KM with ₹10/km transport deduction, evaluate middleman offers, and inspect ML price forecasts to choose the most profitable selling strategy.",
    recent: "Recent:",

    // Weather
    rainRisk: "Rain Risk",
    favorableConditions: "Favorable conditions for market transport.",

    // Step 1: Crop Selection
    step1Title: "Choose Your Harvest Crop",
    step1Subtitle: "Select one of the 4 supported crops to load Agmarknet market data",
    wheat: "Wheat",
    rice: "Rice",
    tomato: "Tomato",
    cotton: "Cotton",
    loadingData: "Loading {crop} market data...",

    // Step 2: Quantity & Middleman
    step2Title: "Harvest Quantity & Selling Options",
    step2Subtitle: "Enter the weight of your produce and optionally configure middleman offers",
    produceWeight: "Total Produce Weight (in Kilograms)",
    weightHelp: "Enter the amount in KG. Our system automatically converts to Quintals for mandi comparison (1 Quintal = 100 KG).",
    standardUnits: "Standard Market Units:",
    quintalsLabel: "{q} Quintals",
    middlemanPrompt: "Local Middleman / Trader Offer?",
    middlemanHelpOn: "Enter middleman's offered rate to see if travelling to a mandi yields higher net profit.",
    middlemanHelpOff: "Toggle ON if a local trader/middleman offered to buy at your doorstep without transport.",
    pricePerQuintal: "Price (₹ / Quintal)",
    commissionPct: "Commission (%)",
    otherDeductions: "Other Deductions (₹)",
    middlemanNet: "Middleman Net Payout:",
    noMiddlemanConfigured: "No middleman configured. You will compare Mandi net values directly.",

    // Step 3: Historical Trend Chart
    priceTrendTitle: "{crop} Historical Price Trend",
    priceTrendSubtitle: "Agmarknet weighted average modal prices (₹ / Quintal)",
    modalPricePerQtl: "Modal Price / Quintal",

    // Step 4: Location & Mandis
    step4Title: "📍 Farm Location & 500 KM Mandi Discovery",
    step4Subtitle: "Find all registered Agmarknet mandis within 500 KM with real distance calculation",
    detectLocation: "Detect My Location",
    detectingLocation: "Detecting Location...",
    locationSet: "Location Set:",
    findMandisBtn: "Find Mandis & Get Recommendation",
    findingMandisBtn: "Analyzing 500 KM Mandis & Forecast...",
    transportRuleNotice: "Transits calculated at flat ₹10 / km one-way. Best option dynamically highlighted.",

    // Step 5: Mandi Results
    mandisFoundTitle: "Mandis Within 500 KM ({count} found)",
    mandisFoundSubtitle: "Showing verified mandis for {crop} with transport deductions for {q} quintals",
    sortLabel: "Sort:",
    sortHighestNet: "⭐ Highest Net Value ▼",
    sortHighestPrice: "Highest Mandi Price ▼",
    sortNearest: "Nearest Distance ▼",
    bestOptionBadge: "⭐ BEST OPTION",
    kmAway: "km",
    mandiPriceLabel: "Mandi Price:",
    grossValueLabel: "Gross Value ({q} Q):",
    transportDeductionLabel: "Transport ({km} km × ₹10):",
    netMandiValueLabel: "Net Mandi Value:",
    aiForecastBtn: "AI Price Forecast",
    noMandisFound: "No Active Mandis Within 500 KM",
    noMandisFoundDesc: "No mandis trading {crop} were located within 500 km of your current coordinates.",

    // Step 6: Recommendation Engine
    recommendationTitle: "🎯 MandiMitra Recommendation Engine",
    recommendationSubtitle: "Algorithmic selling decision comparing Mandi Net, Middleman Offer & ML Forecast",
    sellToday: "SELL TODAY",
    holdDays: "HOLD FOR 2–3 DAYS",
    currentBestNet: "Current Best Net:",
    predictedFutureNet: "Predicted Future Net:",
    expectedDiff: "Expected Difference:",
    weatherFactor: "Weather factor:",
    produceLabel: "Produce:",

    // Step 7: ML Forecast Details
    forecastTitle: "📈 2-3 Day ML Price Forecast",
    forecastSubtitle: "Machine learning model inference for {mandi} ({crop})",
    currentModalPrice: "Current Modal Price",
    expected3Day: "Expected 3-Day Prices",
    tomorrow: "Tomorrow",
    day2: "Day 2",
    day3: "In 3 Days",
    trendLabel: "Price Trend",
    trendRising: "Rising",
    trendFalling: "Falling",
    trendStable: "Stable",
    runningRegressor: "Running Gradient Boosting Regressor...",
    calculatingFeatures: "Calculating 40 temporal features, 30-day price lags and rolling aggregations for {mandi}."
  },

  hi: {
    // Navigation
    appName: "मंडीमित्र",
    tagline: "किसानों का स्मार्ट बिक्री पोर्टल",
    home: "होम",
    howItWorks: "यह कैसे काम करता है",
    aboutUs: "हमारे बारे में",
    contactUs: "संपर्क करें",
    signIn: "साइन इन",
    signUp: "पंजीकरण करें",
    register: "पंजीकरण",
    dashboard: "डैशबोर्ड",
    logout: "लॉग आउट",
    exit: "बाहर निकलें",

    // Hero Banner
    welcomeTitle: "मंडीमित्र में आपका स्वागत है 🌾",
    welcomeFarmer: "स्वागत है, {name}! 🌾",
    aiDecisionEngine: "एआई निर्णय सहायता इंजन",
    heroSubtitle: "500 किमी के भीतर वास्तविक मंडी भावों की तुलना करें, ₹10/किमी परिवहन खर्च घटाएं, बिचौलियों के प्रस्तावों का मूल्यांकन करें और सबसे अधिक लाभकारी बिक्री निर्णय लें।",
    recent: "हालिया खोज:",

    // Weather
    rainRisk: "बारिश का जोखिम",
    favorableConditions: "मंडी परिवहन और फसल सुखाने के लिए अनुकूल मौसम।",

    // Step 1: Crop Selection
    step1Title: "अपनी फसल चुनें",
    step1Subtitle: "एगमार्कनेट बाजार भाव देखने के लिए 4 फसलों में से एक का चयन करें",
    wheat: "गेहूँ",
    rice: "चावल",
    tomato: "टमाटर",
    cotton: "कपास",
    loadingData: "{crop} का बाजार भाव लोड हो रहा है...",

    // Step 2: Quantity & Middleman
    step2Title: "फसल की मात्रा और बिक्री विकल्प",
    step2Subtitle: "अपनी उपज का वजन दर्ज करें और आवश्यकतानुसार बिचौलिए के प्रस्ताव की तुलना करें",
    produceWeight: "कुल उपज का वजन (किलोग्राम में)",
    weightHelp: "वजन किलोग्राम (KG) में दर्ज करें। हमारा सिस्टम स्वचालित रूप से इसे क्विंटल में बदल देता है (1 क्विंटल = 100 KG)।",
    standardUnits: "मानक बाजार इकाई:",
    quintalsLabel: "{q} क्विंटल",
    middlemanPrompt: "स्थानीय बिचौलिए / व्यापारी का प्रस्ताव?",
    middlemanHelpOn: "बिचौलिए द्वारा दिया गया भाव दर्ज करें, यह देखने के लिए कि क्या मंडी जाकर बेचना अधिक लाभदायक है।",
    middlemanHelpOff: "यदि किसी स्थानीय व्यापारी ने आपके खेत से ही खरीदने की पेशकश की है, तो इसे चालू करें।",
    pricePerQuintal: "भाव (₹ / क्विंटल)",
    commissionPct: "आढ़त / कमीशन (%)",
    otherDeductions: "अन्य कटौती (₹)",
    middlemanNet: "बिचौलिए से शुद्ध भुगतान:",
    noMiddlemanConfigured: "कोई बिचौलिया नहीं जोड़ा गया। आप सीधे मंडियों के शुद्ध लाभ की तुलना करेंगे।",

    // Step 3: Historical Trend Chart
    priceTrendTitle: "{crop} ऐतिहासिक मूल्य रुझान",
    priceTrendSubtitle: "एगमार्कनेट भारित औसत मॉडल भाव (₹ / क्विंटल)",
    modalPricePerQtl: "मॉडल भाव / क्विंटल",

    // Step 4: Location & Mandis
    step4Title: "📍 खेत का स्थान और 500 किमी मंडी खोज",
    step4Subtitle: "500 किमी के दायरे में वास्तविक दूरी गणना के साथ सभी पंजीकृत मंडियों को खोजें",
    detectLocation: "मेरा स्थान पता करें",
    detectingLocation: "स्थान खोजा जा रहा है...",
    locationSet: "स्थान निर्धारित:",
    findMandisBtn: "मंडियाँ खोजें और सलाह प्राप्त करें",
    findingMandisBtn: "500 किमी मंडियों और पूर्वानुमान का विश्लेषण...",
    transportRuleNotice: "एकतरफा ₹10 / किमी की दर से परिवहन लागत जोड़ी जाती है। सर्वोत्तम विकल्प को हाइलाइट किया गया है।",

    // Step 5: Mandi Results
    mandisFoundTitle: "500 किमी के भीतर मंडियाँ ({count} मिलीं)",
    mandisFoundSubtitle: "{crop} के लिए {q} क्विंटल उपज पर परिवहन कटौती के साथ वास्तविक मंडियाँ",
    sortLabel: "क्रम:",
    sortHighestNet: "⭐ अधिकतम शुद्ध लाभ ▼",
    sortHighestPrice: "अधिकतम मंडी भाव ▼",
    sortNearest: "सबसे निकटतम ▼",
    bestOptionBadge: "⭐ सर्वोत्तम विकल्प",
    kmAway: "किमी",
    mandiPriceLabel: "मंडी भाव:",
    grossValueLabel: "कुल मूल्य ({q} क्विंटल):",
    transportDeductionLabel: "परिवहन ({km} किमी × ₹10):",
    netMandiValueLabel: "शुद्ध मंडी लाभ:",
    aiForecastBtn: "एआई मूल्य पूर्वानुमान",
    noMandisFound: "500 किमी के दायरे में कोई मंडी नहीं मिली",
    noMandisFoundDesc: "आपके वर्तमान स्थान से 500 किमी के दायरे में {crop} का व्यापार करने वाली कोई मंडी नहीं मिली।",

    // Step 6: Recommendation Engine
    recommendationTitle: "🎯 मंडीमित्र निर्णय इंजन",
    recommendationSubtitle: "मंडी शुद्ध लाभ, बिचौलिया प्रस्ताव और एआई पूर्वानुमान पर आधारित सटीक निर्णय",
    sellToday: "आज ही बेचें",
    holdDays: "2–3 दिन रुकें",
    currentBestNet: "वर्तमान सर्वोत्तम लाभ:",
    predictedFutureNet: "अनुमानित भावी लाभ:",
    expectedDiff: "संभावित अंतर:",
    weatherFactor: "मौसम प्रभाव:",
    produceLabel: "उपज:",

    // Step 7: ML Forecast Details
    forecastTitle: "📈 2-3 दिन का एआई मूल्य पूर्वानुमान",
    forecastSubtitle: "{mandi} ({crop}) के लिए मशीन लर्निंग मॉडल पूर्वानुमान",
    currentModalPrice: "वर्तमान मॉडल भाव",
    expected3Day: "आगामी 3 दिनों का अपेक्षित भाव",
    tomorrow: "कल",
    day2: "2 दिन में",
    day3: "3 दिन में",
    trendLabel: "मूल्य रुझान",
    trendRising: "बढ़ता हुआ",
    trendFalling: "घटता हुआ",
    trendStable: "स्थिर",
    runningRegressor: "ग्रेडिएंट बूस्टिंग रिग्रेसर चल रहा है...",
    calculatingFeatures: "{mandi} के लिए 40 समय-आधारित विशेषताओं और 30-दिवसीय भाव का विश्लेषण किया जा रहा है।"
  },

  mr: {
    // Navigation
    appName: "मंडीमित्र",
    tagline: "शेतकऱ्यांचे स्मार्ट विक्री पोर्टल",
    home: "मुख्यपृष्ठ",
    howItWorks: "हे कसे कार्य करते",
    aboutUs: "आमच्याबद्दल",
    contactUs: "संपर्क साधा",
    signIn: "लॉगिन करा",
    signUp: "नोंदणी करा",
    register: "नोंदणी",
    dashboard: "डॅशबोर्ड",
    logout: "बाहेर पडा",
    exit: "बाहेर पडा",

    // Hero Banner
    welcomeTitle: "मंडीमित्र मध्ये आपले स्वागत आहे 🌾",
    welcomeFarmer: "स्वागत आहे, {name}! 🌾",
    aiDecisionEngine: "एआय निर्णय सहाय्य प्रणाली",
    heroSubtitle: "५०० किमी अंतरावरील बाजारभाव तपासा, ₹१०/किमी वाहतूक खर्च वजा करा, स्थानिक दलालाच्या दराची तुलना करा आणि सर्वाधिक नफा मिळवून देणारा अचूक निर्णय घ्या.",
    recent: "अलीकडील शोध:",

    // Weather
    rainRisk: "पावसाची शक्यता",
    favorableConditions: "बाजार वाहतूक आणि पिके सुरक्षित नेण्यासाठी अनुकूल हवामान.",

    // Step 1: Crop Selection
    step1Title: "आपले पीक निवडा",
    step1Subtitle: "अगमार्कनेट बाजारभाव पाहण्यासाठी ४ पिकांपैकी एका पिकाची निवड करा",
    wheat: "गहू",
    rice: "तांदूळ",
    tomato: "टोमॅटो",
    cotton: "कापूस",
    loadingData: "{crop} चे बाजारभाव लोड होत आहेत...",

    // Step 2: Quantity & Middleman
    step2Title: "पिकाचे प्रमाण आणि विक्री पर्याय",
    step2Subtitle: "आपल्या पिकाचे वजन प्रविष्ट करा आणि आवश्यकतेनुसार स्थानिक दलाल दराची तुलना करा",
    produceWeight: "एकूण उत्पादन वजन (किलोमध्ये)",
    weightHelp: "वजन किलोमध्ये टाका. आमची प्रणाली आपोआप क्विंटलमध्ये बदलते (१ क्विंटल = १०० किलो).",
    standardUnits: "प्रमाणित बाजार युनिट:",
    quintalsLabel: "{q} क्विंटल",
    middlemanPrompt: "स्थानिक दलाल / व्यापारी ऑफर?",
    middlemanHelpOn: "स्थानिक व्यापाऱ्याचा दर टाका, जेणेकरून थेट बाजारात माल नेल्यास अधिक नफा होतो का हे स्पष्ट होईल.",
    middlemanHelpOff: "जर स्थानिक व्यापाऱ्याने थेट शेतावर येऊन खरेदी करण्याची तयारी दर्शवली असेल, तर हे सुरू करा.",
    pricePerQuintal: "भाव (₹ / क्विंटल)",
    commissionPct: "कमिशन / अडत (%)",
    otherDeductions: "इतर कपात (₹)",
    middlemanNet: "दलालाकडून मिळणारी निव्वळ रक्कम:",
    noMiddlemanConfigured: "कोणताही दलाल जोडलेला नाही. थेट बाजारभावांच्या निव्वळ नफ्याची तुलना होईल.",

    // Step 3: Historical Trend Chart
    priceTrendTitle: "{crop} ऐतिहासिक बाजारभाव कल",
    priceTrendSubtitle: "अगमार्कनेट सरासरी भाव (₹ / क्विंटल)",
    modalPricePerQtl: "सरासरी भाव / क्विंटल",

    // Step 4: Location & Mandis
    step4Title: "📍 शेताचे स्थान आणि ५०० किमी बाजार शोध",
    step4Subtitle: "५०० किमी परिसरातील सर्व अधिकृत कृषी उत्पन्न बाजार समित्या अचूक अंतरासह शोधा",
    detectLocation: "माझे स्थान शोधा",
    detectingLocation: "स्थान शोधत आहे...",
    locationSet: "स्थान निश्चित झाले:",
    findMandisBtn: "बाजार शोधा आणि सल्ला मिळवा",
    findingMandisBtn: "५०० किमी बाजार व भावी किमतींचे विश्लेषण सुरू आहे...",
    transportRuleNotice: "एकेरी ₹१० / किमी वाहतूक खर्च वजा केला जातो. सर्वोत्तम पर्याय ठळकपणे दर्शविला आहे.",

    // Step 5: Mandi Results
    mandisFoundTitle: "५०० किमी अंतरावरील बाजार समित्या ({count} आढळल्या)",
    mandisFoundSubtitle: "{crop} साठी {q} क्विंटल उत्पादनावर वाहतूक खर्च वजा करून निव्वळ परतावा",
    sortLabel: "क्रमवारी:",
    sortHighestNet: "⭐ सर्वाधिक निव्वळ नफा ▼",
    sortHighestPrice: "सर्वाधिक बाजारभाव ▼",
    sortNearest: "सर्वात जवळचे बाजार ▼",
    bestOptionBadge: "⭐ सर्वोत्तम पर्याय",
    kmAway: "किमी",
    mandiPriceLabel: "बाजारभाव:",
    grossValueLabel: "एकूण किंमत ({q} क्विंटल):",
    transportDeductionLabel: "वाहतूक खर्च ({km} किमी × ₹१०):",
    netMandiValueLabel: "निव्वळ बाजार नफा:",
    aiForecastBtn: "एआय किंमत अंदाज",
    noMandisFound: "५०० किमीच्या परिसरात कोणताही बाजार आढळला नाही",
    noMandisFoundDesc: "आपल्या सध्याच्या स्थानावरून ५०० किमीच्या परिसरात {crop} खरेदी करणारी कोणतीही बाजार समिती उपलब्ध नाही.",

    // Step 6: Recommendation Engine
    recommendationTitle: "🎯 मंडीमित्र निर्णय प्रणाली",
    recommendationSubtitle: "बाजार नफा, दलाल ऑफर आणि एआय भावी किमतीच्या आधारे अचूक विक्री सल्ला",
    sellToday: "आजच विका",
    holdDays: "२–३ दिवस थांबा",
    currentBestNet: "सध्याचा सर्वोत्तम नफा:",
    predictedFutureNet: "अंदाजित भावी नफा:",
    expectedDiff: "संभाव्य फरक:",
    weatherFactor: "हवामान घटक:",
    produceLabel: "उत्पादन:",

    // Step 7: ML Forecast Details
    forecastTitle: "📈 २-३ दिवसांचा एआय किंमत अंदाज",
    forecastSubtitle: "{mandi} ({crop}) साठी मशीन लर्निंग मॉडेलचा अंदाज",
    currentModalPrice: "सध्याचा सरासरी भाव",
    expected3Day: "पुढील ३ दिवसांचे अपेक्षित भाव",
    tomorrow: "उद्या",
    day2: "२ दिवसांत",
    day3: "३ दिवसांत",
    trendLabel: "किमतीचा कल",
    trendRising: "वाढता",
    trendFalling: "घसरता",
    trendStable: "स्थिर",
    runningRegressor: "ग्रेडियंट बूस्टिंग रिग्रेसर विश्लेषण करत आहे...",
    calculatingFeatures: "{mandi} साठी ४० वैशिष्ट्ये व ३० दिवसांच्या किमतींचे विश्लेषण चालू आहे."
  }
};

export const LanguageProvider = ({ children }) => {
  // Default to English ('en')
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('mandimitra_lang') || 'en';
  });

  useEffect(() => {
    localStorage.setItem('mandimitra_lang', language);
  }, [language]);

  const t = (key, params = {}) => {
    const langDict = translations[language] || translations['en'];
    let text = langDict[key] || translations['en'][key] || key;

    // Interpolate params e.g. {crop}, {q}, {name}
    Object.keys(params).forEach(param => {
      text = text.replace(new RegExp(`\\{${param}\\}`, 'g'), params[param]);
    });

    return text;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => useContext(LanguageContext);
