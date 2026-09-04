import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, AlertCircle } from 'lucide-react';
import { loginUser } from '../services/authService';

import authImg from '../assets/illustrations/auth.jpg';

const LoginPage = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Please enter both your mobile/email and password.');
      return;
    }
    setError('');
    setIsLoading(true);
    try {
      await loginUser(username.trim(), password.trim());
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Login failed. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-cream-50 flex flex-col md:flex-row">
      {/* Left side - Form */}
      <div className="flex-1 flex flex-col justify-center px-8 md:px-20 lg:px-32 py-12 bg-white shadow-2xl z-10">
        <Link to="/" className="inline-flex items-center text-gray-500 hover:text-primary-600 mb-12 w-max transition-colors">
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back to Home
        </Link>
        
        <div className="max-w-md w-full mx-auto space-y-8">
          <div>
            <div className="flex items-center space-x-2 mb-6">
              <span className="text-3xl">🌾</span>
              <span className="text-2xl font-bold text-primary-700">MandiMitra</span>
            </div>
            <h2 className="text-4xl font-bold text-gray-900 mb-2">Welcome Back</h2>
            <p className="text-gray-500">Sign in to your account to continue</p>
          </div>

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2 text-red-700 text-sm">
              <AlertCircle size={18} className="flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form className="space-y-6" onSubmit={handleLogin}>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email / Mobile Number</label>
              <input 
                type="text" 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter email or mobile"
                required
                className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              />
            </div>

            <button 
              type="submit"
              disabled={isLoading}
              className="w-full bg-primary-600 hover:bg-primary-700 text-white font-bold py-3.5 rounded-xl shadow-md transition-colors text-lg flex items-center justify-center gap-2 disabled:opacity-70"
            >
              {isLoading ? (
                <><RefreshCw size={20} className="animate-spin" /> Signing In...</>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <p className="text-center text-gray-600">
            Don't have an account?{' '}
            <Link to="/signup" className="text-primary-600 font-bold hover:underline">
              Sign Up
            </Link>
          </p>
        </div>
      </div>

      {/* Right side - Illustration */}
      <div className="hidden md:flex flex-1 bg-primary-50 relative overflow-hidden items-center justify-center p-12">
        <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-primary-400 via-transparent to-transparent"></div>
        <div className="relative w-full max-w-xl aspect-square rounded-[3rem] overflow-hidden shadow-2xl border-8 border-white transform -rotate-2 hover:rotate-0 transition-transform duration-500">
          <img 
            src={authImg} 
            alt="Indian farmer checking crops on smartphone" 
            className="w-full h-full object-cover"
          />
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
