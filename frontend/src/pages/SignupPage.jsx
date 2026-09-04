import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Check, Eye, EyeOff, Sparkles, MapPin, Sprout, ShieldCheck, ChevronDown, Plus, Minus, Navigation, RefreshCw } from 'lucide-react';
import signupFarmImg from '../assets/illustrations/signup_farm.jpg';
import vegetablesImg from '../assets/illustrations/vegetables.jpeg';
import wheatImg from '../assets/illustrations/wheat.jpg';
import riceImg from '../assets/illustrations/rice.jpg';
import tomatoImg from '../assets/illustrations/tomato.jpg';
import cottonImg from '../assets/illustrations/cotton.jpg';
import { signupUser } from '../services/authService';
import { getUserLocation } from '../services/locationService';

const statesData = {
  'Maharashtra': ['Nashik', 'Pune', 'Ahmednagar', 'Solapur', 'Nagpur', 'Aurangabad', 'Kolhapur', 'Satara', 'Jalgaon', 'Amravati', 'Sangli', 'Latur', 'Dhule', 'Nanded', 'Buldhana'],
  'Madhya Pradesh': ['Indore', 'Ujjain', 'Bhopal', 'Dewas', 'Mandsaur', 'Neemuch', 'Ratlam', 'Sehore', 'Hoshangabad', 'Vidisha', 'Khargone', 'Khandwa', 'Jabalpur', 'Gwalior'],
  'Uttar Pradesh': ['Agra', 'Aligarh', 'Bareilly', 'Kanpur', 'Lucknow', 'Mathura', 'Meerut', 'Varanasi', 'Prayagraj', 'Gorakhpur', 'Bulandshahr', 'Moradabad', 'Saharanpur'],
  'Punjab': ['Ludhiana', 'Amritsar', 'Jalandhar', 'Patiala', 'Bathinda', 'Sangrur', 'Firozpur', 'Hoshiarpur', 'Fazilka', 'Moga'],
  'Haryana': ['Karnal', 'Hisar', 'Ambala', 'Sirsa', 'Rohtak', 'Kurukshetra', 'Panipat', 'Sonipat', 'Yamunanagar', 'Fatehabad'],
  'Rajasthan': ['Jaipur', 'Jodhpur', 'Kota', 'Bikaner', 'Sriganganagar', 'Alwar', 'Nagaur', 'Hanumangarh', 'Ajmer', 'Bharatpur'],
  'Gujarat': ['Ahmedabad', 'Rajkot', 'Surat', 'Vadodara', 'Junagadh', 'Bhavnagar', 'Mehsana', 'Amreli', 'Banaskantha', 'Sabarkantha'],
  'Karnataka': ['Bangalore Rural', 'Belagavi', 'Ballari', 'Mysuru', 'Dharwad', 'Shimoga', 'Haveri', 'Tumakuru', 'Kolar', 'Bagalkot'],
  'Andhra Pradesh': ['Guntur', 'Kurnool', 'Krishna', 'East Godavari', 'West Godavari', 'Anantapur', 'Chittoor', 'Prakasam'],
  'Telangana': ['Warangal', 'Nizamabad', 'Khammam', 'Karimnagar', 'Mahabubnagar', 'Nalgonda', 'Medak', 'Adilabad'],
  'Bihar': ['Patna', 'Muzaffarpur', 'Gaya', 'Bhagalpur', 'Nalanda', 'Samastipur', 'Rohtas', 'Vaishali', 'Purnia'],
  'West Bengal': ['Hooghly', 'Burdwan', 'Nadia', 'Murshidabad', 'North 24 Parganas', 'Bankura', 'Malda'],
  'Tamil Nadu': ['Coimbatore', 'Madurai', 'Tiruchirappalli', 'Salem', 'Erode', 'Dindigul', 'Thanjavur', 'Tirunelveli'],
  'Other / All India': ['Other District']
};

const cropsList = [
  { name: 'Wheat', emoji: '🌾', img: wheatImg },
  { name: 'Rice', emoji: '🍚', img: riceImg },
  { name: 'Tomato', emoji: '🍅', img: tomatoImg },
  { name: 'Cotton', emoji: '🌿', img: cottonImg },
];

const SignupPage = () => {
  const [formData, setFormData] = useState({
    fullName: '',
    mobileNumber: '',
    state: '',
    district: '',
    villageTown: '',
    primaryCrop: '',
    password: '',
    confirmPassword: '',
    email: '',
    landSize: '',
    preferredMandi: '',
    agreeTerms: false,
  });

  const [coords, setCoords] = useState(null);
  const [isLocating, setIsLocating] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [showOptionalFields, setShowOptionalFields] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleGetLocation = async () => {
    setIsLocating(true);
    try {
      const loc = await getUserLocation();
      setCoords(loc);
    } catch (err) {
      console.warn('GPS error:', err);
    } finally {
      setIsLocating(false);
    }
  };

  const handleStateChange = (e) => {
    const selectedState = e.target.value;
    setFormData((prev) => ({
      ...prev,
      state: selectedState,
      district: '',
    }));
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    if (error) setError('');
  };

  const handleCropSelect = (cropName) => {
    setFormData((prev) => ({
      ...prev,
      primaryCrop: cropName,
    }));
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (
      !formData.fullName ||
      !formData.mobileNumber ||
      !formData.state ||
      !formData.district ||
      !formData.villageTown ||
      !formData.primaryCrop ||
      !formData.password ||
      !formData.confirmPassword
    ) {
      setError('Please fill in all required fields marked with *');
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (!formData.agreeTerms) {
      setError('Please agree to the Terms & Conditions and Privacy Policy');
      return;
    }
    setError('');
    setIsLoading(true);

    try {
      const payload = {
        full_name: formData.fullName.trim(),
        email: formData.email ? formData.email.trim() : null,
        mobile: formData.mobileNumber.trim(),
        password: formData.password,
        state: formData.state,
        district: formData.district,
        village: formData.villageTown.trim(),
        primary_crop: formData.primaryCrop,
        latitude: coords ? coords.latitude : null,
        longitude: coords ? coords.longitude : null,
      };

      await signupUser(payload);
      setIsSubmitted(true);
    } catch (err) {
      setError(err.message || 'Registration failed. Please check your information.');
    } finally {
      setIsLoading(false);
    }
  };


  const districtOptions = formData.state ? statesData[formData.state] || [] : [];

  return (
    <div className="min-h-screen bg-cream-50 flex flex-col lg:flex-row font-sans">
      {/* Left side - Visual Farm & 4 Supported Crops Showcase */}
      <div className="hidden lg:flex lg:w-5/12 bg-gradient-to-br from-primary-700 via-primary-800 to-green-950 text-white relative overflow-hidden flex-col justify-between p-10 xl:p-12">
        {/* Background glow effects */}
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-accent/20 rounded-full blur-3xl pointer-events-none"></div>

        {/* Brand & Navigation */}
        <div className="relative z-10">
          <Link to="/" className="inline-flex items-center text-primary-200 hover:text-white transition-colors gap-2 text-sm font-medium mb-6 bg-white/10 px-4 py-2 rounded-full backdrop-blur-sm">
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
          <div className="flex items-center space-x-3 mb-3">
            <span className="text-4xl">🌾</span>
            <div>
              <span className="text-3xl font-extrabold tracking-tight text-white">MandiMitra</span>
              <p className="text-primary-200 text-xs font-semibold tracking-wider uppercase">Kisan Ka Digital Saathi</p>
            </div>
          </div>
          <h1 className="text-3xl font-bold leading-tight mt-4 text-white">
            Smart Crop Selling Decisions for Indian Farmers.
          </h1>
          <p className="text-primary-100 text-sm mt-2 leading-relaxed">
            Get live mandi rates, AI-driven "Sell Today" or "Wait" recommendations, and nearby market comparisons.
          </p>
        </div>

        {/* Visual Showcase: Complete Farm Illustration (Uncropped) & 4 Supported Crops */}
        <div className="relative z-10 my-6 space-y-5">
          {/* Main Farm illustration - 1:1 square showing only the image with no green background */}
          <div className="relative rounded-3xl overflow-hidden shadow-2xl border-4 border-white/20">
            <img 
              src={signupFarmImg} 
              alt="Indian Happy Farm Scene" 
              className="w-full aspect-square object-cover"
            />
          </div>

          {/* 4 Supported Crops Section: Wheat, Rice, Tomato, Cotton */}
          <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/15 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-white uppercase tracking-wider">Top Tracked Crops</span>
              <span className="text-[11px] text-primary-200">Personalized Insights</span>
            </div>
            <div className="grid grid-cols-4 gap-2.5 text-center">
              {cropsList.map((crop) => {
                const isSelected = formData.primaryCrop === crop.name;
                return (
                  <div 
                    key={crop.name}
                    onClick={() => handleCropSelect(crop.name)}
                    className={`bg-white rounded-xl p-2 sm:p-2.5 cursor-pointer transition-all transform hover:scale-105 shadow-sm flex flex-col items-center justify-between border ${
                      isSelected ? 'ring-2 ring-accent border-accent' : 'border-transparent hover:border-gray-200'
                    }`}
                  >
                    <div className="w-10 h-10 sm:w-11 sm:h-11 flex items-center justify-center overflow-hidden">
                      <img src={crop.img} alt={crop.name} className="w-full h-full object-contain" />
                    </div>
                    <p className="text-[11px] font-bold text-gray-900 mt-1">{crop.name}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* AI Price Prediction Banner */}
          <div className="flex items-center gap-3 bg-white/10 backdrop-blur-sm p-3 rounded-2xl border border-white/10">
            <img 
              src={vegetablesImg} 
              alt="Cartoon Vegetables" 
              className="w-12 h-12 sm:w-14 sm:h-14 object-contain rounded-xl bg-white/80 p-0.5 flex-shrink-0"
            />
            <p className="text-xs text-primary-100 leading-snug">
              <strong className="text-white">AI Price Prediction:</strong> Know the highest-paying mandis in your district before leaving your farm.
            </p>
          </div>
        </div>

        {/* Security & Free Guarantee */}
        <div className="relative z-10 flex items-center justify-between text-xs text-primary-200 border-t border-white/10 pt-4">
          <span className="flex items-center gap-1.5"><ShieldCheck className="w-4 h-4 text-accent" /> 100% Free & Secure</span>
          <span className="flex items-center gap-1.5"><Sparkles className="w-4 h-4 text-accent" /> Powered by AI</span>
        </div>
      </div>

      {/* Right side - Form */}
      <div className="flex-1 flex flex-col justify-center px-6 sm:px-12 md:px-16 lg:px-16 xl:px-20 py-10 bg-white">
        <div className="max-w-xl w-full mx-auto">
          {/* Mobile Header Link */}
          <div className="lg:hidden flex items-center justify-between mb-6">
            <Link to="/" className="inline-flex items-center text-gray-500 hover:text-primary-600 transition-colors text-sm font-medium">
              <ArrowLeft className="w-4 h-4 mr-1.5" />
              Home
            </Link>
            <div className="flex items-center space-x-1.5">
              <span className="text-2xl">🌾</span>
              <span className="text-xl font-bold text-primary-700">MandiMitra</span>
            </div>
          </div>

          {/* Screen Title */}
          <div className="mb-8">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-primary-100 text-primary-700 uppercase tracking-wider mb-2">
              🌾 Sign Up
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight">Create your MandiMitra account</h2>
            <p className="text-gray-500 text-sm sm:text-base mt-1.5">
              Join thousands of farmers making smarter selling decisions.
            </p>
          </div>

          {isSubmitted ? (
            <div className="bg-primary-50 border border-primary-200 rounded-3xl p-8 text-center space-y-4 animate-in fade-in">
              <div className="w-16 h-16 bg-primary-600 text-white rounded-full flex items-center justify-center mx-auto shadow-lg">
                <Check className="w-8 h-8" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900">Account Created Successfully!</h3>
              <p className="text-gray-600 max-w-md mx-auto text-sm sm:text-base">
                Welcome to MandiMitra, <strong className="text-gray-900">{formData.fullName}</strong>. Your profile for <strong className="text-primary-700">{formData.primaryCrop}</strong> in <strong className="text-gray-900">{formData.district}, {formData.state}</strong> has been configured.
              </p>
              <div className="pt-4 flex flex-col sm:flex-row gap-3 justify-center">
                <Link to="/dashboard" className="inline-block bg-primary-600 hover:bg-primary-700 text-white font-bold px-8 py-3.5 rounded-full shadow-md transition-transform hover:-translate-y-0.5">
                  🌾 Go to Dashboard
                </Link>
                <Link to="/login" className="inline-block border-2 border-primary-600 text-primary-700 hover:bg-primary-50 font-bold px-8 py-3.5 rounded-full transition-all">
                  Sign In
                </Link>
              </div>
            </div>
          ) : (
            <form className="space-y-4 sm:space-y-5" onSubmit={handleSubmit}>
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm flex items-center gap-2">
                  <span className="font-bold">⚠️</span>
                  <span>{error}</span>
                </div>
              )}

              {/* 1. Full Name */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <input 
                  type="text" 
                  name="fullName"
                  value={formData.fullName}
                  onChange={handleChange}
                  placeholder="Enter your name"
                  required
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm transition-all"
                />
              </div>

              {/* 2. Mobile Number */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">
                  Mobile Number <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-500 text-sm font-semibold">
                    +91
                  </div>
                  <input 
                    type="tel" 
                    name="mobileNumber"
                    value={formData.mobileNumber}
                    onChange={handleChange}
                    placeholder="Enter mobile number"
                    maxLength={10}
                    required
                    className="w-full pl-12 pr-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm transition-all"
                  />
                </div>
              </div>

              {/* 3. State ▼ and 4. District ▼ */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* State ▼ */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">
                    State <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <select
                      name="state"
                      value={formData.state}
                      onChange={handleStateChange}
                      required
                      className="w-full appearance-none px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm bg-white pr-10 transition-all cursor-pointer"
                    >
                      <option value="">Select State ▼</option>
                      {Object.keys(statesData).map((st) => (
                        <option key={st} value={st}>{st}</option>
                      ))}
                    </select>
                    <ChevronDown className="w-4 h-4 text-gray-400 absolute right-3.5 top-1/2 transform -translate-y-1/2 pointer-events-none" />
                  </div>
                </div>

                {/* District ▼ */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">
                    District <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <select
                      name="district"
                      value={formData.district}
                      onChange={handleChange}
                      disabled={!formData.state}
                      required
                      className="w-full appearance-none px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm bg-white pr-10 transition-all cursor-pointer disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
                    >
                      <option value="">{formData.state ? 'Select District ▼' : 'Select State first'}</option>
                      {districtOptions.map((dist) => (
                        <option key={dist} value={dist}>{dist}</option>
                      ))}
                    </select>
                    <ChevronDown className="w-4 h-4 text-gray-400 absolute right-3.5 top-1/2 transform -translate-y-1/2 pointer-events-none" />
                  </div>
                </div>
              </div>

              {/* 5. Village / Town */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm font-semibold text-gray-700">
                    Village / Town <span className="text-red-500">*</span>
                  </label>
                  <button
                    type="button"
                    onClick={handleGetLocation}
                    disabled={isLocating}
                    className="text-xs font-bold text-primary-700 hover:text-primary-800 flex items-center gap-1 bg-primary-50 hover:bg-primary-100 px-2.5 py-1 rounded-lg border border-primary-200 transition-all cursor-pointer"
                  >
                    {isLocating ? <RefreshCw size={13} className="animate-spin" /> : <Navigation size={13} />}
                    <span>{coords ? '📍 GPS Attached' : '📍 Use My GPS'}</span>
                  </button>
                </div>
                <input 
                  type="text" 
                  name="villageTown"
                  value={formData.villageTown}
                  onChange={handleChange}
                  placeholder="Enter your village or town"
                  required
                  className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm transition-all"
                />
                {coords && (
                  <p className="text-[11px] text-emerald-600 font-semibold mt-1">
                    ✓ Exact farm coordinates captured ({coords.latitude.toFixed(4)}, {coords.longitude.toFixed(4)})
                  </p>
                )}
              </div>

              {/* 6. Primary Crop ▼ (ONLY 4 crops: Wheat, Rice, Tomato, Cotton) */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">
                  Primary Crop <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <select
                    name="primaryCrop"
                    value={formData.primaryCrop}
                    onChange={handleChange}
                    required
                    className="w-full appearance-none px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm bg-white pr-10 transition-all cursor-pointer"
                  >
                    <option value="">Select Primary Crop ▼</option>
                    {cropsList.map((c) => (
                      <option key={c.name} value={c.name}>
                        {c.emoji} {c.name}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="w-4 h-4 text-gray-400 absolute right-3.5 top-1/2 transform -translate-y-1/2 pointer-events-none" />
                </div>
                {/* Popular Pill Buttons for the 4 Crops */}
                <div className="flex items-center gap-2 mt-2 overflow-x-auto pb-1 text-xs">
                  <span className="text-gray-400 text-[11px] font-medium flex-shrink-0">Popular:</span>
                  {cropsList.map((c) => (
                    <button
                      key={c.name}
                      type="button"
                      onClick={() => handleCropSelect(c.name)}
                      className={`px-3 py-1 rounded-full border transition-all flex items-center gap-1.5 cursor-pointer flex-shrink-0 text-xs ${
                        formData.primaryCrop === c.name
                          ? 'bg-primary-100 border-primary-500 text-primary-800 font-bold shadow-sm'
                          : 'bg-cream-100 border-gray-200 text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <span>{c.emoji}</span> {c.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* 7. Password and 8. Confirm Password */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Password */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">
                    Password <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input 
                      type={showPassword ? 'text' : 'password'} 
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      placeholder="Enter password"
                      required
                      className="w-full px-4 py-3 pr-11 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-1"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Confirm Password */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">
                    Confirm Password <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <input 
                      type={showConfirmPassword ? 'text' : 'password'} 
                      name="confirmPassword"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      placeholder="Confirm password"
                      required
                      className="w-full px-4 py-3 pr-11 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-1"
                    >
                      {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>

              {/* Optional Details (Email Address, Land Size, Preferred Mandi) */}
              <div className="pt-1">
                <button
                  type="button"
                  onClick={() => setShowOptionalFields(!showOptionalFields)}
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-primary-700 hover:text-primary-800 transition-colors py-1"
                >
                  {showOptionalFields ? <Minus className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
                  <span>{showOptionalFields ? 'Hide' : 'Add'} Optional Details (Email, Land Size, Preferred Mandi)</span>
                </button>

                {showOptionalFields && (
                  <div className="mt-3 p-4 rounded-2xl bg-cream-100 border border-gray-200 space-y-3 animate-in fade-in">
                    <div>
                      <label className="block text-xs font-semibold text-gray-700 mb-1">
                        Email Address <span className="text-gray-400 font-normal">(Optional)</span>
                      </label>
                      <input 
                        type="email" 
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        placeholder="e.g. farmer@example.com"
                        className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm bg-white"
                      />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1">
                          Land Size <span className="text-gray-400 font-normal">(Optional, e.g. 2 acres)</span>
                        </label>
                        <input 
                          type="text" 
                          name="landSize"
                          value={formData.landSize}
                          onChange={handleChange}
                          placeholder="e.g. 2 acres / 5 bigha"
                          className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm bg-white"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1">
                          Preferred / Nearby Mandi <span className="text-gray-400 font-normal">(Optional)</span>
                        </label>
                        <input 
                          type="text" 
                          name="preferredMandi"
                          value={formData.preferredMandi}
                          onChange={handleChange}
                          placeholder="e.g. Lasalgaon Mandi"
                          className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm bg-white"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Agreement Checkbox */}
              <div className="pt-2">
                <label className="flex items-start gap-3 cursor-pointer select-none">
                  <input 
                    type="checkbox" 
                    name="agreeTerms"
                    checked={formData.agreeTerms}
                    onChange={handleChange}
                    className="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500 mt-0.5 cursor-pointer accent-primary-600"
                  />
                  <span className="text-xs sm:text-sm text-gray-600">
                    I agree to the{' '}
                    <Link to="/terms" className="text-primary-600 font-semibold hover:underline">Terms & Conditions</Link>{' '}
                    and{' '}
                    <Link to="/terms" className="text-primary-600 font-semibold hover:underline">Privacy Policy</Link>
                  </span>
                </label>
              </div>

              {error && (
                <div className="p-3.5 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm flex items-center gap-2">
                  <span className="font-bold">⚠️</span>
                  <span>{error}</span>
                </div>
              )}

              {/* Create Account Button */}
              <button 
                type="submit"
                disabled={isLoading}
                className="w-full bg-primary-600 hover:bg-primary-700 active:bg-primary-800 text-white font-bold py-3.5 rounded-xl shadow-lg hover:shadow-xl transition-all hover:-translate-y-0.5 text-base sm:text-lg flex items-center justify-center gap-2 cursor-pointer mt-2 disabled:opacity-70"
              >
                {isLoading ? (
                  <><RefreshCw size={20} className="animate-spin" /> <span>Creating Account...</span></>
                ) : (
                  <><span>Create Account</span> <span className="text-xl">🌾</span></>
                )}
              </button>

              <p className="text-center text-sm text-gray-600 pt-1">
                Already have an account?{' '}
                <Link to="/login" className="text-primary-600 font-bold hover:underline">
                  Sign In
                </Link>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default SignupPage;
