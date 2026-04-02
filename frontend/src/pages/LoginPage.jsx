import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

// Google SVG Icon
export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleEmailLogin = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Please enter email and password');
      return;
    }

    setIsLoading(true);
    try {
      // Use window.location.origin to guarantee same-origin (no CORS issues)
      const loginUrl = window.location.origin + '/api/auth/login';
      
      const response = await fetch(loginUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        let msg = 'Invalid email or password';
        try { const err = await response.json(); msg = err.detail || msg; } catch (_) {}
        throw new Error(msg);
      }

      const data = await response.json();

      // Store session
      if (data.session_token) {
        sessionStorage.setItem('session_token', data.session_token);
        sessionStorage.setItem('user_data', JSON.stringify(data));
        // Track login count for welcome message limiting
        const countKey = `solomon_login_count_${data.role === 'member' ? 'member' : 'church_admin'}`;
        const prevCount = parseInt(sessionStorage.getItem(countKey) || '0', 10);
        sessionStorage.setItem(countKey, String(prevCount + 1));
      }
      
      // Route based on role
      if (data.role === 'member') {
        navigate('/portal', { state: { user: data } });
      } else if (data.role === 'platform_admin') {
        navigate('/platform', { state: { user: data } });
      } else {
        navigate('/dashboard', { state: { user: data } });
      }
      
      toast.success(`Welcome, ${data.name}!`);
    } catch (error) {
      toast.error(error.message || 'Login failed — please try again');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="solomon-login" data-testid="login-page">
      {/* Full-screen centered layout */}
      <div className="solomon-login-container">
        
        {/* Logo */}
        <div className="solomon-logo">
          <span className="solomon-logo-text">SOLOMON</span>
          <span className="solomon-logo-ai">AI</span>
        </div>

        {/* Tagline */}
        <p style={{ fontSize: 13, color: '#64748b', marginBottom: 32, letterSpacing: '0.02em' }}>Your church. Elevated.</p>

        {/* Login Card */}
        <div className="solomon-login-card">
          
          {/* Email/Password Form */}
          <form onSubmit={handleEmailLogin} className="solomon-form">
            <div className="solomon-input-group">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="solomon-input"
                placeholder="Email"
                data-testid="email-input"
              />
            </div>
            
            <div className="solomon-input-group">
              <div className="solomon-password-wrapper">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="solomon-input"
                  placeholder="Password"
                  data-testid="password-input"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="solomon-password-toggle"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="solomon-submit-btn"
              data-testid="login-submit-btn"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                'Sign In'
              )}
            </button>
          </form>

        </div>

        {/* Footer */}
        <div className="solomon-footer">
          <div style={{ fontSize: 12, color: '#334155', marginTop: 24 }}>
            <span>&copy; 2026 Solomon AI</span>
            <span style={{ margin: '0 8px', color: '#475569' }}>&middot;</span>
            <span style={{ color: '#475569' }}>Privacy</span>
            <span style={{ margin: '0 8px', color: '#475569' }}>&middot;</span>
            <span style={{ color: '#475569' }}>Terms</span>
          </div>
        </div>

      </div>

      <style>{`
        .solomon-login {
          min-height: 100vh;
          width: 100%;
          background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
        }

        .solomon-login-container {
          width: 100%;
          max-width: 380px;
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .solomon-logo {
          display: flex;
          align-items: baseline;
          gap: 8px;
          margin-bottom: 48px;
        }

        .solomon-logo-text {
          font-family: 'Inter', -apple-system, sans-serif;
          font-size: 28px;
          font-weight: 200;
          letter-spacing: 8px;
          color: #ffffff;
        }

        .solomon-logo-ai {
          font-family: 'Inter', -apple-system, sans-serif;
          font-size: 14px;
          font-weight: 500;
          letter-spacing: 2px;
          color: #3b82f6;
        }

        .solomon-login-card {
          width: 100%;
        }

        .solomon-form {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .solomon-input-group {
          width: 100%;
        }

        .solomon-input {
          width: 100%;
          height: 52px;
          padding: 0 20px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          color: #ffffff;
          font-size: 15px;
          font-weight: 300;
          letter-spacing: 0.3px;
          transition: all 0.2s ease;
          outline: none;
        }

        .solomon-input::placeholder {
          color: rgba(255, 255, 255, 0.35);
          font-weight: 300;
        }

        .solomon-input:focus {
          border-color: rgba(59, 130, 246, 0.5);
          background: rgba(255, 255, 255, 0.08);
        }

        .solomon-password-wrapper {
          position: relative;
          width: 100%;
        }

        .solomon-password-wrapper .solomon-input {
          padding-right: 48px;
        }

        .solomon-password-toggle {
          position: absolute;
          right: 16px;
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: none;
          color: rgba(255, 255, 255, 0.4);
          cursor: pointer;
          padding: 4px;
          transition: color 0.2s ease;
          z-index: 2;
          display: flex;
          align-items: center;
        }

        .solomon-password-toggle:hover {
          color: rgba(255, 255, 255, 0.7);
        }

        .solomon-submit-btn {
          width: 100%;
          height: 52px;
          background: #3b82f6;
          border: none;
          border-radius: 8px;
          color: #ffffff;
          font-size: 15px;
          font-weight: 400;
          letter-spacing: 0.5px;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-top: 8px;
        }

        .solomon-submit-btn:hover {
          background: #2563eb;
        }

        .solomon-submit-btn:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .solomon-divider {
          display: flex;
          align-items: center;
          gap: 16px;
          margin: 28px 0;
        }

        .solomon-divider::before,
        .solomon-divider::after {
          content: '';
          flex: 1;
          height: 1px;
          background: rgba(255, 255, 255, 0.1);
        }

        .solomon-divider span {
          color: rgba(255, 255, 255, 0.35);
          font-size: 12px;
          font-weight: 300;
          letter-spacing: 1px;
          text-transform: uppercase;
        }

        .solomon-google-btn {
          width: 100%;
          height: 52px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          color: #ffffff;
          font-size: 15px;
          font-weight: 300;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
        }

        .solomon-google-btn:hover {
          background: rgba(255, 255, 255, 0.08);
          border-color: rgba(255, 255, 255, 0.15);
        }

        .solomon-footer {
          margin-top: 40px;
        }

        .solomon-footer-link {
          color: rgba(255, 255, 255, 0.4);
          font-size: 13px;
          font-weight: 300;
          letter-spacing: 0.5px;
          text-decoration: none;
          transition: color 0.2s ease;
        }

        .solomon-footer-link:hover {
          color: rgba(255, 255, 255, 0.7);
        }
      `}</style>
    </div>
  );
}
