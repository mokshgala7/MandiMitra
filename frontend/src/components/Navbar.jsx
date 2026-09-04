import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getStoredUser, getCurrentUser, logout } from '../services/authService';
import { useLanguage } from '../context/LanguageContext';
import LanguageSelector from './LanguageSelector';

const Navbar = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(getStoredUser());
  const { t } = useLanguage();

  useEffect(() => {
    setUser(getStoredUser());
    getCurrentUser().then(fresh => {
      if (fresh) setUser(fresh);
    });
  }, []);

  const handleLogout = () => {
    logout();
    setUser(null);
    navigate('/');
  };

  return (
    <nav className="bg-white shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <span className="text-3xl">🌾</span>
            <span className="text-2xl font-bold text-primary-700">{t('appName')}</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-7">
            <Link to="/" className="text-gray-600 hover:text-primary-600 font-medium transition-colors">{t('home')}</Link>
            <a href="/#how-it-works" className="text-gray-600 hover:text-primary-600 font-medium transition-colors">{t('howItWorks')}</a>
            <a href="/#about-us" className="text-gray-600 hover:text-primary-600 font-medium transition-colors">{t('aboutUs')}</a>
            <a href="/#contact" className="text-gray-600 hover:text-primary-600 font-medium transition-colors">{t('contactUs')}</a>
          </div>

          {/* Language Selector + Action Buttons */}
          <div className="flex items-center space-x-3">
            <LanguageSelector />

            {user ? (
              <>
                <Link
                  to="/dashboard"
                  className="bg-primary-600 hover:bg-primary-700 text-white px-4 sm:px-5 py-2 sm:py-2.5 rounded-full font-semibold transition-all shadow-md hover:shadow-lg flex items-center gap-2 text-xs sm:text-sm"
                >
                  <span>{t('dashboard')}</span>
                  <span className="bg-primary-700 text-emerald-100 text-[10px] sm:text-xs px-2 py-0.5 rounded-full font-normal">
                    {user.full_name?.split(' ')[0] || 'Farmer'}
                  </span>
                </Link>
                <button
                  onClick={handleLogout}
                  className="text-gray-500 hover:text-red-600 text-xs sm:text-sm font-medium px-2.5 py-1.5 rounded-lg transition-colors"
                >
                  {t('logout')}
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-primary-600 font-semibold hover:text-primary-700 px-3 py-2 hidden sm:block transition-colors text-sm">
                  {t('signIn')}
                </Link>
                <Link to="/signup" className="bg-primary-500 hover:bg-primary-600 text-white px-5 py-2.5 rounded-full font-semibold transition-all shadow-md hover:shadow-lg text-sm">
                  {t('signUp')}
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
