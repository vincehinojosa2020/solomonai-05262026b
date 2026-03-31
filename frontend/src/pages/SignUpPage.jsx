import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Check, ArrowRight, ArrowLeft, Loader2, Eye, EyeOff } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

const STEPS = ['Your Church', 'Your Account', 'Launch'];

const memberCounts = ['Under 200', '200-1,000', '1,000-5,000', '5,000-20,000', '20,000+'];
const roles = ['Lead Pastor', 'Executive Pastor', 'Church Administrator', 'IT/Tech Director', 'Other'];

export default function SignUpPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({
    church_name: '', city: '', state: '', denomination: '', member_count: '', referral: '',
    first_name: '', last_name: '', email: '', role_title: '', password: '', confirm: ''
  });

  const set = (key) => (e) => setForm(prev => ({ ...prev, [key]: e.target.value }));
  const setCount = (val) => setForm(prev => ({ ...prev, member_count: val }));

  const canAdvance = () => {
    if (step === 0) return form.church_name && form.city && form.state;
    if (step === 1) return form.first_name && form.email && form.password && form.password === form.confirm && form.password.length >= 8;
    return true;
  };

  const handleLaunch = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/auth/register-church`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      });
      if (res.ok) {
        const data = await res.json();
        sessionStorage.setItem('session_token', data.token);
        sessionStorage.setItem('user_data', JSON.stringify(data));
        toast.success('Welcome to Solomon AI!');
        navigate('/dashboard', { state: { user: data } });
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Registration failed');
      }
    } catch { toast.error('Registration failed'); }
    finally { setLoading(false); }
  };

  const inputStyle = { width: '100%', padding: '12px 16px', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 10, fontSize: 14, color: '#fff', background: 'rgba(30,41,59,0.6)', outline: 'none' };
  const labelStyle = { display: 'block', fontSize: 13, fontWeight: 600, color: '#94a3b8', marginBottom: 6 };

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, fontFamily: "'Inter',-apple-system,sans-serif" }} data-testid="signup-page">
      <div style={{ width: '100%', maxWidth: 480 }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <Link to="/" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 22, fontWeight: 200, letterSpacing: 6, color: '#fff' }}>SOLOMON</span>
            <span style={{ fontSize: 22, fontWeight: 700, color: '#3b82f6' }}>AI</span>
          </Link>
          <p style={{ fontSize: 13, color: '#64748b', marginTop: 8 }}>Start your 30-day free trial</p>
        </div>

        {/* Steps */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 28, justifyContent: 'center' }}>
          {STEPS.map((label, idx) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 12, fontWeight: 700, transition: 'all 0.2s',
                background: idx < step ? '#3b82f6' : idx === step ? '#fff' : 'rgba(51,65,85,0.5)',
                color: idx < step ? '#fff' : idx === step ? '#0f172a' : '#64748b'
              }}>{idx < step ? <Check style={{ width: 14, height: 14 }} /> : idx + 1}</div>
              <span style={{ fontSize: 12, fontWeight: 600, color: idx <= step ? '#fff' : '#64748b' }}>{label}</span>
              {idx < STEPS.length - 1 && <div style={{ width: 32, height: 1, background: idx < step ? '#3b82f6' : 'rgba(51,65,85,0.5)' }} />}
            </div>
          ))}
        </div>

        {/* Card */}
        <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 16, padding: '32px 28px', backdropFilter: 'blur(8px)' }}>
          {/* Step 0: Church Info */}
          {step === 0 && (
            <div data-testid="signup-step-church">
              <h2 style={{ fontSize: 20, fontWeight: 700, color: '#fff', margin: '0 0 4px 0' }}>Tell us about your church</h2>
              <p style={{ fontSize: 13, color: '#64748b', margin: '0 0 24px 0' }}>We'll set up your platform in seconds.</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div>
                  <label style={labelStyle}>Church name *</label>
                  <input value={form.church_name} onChange={set('church_name')} style={inputStyle} placeholder="e.g. Abundant Church" data-testid="signup-church-name" />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <label style={labelStyle}>City *</label>
                    <input value={form.city} onChange={set('city')} style={inputStyle} placeholder="Charlotte" data-testid="signup-city" />
                  </div>
                  <div>
                    <label style={labelStyle}>State *</label>
                    <input value={form.state} onChange={set('state')} style={inputStyle} placeholder="NC" data-testid="signup-state" />
                  </div>
                </div>
                <div>
                  <label style={labelStyle}>Denomination (optional)</label>
                  <select value={form.denomination} onChange={set('denomination')} style={inputStyle} data-testid="signup-denomination">
                    <option value="">Select...</option>
                    <option>Non-denominational</option><option>Baptist</option><option>Methodist</option><option>Pentecostal</option><option>Presbyterian</option><option>Catholic</option><option>Lutheran</option><option>Other</option>
                  </select>
                </div>
                <div>
                  <label style={labelStyle}>Approximate member count</label>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {memberCounts.map(c => (
                      <button type="button" key={c} onClick={() => setCount(c)} style={{
                        padding: '8px 14px', borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: 'pointer',
                        background: form.member_count === c ? '#3b82f6' : 'rgba(51,65,85,0.5)',
                        color: '#fff', border: 'none', transition: 'all 0.15s'
                      }} data-testid={`signup-count-${c.replace(/[^a-zA-Z0-9]/g, '')}`}>{c}</button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 1: Account */}
          {step === 1 && (
            <div data-testid="signup-step-account">
              <h2 style={{ fontSize: 20, fontWeight: 700, color: '#fff', margin: '0 0 4px 0' }}>Create your account</h2>
              <p style={{ fontSize: 13, color: '#64748b', margin: '0 0 24px 0' }}>You'll be the admin for {form.church_name}.</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <label style={labelStyle}>First name *</label>
                    <input value={form.first_name} onChange={set('first_name')} style={inputStyle} data-testid="signup-first-name" />
                  </div>
                  <div>
                    <label style={labelStyle}>Last name</label>
                    <input value={form.last_name} onChange={set('last_name')} style={inputStyle} data-testid="signup-last-name" />
                  </div>
                </div>
                <div>
                  <label style={labelStyle}>Email *</label>
                  <input type="email" value={form.email} onChange={set('email')} style={inputStyle} data-testid="signup-email" />
                </div>
                <div>
                  <label style={labelStyle}>Your role</label>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {roles.map(r => (
                      <button type="button" key={r} onClick={() => setForm(prev => ({ ...prev, role_title: r }))} style={{
                        padding: '8px 12px', borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: 'pointer',
                        background: form.role_title === r ? '#3b82f6' : 'rgba(51,65,85,0.5)',
                        color: '#fff', border: 'none'
                      }}>{r}</button>
                    ))}
                  </div>
                </div>
                <div>
                  <label style={labelStyle}>Password *</label>
                  <div style={{ position: 'relative' }}>
                    <input type={showPassword ? 'text' : 'password'} value={form.password} onChange={set('password')} style={inputStyle} data-testid="signup-password" />
                    <button type="button" onClick={() => setShowPassword(!showPassword)} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}>
                      {showPassword ? <EyeOff style={{ width: 16, height: 16 }} /> : <Eye style={{ width: 16, height: 16 }} />}
                    </button>
                  </div>
                  {form.password && form.password.length < 8 && <p style={{ fontSize: 11, color: '#ef4444', marginTop: 4 }}>Must be at least 8 characters</p>}
                </div>
                <div>
                  <label style={labelStyle}>Confirm password *</label>
                  <input type="password" value={form.confirm} onChange={set('confirm')} style={inputStyle} data-testid="signup-confirm" />
                  {form.confirm && form.password !== form.confirm && <p style={{ fontSize: 11, color: '#ef4444', marginTop: 4 }}>Passwords don't match</p>}
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Summary & Launch */}
          {step === 2 && (
            <div data-testid="signup-step-launch" style={{ textAlign: 'center' }}>
              <h2 style={{ fontSize: 20, fontWeight: 700, color: '#fff', margin: '0 0 4px 0' }}>You're almost ready</h2>
              <p style={{ fontSize: 13, color: '#64748b', margin: '0 0 24px 0' }}>Review and launch your Solomon AI platform.</p>
              <div style={{ background: 'rgba(30,41,59,0.8)', borderRadius: 12, padding: 24, textAlign: 'left', marginBottom: 24 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(51,65,85,0.4)' }}>
                  <span style={{ fontSize: 13, color: '#94a3b8' }}>Church</span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>{form.church_name}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(51,65,85,0.4)' }}>
                  <span style={{ fontSize: 13, color: '#94a3b8' }}>Location</span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>{form.city}, {form.state}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(51,65,85,0.4)' }}>
                  <span style={{ fontSize: 13, color: '#94a3b8' }}>Admin</span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>{form.first_name} {form.last_name}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(51,65,85,0.4)' }}>
                  <span style={{ fontSize: 13, color: '#94a3b8' }}>Email</span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#fff' }}>{form.email}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0' }}>
                  <span style={{ fontSize: 13, color: '#94a3b8' }}>Plan</span>
                  <span style={{ fontSize: 13, fontWeight: 700, color: '#3b82f6' }}>Growth — 30-day free trial</span>
                </div>
              </div>
              <p style={{ fontSize: 12, color: '#64748b', marginBottom: 16 }}>We'll import your member list in Week 1.</p>
            </div>
          )}

          {/* Navigation */}
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 28 }}>
            {step > 0 ? (
              <button onClick={() => setStep(s => s - 1)} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '12px 20px', background: 'none', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 10, color: '#94a3b8', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>
                <ArrowLeft style={{ width: 16, height: 16 }} /> Back
              </button>
            ) : <div />}
            {step < 2 ? (
              <button onClick={() => canAdvance() && setStep(s => s + 1)} disabled={!canAdvance()} style={{
                display: 'flex', alignItems: 'center', gap: 6, padding: '12px 24px', background: canAdvance() ? '#3b82f6' : 'rgba(59,130,246,0.3)',
                border: 'none', borderRadius: 10, color: '#fff', fontSize: 14, fontWeight: 700, cursor: canAdvance() ? 'pointer' : 'default'
              }} data-testid="signup-next-btn">
                Continue <ArrowRight style={{ width: 16, height: 16 }} />
              </button>
            ) : (
              <button onClick={handleLaunch} disabled={loading} style={{
                display: 'flex', alignItems: 'center', gap: 8, padding: '14px 28px', background: '#f59e0b',
                border: 'none', borderRadius: 10, color: '#fff', fontSize: 15, fontWeight: 800, cursor: 'pointer'
              }} data-testid="signup-launch-btn">
                {loading ? <Loader2 style={{ width: 18, height: 18, animation: 'spin 0.8s linear infinite' }} /> : null}
                Launch Solomon AI <ArrowRight style={{ width: 18, height: 18 }} />
              </button>
            )}
          </div>
        </div>

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: 20 }}>
          <p style={{ fontSize: 13, color: '#475569' }}>
            Already have an account? <Link to="/login" style={{ color: '#3b82f6', textDecoration: 'none', fontWeight: 600 }}>Sign In</Link>
          </p>
        </div>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  );
}
