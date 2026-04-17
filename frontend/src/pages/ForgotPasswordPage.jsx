import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Loader2, Mail, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) { toast.error('Please enter your email'); return; }
    setLoading(true);
    try {
      const res = await fetch(window.location.origin + '/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      if (res.ok) {
        setSent(true);
      } else {
        // Always show success to prevent email enumeration
        setSent(true);
      }
    } catch {
      setSent(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }} data-testid="forgot-password-page">
      <div style={{ width: '100%', maxWidth: 400 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, justifyContent: 'center', marginBottom: 40 }}>
          <span style={{ fontSize: 20, fontWeight: 200, letterSpacing: 6, color: '#fff' }}>SOLOMON</span>
          <span style={{ fontSize: 20, fontWeight: 700, color: '#3b82f6' }}>AI</span>
        </div>

        <div style={{ background: '#fff', borderRadius: 16, padding: 32, boxShadow: '0 25px 50px rgba(0,0,0,0.25)' }}>
          {sent ? (
            <div style={{ textAlign: 'center' }}>
              <div style={{ width: 56, height: 56, borderRadius: '50%', background: '#dcfce7', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                <CheckCircle style={{ width: 28, height: 28, color: '#16a34a' }} />
              </div>
              <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>Check Your Email</h2>
              <p style={{ fontSize: 14, color: '#64748b', lineHeight: 1.6, margin: '0 0 24px 0' }}>
                If an account exists for <strong>{email}</strong>, we've sent password reset instructions.
              </p>
              <Link to="/login" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: '#3b82f6', fontSize: 14, fontWeight: 600, textDecoration: 'none' }} data-testid="back-to-login">
                <ArrowLeft style={{ width: 16, height: 16 }} /> Back to Sign In
              </Link>
            </div>
          ) : (
            <>
              <div style={{ textAlign: 'center', marginBottom: 24 }}>
                <div style={{ width: 48, height: 48, borderRadius: '50%', background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
                  <Mail style={{ width: 24, height: 24, color: '#3b82f6' }} />
                </div>
                <h2 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a', margin: '0 0 6px 0' }}>Reset Password</h2>
                <p style={{ fontSize: 14, color: '#64748b', margin: 0 }}>Enter your email and we'll send reset instructions</p>
              </div>
              <form onSubmit={handleSubmit}>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="Email address"
                  autoComplete="off"
                  style={{ width: '100%', padding: '12px 16px', border: '1px solid #d1d5db', borderRadius: 10, fontSize: 15, outline: 'none', marginBottom: 16, boxSizing: 'border-box' }}
                  data-testid="forgot-email-input"
                />
                <button
                  type="submit"
                  disabled={loading}
                  style={{ width: '100%', padding: '12px 24px', background: loading ? '#94a3b8' : '#3b82f6', color: '#fff', border: 'none', borderRadius: 10, fontSize: 15, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
                  data-testid="forgot-submit-btn"
                >
                  {loading ? <Loader2 style={{ width: 18, height: 18, animation: 'spin 1s linear infinite' }} /> : 'Send Reset Link'}
                </button>
              </form>
              <div style={{ textAlign: 'center', marginTop: 16 }}>
                <Link to="/login" style={{ color: '#64748b', fontSize: 13, textDecoration: 'none' }} data-testid="forgot-back-link">
                  <ArrowLeft style={{ width: 14, height: 14, display: 'inline', verticalAlign: 'middle', marginRight: 4 }} />
                  Back to Sign In
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
