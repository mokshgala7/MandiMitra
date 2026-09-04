import { Link } from 'react-router-dom';
import { useLanguage } from '../context/LanguageContext';

const Footer = () => {
  const { t } = useLanguage();

  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center flex-col md:flex-row gap-6">
          <div className="flex items-center space-x-2">
            <span className="text-3xl">🌾</span>
            <span className="text-2xl font-bold text-primary-700">{t('appName')}</span>
          </div>
          
          <div className="flex flex-col md:flex-row items-center gap-6">
            <div className="flex flex-wrap justify-center gap-6 text-sm font-medium">
              <Link to="/" className="text-gray-500 hover:text-primary-600 transition-colors">{t('home')}</Link>
              <a href="/#how-it-works" className="text-gray-500 hover:text-primary-600 transition-colors">{t('howItWorks')}</a>
              <a href="/#about-us" className="text-gray-500 hover:text-primary-600 transition-colors">{t('aboutUs')}</a>
              <a href="/#contact" className="text-gray-500 hover:text-primary-600 transition-colors">{t('contactUs')}</a>
              <Link to="/faq" className="text-gray-500 hover:text-primary-600 transition-colors">FAQ</Link>
              <Link to="/terms" className="text-gray-500 hover:text-primary-600 transition-colors">Terms & Conditions</Link>
            </div>
            <div className="text-xs text-gray-500 text-center md:text-right">
              <p>📞 +91 88503 47147 &bull; ✉️ support@mandimitra.in</p>
              <p className="text-gray-400">Mumbai, Maharashtra, India</p>
            </div>
          </div>
        </div>
        
        <div className="mt-8 pt-6 border-t border-gray-100 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-gray-400 text-xs text-center sm:text-left">
            &copy; 2026 {t('appName')}. Helping farmers make smarter selling decisions.
          </p>
          <p className="text-gray-400 text-xs">
            All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
