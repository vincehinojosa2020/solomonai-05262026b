import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Check, ArrowLeft } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

export default function DemoPage() {
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    first_name: '', last_name: '', church_name: '', email: '', phone: '',
    member_count: '', interests: []
  });

  const interestOptions = [
    'Replacing Planning Center', 'Reducing giving fees', 'Kids Check-In',
    'Multi-campus management', 'AI assistant', 'Becoming a Solomon Pay early adopter'
  ];

  const toggleInterest = (interest) => {
    setForm(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.first_name || !form.church_name || !form.email) {
      toast.error('Please fill in all required fields');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/demo-requests`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      });
      if (res.ok) { setSubmitted(true); }
      else { const err = await res.json(); toast.error(err.detail || 'Failed to submit'); }
    } catch { toast.error('Failed to submit request'); }
    finally { setLoading(false); }
  };

  const set = (key) => (e) => setForm(prev => ({ ...prev, [key]: e.target.value }));

  const inputStyle = { width: '100%', padding: '12px 16px', border: '1px solid #e5e7eb', borderRadius: 10, fontSize: 14, color: '#111827', background: '#fff' };
  const labelStyle = { display: 'block', fontSize: 13, fontWeight: 600, color: '#374151', marginBottom: 6 };

  return (
    <div style={{ minHeight: '100vh', fontFamily: "'Inter',-apple-system,sans-serif" }} data-testid="demo-page">
      {/* Header */}
      <div style={{ background: '#0f172a', padding: '100px 32px 60px', textAlign: 'center' }}>
        <Link to="/" style={{ position: 'absolute', top: 20, left: 32, display: 'flex', alignItems: 'center', gap: 6, color: '#94a3b8', textDecoration: 'none', fontSize: 14, fontWeight: 500 }}>
          <ArrowLeft style={{ width: 16, height: 16 }} /> Back
        </Link>
        <h1 style={{ fontSize: 'clamp(32px, 4vw, 48px)', fontWeight: 800, color: '#fff', margin: '0 0 12px 0', letterSpacing: '-0.02em' }}>See Solomon AI in action.</h1>
        <p style={{ fontSize: 18, color: '#94a3b8', margin: 0 }}>We'll show you everything in 20 minutes.</p>
      </div>

      {/* Form */}
      <div style={{ maxWidth: 580, margin: '-30px auto 60px', padding: '0 24px' }}>
        {submitted ? (
          <div style={{ background: '#fff', borderRadius: 16, padding: 48, border: '1px solid #e5e7eb', textAlign: 'center', boxShadow: '0 4px 24px rgba(0,0,0,0.06)' }} data-testid="demo-success">
            <div style={{ width: 64, height: 64, borderRadius: '50%', background: '#ecfdf5', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
              <Check style={{ width: 32, height: 32, color: '#10b981' }} />
            </div>
            <h2 style={{ fontSize: 24, fontWeight: 700, color: '#111827', margin: '0 0 8px 0' }}>We'll be in touch within 24 hours.</h2>
            <p style={{ fontSize: 15, color: '#6b7280', margin: '0 0 32px 0' }}>In the meantime, explore the live demo:</p>
            <Link to="/login" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '14px 28px', background: '#0f172a', color: '#fff', borderRadius: 10, fontSize: 15, fontWeight: 700, textDecoration: 'none' }} data-testid="try-demo-btn">
              Try Live Demo <ArrowRight style={{ width: 16, height: 16 }} />
            </Link>
            <p style={{ fontSize: 12, color: '#9ca3af', marginTop: 12 }}>Login: member@abundant.church / Demo2026!</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ background: '#fff', borderRadius: 16, padding: '36px 32px', border: '1px solid #e5e7eb', boxShadow: '0 4px 24px rgba(0,0,0,0.06)' }} data-testid="demo-form">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
              <div>
                <label style={labelStyle}>First name *</label>
                <input value={form.first_name} onChange={set('first_name')} style={inputStyle} required data-testid="demo-first-name" />
              </div>
              <div>
                <label style={labelStyle}>Last name</label>
                <input value={form.last_name} onChange={set('last_name')} style={inputStyle} data-testid="demo-last-name" />
              </div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={labelStyle}>Church name *</label>
              <input value={form.church_name} onChange={set('church_name')} style={inputStyle} required data-testid="demo-church" />
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={labelStyle}>Email *</label>
              <input type="email" value={form.email} onChange={set('email')} style={inputStyle} required data-testid="demo-email" />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
              <div>
                <label style={labelStyle}>Phone (optional)</label>
                <input value={form.phone} onChange={set('phone')} style={inputStyle} data-testid="demo-phone" />
              </div>
              <div>
                <label style={labelStyle}>Member count</label>
                <select value={form.member_count} onChange={set('member_count')} style={inputStyle} data-testid="demo-members">
                  <option value="">Select...</option>
                  <option>Under 200</option><option>200-1,000</option><option>1,000-5,000</option><option>5,000-20,000</option><option>20,000+</option>
                </select>
              </div>
            </div>
            <div style={{ marginBottom: 24 }}>
              <label style={labelStyle}>What are you most interested in?</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {interestOptions.map(opt => (
                  <button type="button" key={opt} onClick={() => toggleInterest(opt)} style={{
                    padding: '8px 14px', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer', transition: 'all 0.15s',
                    background: form.interests.includes(opt) ? '#0f172a' : '#f8fafc',
                    color: form.interests.includes(opt) ? '#fff' : '#374151',
                    border: `1px solid ${form.interests.includes(opt) ? '#0f172a' : '#e5e7eb'}`
                  }}>{opt}</button>
                ))}
              </div>
            </div>
            <button type="submit" disabled={loading} style={{ width: '100%', padding: '14px 0', background: '#0f172a', color: '#fff', border: 'none', borderRadius: 10, fontSize: 15, fontWeight: 700, cursor: 'pointer' }} data-testid="demo-submit-btn">
              {loading ? 'Submitting...' : 'Request Demo'} {!loading && <ArrowRight style={{ width: 14, height: 14, display: 'inline', verticalAlign: 'middle' }} />}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
