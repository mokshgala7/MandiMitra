import { useState } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Sprout, TrendingUp, Cpu, MapPin, Target, Sparkles, Compass, Phone, Mail, Send, Check } from 'lucide-react';
import farmerImg from '../assets/illustrations/image.png';
import heroImg from '../assets/illustrations/hero.jpg';

const LandingPage = () => {
  const [contactData, setContactData] = useState({
    name: '',
    mobile: '',
    email: '',
    message: ''
  });
  const [isContactSent, setIsContactSent] = useState(false);

  const handleContactSubmit = (e) => {
    e.preventDefault();
    if (!contactData.name || !contactData.mobile || !contactData.message) {
      alert('Please fill in your name, mobile number, and message.');
      return;
    }
    setIsContactSent(true);
  };
  return (
    <div className="min-h-screen flex flex-col bg-cream-50 font-sans">
      <Navbar />

      {/* Hero Section */}
      <section className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24 flex flex-col-reverse md:flex-row items-center gap-12">
        <div className="flex-1 text-center md:text-left space-y-8">
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 leading-tight">
            Sell Smarter. <br />
            <span className="text-primary-600">Earn Better.</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-lg mx-auto md:mx-0">
            MandiMitra helps farmers make better decisions about when and where to sell their crops using real-time market data.
          </p>
          <div className="pt-4">
            <Link to="/signup" className="inline-block bg-accent hover:bg-accent-hover text-white px-8 py-4 rounded-full font-bold text-lg shadow-lg hover:shadow-xl transition-all hover:-translate-y-1">
              Get Started
            </Link>
          </div>
        </div>
        <div className="flex-1 w-full flex justify-center">
          <div className="relative w-full max-w-lg aspect-square rounded-[3rem] overflow-hidden shadow-2xl border-8 border-white transform rotate-3 hover:rotate-0 transition-transform duration-500">
            <img
              src={heroImg}
              alt="Indian farmer using smartphone in field"
              className="w-full h-full object-cover"
            />
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="bg-white py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">How It Works</h2>
            <p className="text-xl text-gray-500">Three simple steps to maximize your profits</p>
          </div>

          <div className="grid md:grid-cols-3 gap-12 text-center">
            <div className="flex flex-col items-center space-y-4">
              <div className="w-24 h-24 bg-primary-100 rounded-full flex items-center justify-center mb-4 shadow-inner">
                <Sprout className="w-12 h-12 text-primary-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900">1. Select Your Crop</h3>
              <p className="text-gray-600">Choose the crop you want to sell from your harvest.</p>
            </div>
            <div className="flex flex-col items-center space-y-4">
              <div className="w-24 h-24 bg-accent/20 rounded-full flex items-center justify-center mb-4 shadow-inner">
                <TrendingUp className="w-12 h-12 text-accent" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900">2. Check Market Prices</h3>
              <p className="text-gray-600">See live mandi prices and historical market trends.</p>
            </div>
            <div className="flex flex-col items-center space-y-4">
              <div className="w-24 h-24 bg-blue-100 rounded-full flex items-center justify-center mb-4 shadow-inner">
                <Cpu className="w-12 h-12 text-blue-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900">3. Get AI Recommendation</h3>
              <p className="text-gray-600">MandiMitra analyzes data to advise you to sell now or wait.</p>
            </div>
          </div>
        </div>
      </section>

      {/* About Us */}
      <section id="about-us" className="py-24 bg-cream-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          {/* Main About Intro Grid with Farmer Mascot */}
          <div className="grid md:grid-cols-12 gap-8 items-center">
            <div className="md:col-span-7 space-y-6 text-center md:text-left">
              <div>
                <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-semibold bg-primary-100 text-primary-700 uppercase tracking-wider mb-3">
                  About Us
                </span>
                <h2 className="text-4xl md:text-5xl font-bold text-gray-900 tracking-tight">About MandiMitra</h2>
              </div>
              <p className="text-xl text-gray-700 leading-relaxed">
                <strong className="font-semibold text-gray-900">MandiMitra</strong> is a smart crop-selling decision support platform designed to help farmers make better decisions about <strong className="font-semibold text-primary-700">where and when to sell their produce</strong>.
              </p>
              
              {/* Goal Callout Banner */}
              <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-3xl p-6 md:p-8 text-white shadow-xl flex flex-col sm:flex-row items-center sm:items-start gap-5 text-center sm:text-left">
                <div className="w-14 h-14 bg-white/15 backdrop-blur-sm rounded-2xl flex items-center justify-center flex-shrink-0 shadow-inner">
                  <Target className="w-8 h-8 text-white" />
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-primary-200">Our Goal</p>
                  <p className="text-lg md:text-xl font-bold mt-0.5 text-white">
                    Help farmers sell at the right time, at the right market, and make more informed decisions.
                  </p>
                </div>
              </div>
            </div>

            {/* Farmer Illustration Mascot */}
            <div className="md:col-span-5 flex flex-col items-center justify-center">
              <div className="relative flex justify-center items-center w-full">
                <img 
                  src={farmerImg} 
                  alt="MandiMitra Farmer Friend" 
                  className="w-72 sm:w-80 md:w-96 max-h-[460px] object-contain filter drop-shadow-xl hover:scale-105 transition-transform duration-300"
                />
              </div>
              <div className="mt-4 inline-flex items-center gap-2 px-5 py-2 bg-white/90 backdrop-blur-sm border border-gray-200/80 rounded-full text-sm font-semibold text-gray-800 shadow-md">
                <span className="w-2.5 h-2.5 rounded-full bg-primary-500 animate-pulse"></span>
                Built for India's Farmers
              </div>
            </div>
          </div>

          {/* Core Pillars / Features Grid */}
          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow flex flex-col justify-between">
              <div className="space-y-4">
                <div className="w-12 h-12 bg-primary-100 rounded-2xl flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-primary-600" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900">Market Intelligence</h3>
                <p className="text-gray-600 leading-relaxed">
                  We bring together mandi prices, historical price trends, nearby market comparisons, and other relevant information to give farmers a simple and easy-to-understand view of the market.
                </p>
              </div>
              <div className="flex flex-wrap gap-2 pt-6">
                <span className="inline-flex items-center text-xs font-medium bg-gray-100 text-gray-700 px-3 py-1 rounded-full">Live Mandi Prices</span>
                <span className="inline-flex items-center text-xs font-medium bg-gray-100 text-gray-700 px-3 py-1 rounded-full">Historical Trends</span>
                <span className="inline-flex items-center text-xs font-medium bg-gray-100 text-gray-700 px-3 py-1 rounded-full">Nearby Market Comparisons</span>
              </div>
            </div>

            <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow flex flex-col justify-between">
              <div className="space-y-4">
                <div className="w-12 h-12 bg-accent/20 rounded-2xl flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-accent" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900">AI-Powered Insights</h3>
                <p className="text-gray-600 leading-relaxed">
                  With AI-powered insights, MandiMitra analyzes available market data and provides actionable recommendations such as <strong className="font-semibold text-gray-900">“Sell Today”</strong> or <strong className="font-semibold text-gray-900">“Wait”</strong>, helping farmers reduce uncertainty and improve their chances of getting a better price.
                </p>
              </div>
              <div className="flex flex-wrap gap-2 pt-6">
                <span className="inline-flex items-center text-xs font-medium bg-green-50 text-green-700 border border-green-200 px-3 py-1 rounded-full">“Sell Today”</span>
                <span className="inline-flex items-center text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200 px-3 py-1 rounded-full">“Wait”</span>
                <span className="inline-flex items-center text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 px-3 py-1 rounded-full">Better Price Opportunities</span>
              </div>
            </div>
          </div>

          {/* Our Mission */}
          <div className="bg-white rounded-3xl p-8 md:p-10 shadow-sm border border-primary-100 relative overflow-hidden">
            <div className="relative z-10 max-w-3xl mx-auto text-center space-y-4">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-primary-100 rounded-full text-primary-600 mb-2">
                <Compass className="w-6 h-6" />
              </div>
              <h3 className="text-3xl font-bold text-gray-900">Our Mission</h3>
              <p className="text-lg md:text-xl text-gray-700 leading-relaxed">
                To make market information easier to access and understand, so that every farmer can make <span className="font-semibold text-primary-700">data-driven selling decisions with confidence</span>.
              </p>
              <div className="pt-4 border-t border-gray-100 mt-6">
                <p className="text-base font-semibold text-gray-900 tracking-wide">
                  MandiMitra — Making smarter selling decisions simpler for farmers.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Contact Us */}
      <section id="contact" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
            <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-semibold bg-primary-100 text-primary-700 uppercase tracking-wider">
              Get In Touch
            </span>
            <h2 className="text-4xl md:text-5xl font-extrabold text-gray-900 tracking-tight">Contact Us</h2>
            <p className="text-lg text-gray-600 leading-relaxed">
              Have a question, feedback, or need help using MandiMitra? We’d love to hear from you.
            </p>
            <p className="text-sm text-gray-500 max-w-2xl mx-auto">
              Whether you have a question about mandi prices, selling decisions, or our platform, feel free to get in touch with us.
            </p>
          </div>

          <div className="grid lg:grid-cols-12 gap-10 items-start max-w-6xl mx-auto">
            {/* Left Card - Direct Contact Info */}
            <div className="lg:col-span-5 bg-gradient-to-br from-cream-100 via-white to-primary-50/50 p-8 sm:p-10 rounded-3xl border border-gray-200/80 shadow-lg space-y-8">
              <div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Get in Touch</h3>
                <p className="text-sm text-gray-600">
                  Reach out directly through phone, email, or visit our office.
                </p>
              </div>

              <div className="space-y-6">
                {/* Phone */}
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-primary-100 rounded-2xl flex items-center justify-center flex-shrink-0 text-primary-700 shadow-sm">
                    <Phone className="w-6 h-6" />
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">Phone</span>
                    <a href="tel:8850347147" className="text-lg font-bold text-gray-900 hover:text-primary-600 transition-colors">
                      +91 88503 47147
                    </a>
                    <p className="text-xs text-gray-500 mt-0.5">Mon–Sat, 8:00 AM – 7:00 PM</p>
                  </div>
                </div>

                {/* Email */}
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-primary-100 rounded-2xl flex items-center justify-center flex-shrink-0 text-primary-700 shadow-sm">
                    <Mail className="w-6 h-6" />
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">Email</span>
                    <a href="mailto:support@mandimitra.in" className="text-lg font-bold text-gray-900 hover:text-primary-600 transition-colors">
                      support@mandimitra.in
                    </a>
                    <p className="text-xs text-gray-500 mt-0.5">Online support & queries</p>
                  </div>
                </div>

                {/* Address */}
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-primary-100 rounded-2xl flex items-center justify-center flex-shrink-0 text-primary-700 shadow-sm">
                    <MapPin className="w-6 h-6" />
                  </div>
                  <div>
                    <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider block">Address</span>
                    <p className="text-base font-bold text-gray-900">
                      Mumbai, Maharashtra, India
                    </p>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-gray-200/70">
                <div className="inline-flex items-center gap-2 text-xs font-semibold text-primary-800 bg-primary-100/70 px-4 py-2 rounded-full">
                  <span>🌾</span>
                  <span>MandiMitra — Helping farmers make smarter selling decisions.</span>
                </div>
              </div>
            </div>

            {/* Right Card - Send Us a Message Form */}
            <div className="lg:col-span-7 bg-white p-8 sm:p-10 rounded-3xl border border-gray-200 shadow-lg">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Send Us a Message</h3>
              <p className="text-sm text-gray-500 mb-6">
                Fill in the form below and our team will get back to you shortly.
              </p>

              {isContactSent ? (
                <div className="bg-primary-50 border border-primary-200 rounded-2xl p-8 text-center space-y-3 animate-in fade-in">
                  <div className="w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center mx-auto shadow-md">
                    <Check className="w-6 h-6" />
                  </div>
                  <h4 className="text-xl font-bold text-gray-900">Thank you for contacting us!</h4>
                  <p className="text-sm text-gray-600">
                    We have received your message and will respond as soon as possible.
                  </p>
                  <button 
                    onClick={() => {
                      setIsContactSent(false);
                      setContactData({ name: '', mobile: '', email: '', message: '' });
                    }}
                    className="mt-4 text-xs font-semibold text-primary-700 hover:underline"
                  >
                    Send another message
                  </button>
                </div>
              ) : (
                <form onSubmit={handleContactSubmit} className="space-y-4">
                  {/* Name */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-1">
                      Name <span className="text-red-500">*</span>
                    </label>
                    <input 
                      type="text"
                      value={contactData.name}
                      onChange={(e) => setContactData({ ...contactData, name: e.target.value })}
                      placeholder="Enter your name"
                      required
                      className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm transition-all"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Mobile Number */}
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        Mobile Number <span className="text-red-500">*</span>
                      </label>
                      <input 
                        type="tel"
                        value={contactData.mobile}
                        onChange={(e) => setContactData({ ...contactData, mobile: e.target.value })}
                        placeholder="Enter your mobile number"
                        required
                        className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm transition-all"
                      />
                    </div>

                    {/* Email Address */}
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        Email Address <span className="text-gray-400 font-normal">(Optional)</span>
                      </label>
                      <input 
                        type="email"
                        value={contactData.email}
                        onChange={(e) => setContactData({ ...contactData, email: e.target.value })}
                        placeholder="Enter your email address"
                        className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm transition-all"
                      />
                    </div>
                  </div>

                  {/* Message */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-1">
                      Message <span className="text-red-500">*</span>
                    </label>
                    <textarea 
                      rows={4}
                      value={contactData.message}
                      onChange={(e) => setContactData({ ...contactData, message: e.target.value })}
                      placeholder="How can we help you?"
                      required
                      className="w-full px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm transition-all resize-none"
                    ></textarea>
                  </div>

                  {/* Submit Button */}
                  <button 
                    type="submit"
                    className="w-full bg-primary-600 hover:bg-primary-700 active:bg-primary-800 text-white font-bold py-3.5 rounded-xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 text-base cursor-pointer"
                  >
                    <Send className="w-4 h-4" />
                    <span>Send Message</span>
                  </button>

                  <p className="text-xs text-gray-500 text-center pt-2">
                    We aim to respond to your queries as soon as possible.
                  </p>
                </form>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="bg-primary-600 py-20 text-center">
        <div className="max-w-4xl mx-auto px-4">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-8">
            Make your next selling decision smarter.
          </h2>
          <Link to="/signup" className="inline-block bg-white text-primary-700 hover:bg-cream-50 px-10 py-4 rounded-full font-bold text-xl shadow-lg transition-transform hover:-translate-y-1">
            Get Started Now
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default LandingPage;
