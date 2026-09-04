import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { Shield, FileText, Phone } from 'lucide-react';

const TermsPage = () => {
  return (
    <div className="min-h-screen flex flex-col bg-white font-sans text-gray-800">
      <Navbar />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-20">
        {/* Header */}
        <div className="text-center space-y-4 mb-12">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full text-xs font-semibold bg-primary-100 text-primary-700 uppercase tracking-wider">
            <FileText className="w-3.5 h-3.5" />
            Legal
          </div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-gray-900 tracking-tight">
            Terms & Conditions
          </h1>
          <p className="text-sm font-medium text-gray-500">
            Last Updated: September 2026
          </p>
        </div>

        {/* Introduction */}
        <div className="prose max-w-none text-gray-600 space-y-8 text-base leading-relaxed">
          <div className="bg-cream-100 border border-gray-200 rounded-2xl p-6 text-gray-700">
            <p className="font-medium text-gray-900">
              Welcome to MandiMitra. By accessing or using the MandiMitra platform, you agree to these Terms & Conditions.
            </p>
          </div>

          {/* Section 1 */}
          <div className="space-y-2 border-b border-gray-100 pb-6">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2.5">
              <span className="w-7 h-7 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-bold">1</span>
              Use of the Platform
            </h2>
            <p className="text-gray-600 pl-9">
              MandiMitra provides market information, price trends, and AI-based insights to help farmers make informed crop-selling decisions.
            </p>
          </div>

          {/* Section 2 */}
          <div className="space-y-2 border-b border-gray-100 pb-6">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2.5">
              <span className="w-7 h-7 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-bold">2</span>
              Information Provided
            </h2>
            <p className="text-gray-600 pl-9">
              The information displayed on MandiMitra is intended for general informational purposes. Market prices, forecasts, and recommendations may change and may not always be accurate.
            </p>
          </div>

          {/* Section 3 */}
          <div className="space-y-2 border-b border-gray-100 pb-6">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2.5">
              <span className="w-7 h-7 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-bold">3</span>
              AI Recommendations
            </h2>
            <p className="text-gray-600 pl-9">
              MandiMitra may provide recommendations such as “Sell Today” or “Wait” based on available data and machine-learning models. These recommendations are not financial or agricultural guarantees.
            </p>
          </div>

          {/* Section 4 */}
          <div className="space-y-2 border-b border-gray-100 pb-6">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2.5">
              <span className="w-7 h-7 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-bold">4</span>
              User Responsibility
            </h2>
            <p className="text-gray-600 pl-9">
              Users are responsible for making their own decisions regarding the sale of their crops. MandiMitra is not responsible for losses resulting from decisions made using the platform.
            </p>
          </div>

          {/* Section 5 */}
          <div className="space-y-2 border-b border-gray-100 pb-6">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2.5">
              <span className="w-7 h-7 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-bold">5</span>
              Data Accuracy
            </h2>
            <p className="text-gray-600 pl-9">
              We aim to provide reliable and up-to-date information, but we cannot guarantee that all market data will always be complete, accurate, or available.
            </p>
          </div>

          {/* Section 6 */}
          <div className="space-y-2 border-b border-gray-100 pb-6">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2.5">
              <span className="w-7 h-7 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-bold">6</span>
              Account Security
            </h2>
            <p className="text-gray-600 pl-9">
              Users are responsible for keeping their account credentials confidential and for all activity performed through their account.
            </p>
          </div>

          {/* Section 7 */}
          <div className="space-y-2 border-b border-gray-100 pb-6">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2.5">
              <span className="w-7 h-7 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-bold">7</span>
              Changes to the Platform
            </h2>
            <p className="text-gray-600 pl-9">
              MandiMitra may update, modify, or discontinue features of the platform at any time.
            </p>
          </div>

          {/* Section 8 */}
          <div className="space-y-2 pb-6">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2.5">
              <span className="w-7 h-7 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-bold">8</span>
              Contact
            </h2>
            <p className="text-gray-600 pl-9">
              For questions regarding these Terms & Conditions, contact us at{' '}
              <a href="tel:8850347147" className="text-primary-600 font-semibold hover:underline">
                8850347147
              </a>{' '}
              or email{' '}
              <a href="mailto:support@mandimitra.in" className="text-primary-600 font-semibold hover:underline">
                support@mandimitra.in
              </a>.
            </p>
          </div>
        </div>

        {/* Back Link */}
        <div className="mt-12 pt-8 border-t border-gray-200 flex justify-between items-center flex-wrap gap-4 text-sm">
          <Link to="/" className="text-primary-600 hover:text-primary-700 font-semibold">
            &larr; Return to Home
          </Link>
          <Link to="/faq" className="text-gray-500 hover:text-primary-600 font-medium">
            Frequently Asked Questions &rarr;
          </Link>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default TermsPage;
