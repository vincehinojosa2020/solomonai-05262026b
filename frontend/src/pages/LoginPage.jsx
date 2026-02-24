import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, Copy, Check, Loader2 } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

// Google SVG Icon
const GoogleIcon = () => (
  <svg viewBox="0 0 24 24" width="18" height="18">
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
  </svg>
);

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [copiedAdmin, setCopiedAdmin] = useState(false);
  const [copiedMember, setCopiedMember] = useState(false);

  const handleGoogleLogin = () => {
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const handleEmailLogin = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Please enter email and password');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }

      const data = await response.json();
      
      // Route based on role
      if (data.role === 'member') {
        navigate('/portal', { state: { user: data } });
      } else {
        navigate('/dashboard', { state: { user: data } });
      }
      
      toast.success(`Welcome, ${data.name}!`);
    } catch (error) {
      toast.error(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const copyCredentials = async (type) => {
    const creds = type === 'admin' 
      ? 'admin@abundant.church / Demo2026!'
      : 'member@abundant.church / Demo2026!';
    
    await navigator.clipboard.writeText(creds);
    
    if (type === 'admin') {
      setCopiedAdmin(true);
      setTimeout(() => setCopiedAdmin(false), 2000);
    } else {
      setCopiedMember(true);
      setTimeout(() => setCopiedMember(false), 2000);
    }
    toast.success('Credentials copied!');
  };

  const fillCredentials = (type) => {
    if (type === 'admin') {
      setEmail('admin@abundant.church');
      setPassword('Demo2026!');
    } else {
      setEmail('member@abundant.church');
      setPassword('Demo2026!');
    }
  };

  return (
    <div className="login-page" data-testid="login-page">
      {/* Left Panel - System Info */}
      <div className="login-sidebar">
        <div>
          <div className="login-logo">
            SAMS<span className="accent">O</span>N
          </div>
          <div className="login-tagline">
            Enterprise Church Management System
          </div>
          
          <div className="mt-12 space-y-6">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-blue-600/20 flex items-center justify-center flex-shrink-0">
                <svg className="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                </svg>
              </div>
              <div>
                <h4 className="text-sm font-medium text-white">50,000+ Member Scale</h4>
                <p className="text-xs text-slate-400 mt-1">Built for mega church operations</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-blue-600/20 flex items-center justify-center flex-shrink-0">
                <svg className="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <h4 className="text-sm font-medium text-white">Enterprise Security</h4>
                <p className="text-xs text-slate-400 mt-1">SOC 2 compliant infrastructure</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-blue-600/20 flex items-center justify-center flex-shrink-0">
                <svg className="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h4 className="text-sm font-medium text-white">Multi-Channel Giving</h4>
                <p className="text-xs text-slate-400 mt-1">Card, ACH, PayPal, Crypto</p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="mt-auto pt-8">
          <div className="text-xs text-slate-500">
            Version 1.0.0 • Build 2026.02
          </div>
        </div>
      </div>

      {/* Right Panel - Login */}
      <div className="login-main">
        <div className="login-box" style={{ maxWidth: '400px' }}>
          <h1 className="login-title">Sign in to SAMSON</h1>
          <p className="login-subtitle">
            Access your church management platform
          </p>
          
          {/* Email/Password Form */}
          <form onSubmit={handleEmailLogin} className="space-y-4 mt-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Email address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="login-input"
                placeholder="you@church.org"
                data-testid="email-input"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="login-input pr-10"
                  placeholder="••••••••"
                  data-testid="password-input"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full"
              data-testid="login-submit-btn"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Signing in...
                </>
              ) : (
                'Sign In →'
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="login-divider">
            <span>or</span>
          </div>

          {/* Google OAuth */}
          <button 
            onClick={handleGoogleLogin}
            className="btn-google"
            data-testid="google-login-btn"
          >
            <GoogleIcon />
            Continue with Google
          </button>

          {/* Demo Credentials Box */}
          <div className="demo-credentials-box" data-testid="demo-credentials-box">
            <div className="demo-credentials-label">
              <span className="demo-key-icon">🔑</span>
              Demo Accounts (Password: Demo2026!)
            </div>
            
            {/* Platform Admin - God Mode */}
            <div className="demo-credential-row">
              <div className="demo-credential-info">
                <span className="demo-role" style={{color: '#8b5cf6', minWidth: '95px'}}>Platform:</span>
                <code className="demo-creds" onClick={() => {
                  setEmail('admin@samson.ai');
                  setPassword('Demo2026!');
                }}>
                  admin@samson.ai
                </code>
              </div>
            </div>
            
            {/* Church Admins */}
            <div className="demo-credential-row">
              <div className="demo-credential-info">
                <span className="demo-role">Abundant:</span>
                <code className="demo-creds" onClick={() => fillCredentials('admin')}>
                  admin@abundant.church
                </code>
              </div>
              <button 
                onClick={() => copyCredentials('admin')}
                className="demo-copy-btn"
                title="Copy credentials"
              >
                {copiedAdmin ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
            
            <div className="demo-credential-row">
              <div className="demo-credential-info">
                <span className="demo-role" style={{color: '#10b981'}}>CityReach:</span>
                <code className="demo-creds" onClick={() => {
                  setEmail('admin@cityreach.church');
                  setPassword('Demo2026!');
                }}>
                  admin@cityreach.church
                </code>
              </div>
            </div>

            <div className="demo-credential-row">
              <div className="demo-credential-info">
                <span className="demo-role" style={{color: '#7c3aed'}}>Potter's:</span>
                <code className="demo-creds" onClick={() => {
                  setEmail('admin@pottershouse.church');
                  setPassword('Demo2026!');
                }}>
                  admin@pottershouse.church
                </code>
              </div>
            </div>

            {/* Member Account - Maria */}
            <div className="demo-credentials-divider">
              <span>Member Portal</span>
            </div>
            
            <div className="demo-credential-row">
              <div className="demo-credential-info">
                <span className="demo-role" style={{color: '#f59e0b', minWidth: '95px'}}>Maria:</span>
                <code className="demo-creds" onClick={() => {
                  setEmail('member@abundant.church');
                  setPassword('Demo2026!');
                }}>
                  member@abundant.church
                </code>
              </div>
              <button 
                onClick={() => copyCredentials('member')}
                className="demo-copy-btn"
                title="Copy credentials"
              >
                {copiedMember ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
            
            <div className="demo-credential-row">
              <div className="demo-credential-info">
                <span className="demo-role" style={{color: '#10b981', minWidth: '95px'}}>John:</span>
                <code className="demo-creds" onClick={() => {
                  setEmail('member@cityreach.church');
                  setPassword('Demo2026!');
                }}>
                  member@cityreach.church
                </code>
              </div>
            </div>
          </div>
          
          <div className="login-footer">
            Don't have an account? <Link to="/signup" className="text-blue-600 hover:underline">Create account →</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
