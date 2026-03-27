import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, Check, X, Tv, Baby, Heart, Users, Calendar, Zap, Play, DollarSign, Menu, Loader2 } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

const S = {
  navy: '#0f172a', navyLight: '#1e293b', blue: '#3b82f6', gold: '#f59e0b',
  grayLight: '#f8fafc', white: '#ffffff', textDark: '#0f172a', textGray: '#6b7280', border: '#e5e7eb',
  textMuted: '#94a3b8',
};

export default function LandingPage() {
  const navigate = useNavigate();
  const [waitlistEmail, setWaitlistEmail] = useState('');
  const [waitlistChurch, setWaitlistChurch] = useState('');
  const [waitlistSent, setWaitlistSent] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showLeadForm, setShowLeadForm] = useState(false);
  const [leadSubmitted, setLeadSubmitted] = useState(false);
  const [leadLoading, setLeadLoading] = useState(false);
  const [leadData, setLeadData] = useState({
    church_name: '', name: '', email: '', phone: '', current_software: '', church_size: ''
  });

  const submitWaitlist = async () => {
    if (!waitlistEmail) return;
    try {
      await fetch(`${API_URL}/waitlist/solomon-pay`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: waitlistEmail, church_name: waitlistChurch })
      });
      setWaitlistSent(true);
      toast.success("You're on the waitlist!");
    } catch { toast.error('Failed to join waitlist'); }
  };

  const submitLeadForm = async (e) => {
    e.preventDefault();
    if (!leadData.church_name || !leadData.name || !leadData.email) return;
    setLeadLoading(true);
    try {
      await fetch(`${API_URL}/leads/capture`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(leadData)
      });
      setLeadSubmitted(true);
    } catch { toast.error('Something went wrong. Please try again.'); }
    finally { setLeadLoading(false); }
  };

  const openLeadForm = (e) => { e?.preventDefault(); setShowLeadForm(true); };

  return (
    <div style={{ background: S.white, color: S.textDark, fontFamily: "'Inter',-apple-system,BlinkMacSystemFont,sans-serif" }} data-testid="landing-page">
      <style>{`
        @media (max-width: 768px) {
          .lp-nav-desktop { display: none !important; }
          .lp-nav-mobile-toggle { display: flex !important; }
          .lp-grid-3 { grid-template-columns: 1fr !important; }
          .lp-grid-4 { grid-template-columns: 1fr !important; }
          .lp-stats-grid { grid-template-columns: repeat(3, 1fr) !important; gap: 16px !important; }
          .lp-stats-grid p:first-child { font-size: 28px !important; }
          .lp-hero-btns { flex-direction: column !important; align-items: center !important; }
          .lp-hero-btns a { width: 100% !important; max-width: 300px !important; justify-content: center !important; }
          .lp-footer-grid { grid-template-columns: 1fr 1fr !important; gap: 24px !important; }
          .lp-footer-bottom { flex-direction: column !important; gap: 8px !important; text-align: center !important; }
          .lp-table-wrap { overflow-x: auto !important; }
          .lp-waitlist-row { flex-direction: column !important; }
          .lp-waitlist-row input, .lp-waitlist-row button { width: 100% !important; }
          .lp-pricing-grid { grid-template-columns: 1fr !important; max-width: 400px !important; margin-left: auto !important; margin-right: auto !important; }
        }
        @media (min-width: 769px) {
          .lp-nav-mobile-toggle { display: none !important; }
          .lp-mobile-menu { display: none !important; }
        }
        @media (max-width: 480px) {
          .lp-stats-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>

      {/* ── NAV ── */}
      <nav style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100, background: 'rgba(15,23,42,0.95)', backdropFilter: 'blur(12px)', borderBottom: '1px solid rgba(255,255,255,0.06)' }} data-testid="landing-header">
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px', height: 64, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'baseline', gap: 6 }} data-testid="landing-logo">
            <span style={{ fontSize: 18, fontWeight: 200, letterSpacing: 6, color: '#fff' }}>SOLOMON</span>
            <span style={{ fontSize: 18, fontWeight: 700, color: S.blue }}>AI</span>
          </Link>
          {/* Desktop nav */}
          <div className="lp-nav-desktop" style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
            <Link to="/pricing" style={{ fontSize: 14, fontWeight: 500, color: '#cbd5e1', textDecoration: 'none' }} data-testid="nav-pricing">Pricing</Link>
            <Link to="/demo" style={{ fontSize: 14, fontWeight: 500, color: '#cbd5e1', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 6 }} data-testid="nav-watch-demo">
              <Play style={{ width: 13, height: 13 }} /> Watch Demo
            </Link>
            <Link to="/login" style={{ padding: '8px 20px', fontSize: 14, fontWeight: 600, color: '#fff', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 8, textDecoration: 'none' }} data-testid="landing-login-btn">Login</Link>
          </div>
          {/* Mobile hamburger */}
          <button
            className="lp-nav-mobile-toggle"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            style={{ display: 'none', alignItems: 'center', justifyContent: 'center', background: 'none', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 8, padding: 8, cursor: 'pointer', color: '#fff' }}
            data-testid="mobile-menu-toggle"
            aria-label="Menu"
          >
            <Menu style={{ width: 20, height: 20 }} />
          </button>
        </div>
        {/* Mobile dropdown */}
        {mobileMenuOpen && (
          <div className="lp-mobile-menu" style={{ background: 'rgba(15,23,42,0.98)', borderTop: '1px solid rgba(255,255,255,0.06)', padding: '16px 24px' }} data-testid="mobile-menu">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <Link to="/pricing" onClick={() => setMobileMenuOpen(false)} style={{ fontSize: 15, fontWeight: 500, color: '#cbd5e1', textDecoration: 'none', padding: '8px 0' }}>Pricing</Link>
              <Link to="/demo" onClick={() => setMobileMenuOpen(false)} style={{ fontSize: 15, fontWeight: 500, color: '#cbd5e1', textDecoration: 'none', padding: '8px 0', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Play style={{ width: 14, height: 14 }} /> Watch Demo
              </Link>
              <Link to="/login" onClick={() => setMobileMenuOpen(false)} style={{ fontSize: 15, fontWeight: 600, color: '#fff', textDecoration: 'none', padding: '10px 0', borderTop: '1px solid rgba(255,255,255,0.08)', marginTop: 4 }}>Login</Link>
            </div>
          </div>
        )}
      </nav>

      {/* ── HERO ── */}
      <section style={{ background: S.white, minHeight: '100vh', paddingTop: 120, paddingBottom: 80, display: 'flex', alignItems: 'center' }} data-testid="hero-section">
        <div style={{ maxWidth: 900, margin: '0 auto', padding: '0 32px', textAlign: 'center' }}>
          <h1 style={{ fontSize: 'clamp(44px, 6vw, 72px)', fontWeight: 800, color: S.textDark, lineHeight: 1.05, letterSpacing: '-0.04em', margin: '0 0 28px 0' }} data-testid="hero-headline">
            Your Church.<br />One App.<br />Zero Compromise.
          </h1>
          <p style={{ fontSize: 'clamp(17px, 1.8vw, 21px)', color: S.textGray, lineHeight: 1.65, maxWidth: 580, margin: '0 auto 44px auto' }} data-testid="hero-subtitle">
            From Sunday morning to Monday morning &mdash; everything your congregation needs, in the palm of their hand.
          </p>
          <div className="lp-hero-btns" style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button onClick={openLeadForm} style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '16px 36px', background: S.blue, color: '#fff', fontSize: 16, fontWeight: 700, borderRadius: 10, border: 'none', cursor: 'pointer', transition: 'transform 0.15s' }} data-testid="hero-cta-demo">
              Request a Demo <ArrowRight style={{ width: 18, height: 18 }} />
            </button>
            <Link to="/demo" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '16px 28px', border: `2px solid ${S.border}`, color: S.textDark, fontSize: 16, fontWeight: 600, borderRadius: 10, textDecoration: 'none' }} data-testid="hero-cta-watch">
              <Play style={{ width: 16, height: 16 }} /> Watch Demo
            </Link>
          </div>
        </div>
      </section>

      {/* ── STATS BAR ── */}
      <section style={{ background: S.white, padding: '48px 32px', borderTop: `1px solid ${S.border}`, borderBottom: `1px solid ${S.border}` }} data-testid="social-proof-section">
        <div style={{ maxWidth: 800, margin: '0 auto', textAlign: 'center' }}>
          <p style={{ fontSize: 12, color: S.textGray, textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600, marginBottom: 28 }}>Powering Churches Across America</p>
          <div className="lp-stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 32 }}>
            {[
              { num: '64,500', label: 'Members Engaged' },
              { num: '$151M+', label: 'Given in 2026' },
              { num: '140+', label: 'Active Small Groups' },
            ].map(s => (
              <div key={s.label} data-testid={`stat-${s.label.toLowerCase().replace(/\s+/g, '-')}`}>
                <p style={{ fontSize: 40, fontWeight: 800, color: S.textDark, margin: 0, fontFamily: 'monospace', letterSpacing: '-0.03em' }}>{s.num}</p>
                <p style={{ fontSize: 14, fontWeight: 600, color: S.textGray, margin: '6px 0 0 0' }}>{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── THE PROBLEM ── */}
      <section style={{ background: S.grayLight, padding: '80px 32px' }} data-testid="problem-section">
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <p style={{ fontSize: 12, fontWeight: 700, color: S.blue, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12 }}>The Problem</p>
          <h2 style={{ fontSize: 'clamp(28px, 3vw, 40px)', fontWeight: 800, color: S.textDark, letterSpacing: '-0.02em', margin: '0 0 48px 0', lineHeight: 1.15 }}>
            Your church is paying too much<br />for too little.
          </h2>
          <div className="lp-grid-3" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
            {[
              { title: 'Too many bills', body: 'Planning Center: $300-$1,500/mo\nSecureGive: $99-$199/mo + 2% fees\nSermon platform: $50-$200/mo\nChurch app: $200-$500/mo', highlight: 'TOTAL: $700-$2,400/month for tools that don\'t talk to each other', color: '#ef4444' },
              { title: 'Too complex', body: 'Church Center is not your app. It says "Church Center" — not your church\'s name. Planning Center takes months to learn. Your staff dreads Sunday morning logistics.', highlight: '', color: '#f59e0b' },
              { title: 'Zero AI', body: 'Planning Center was built in 2006. Church Center has no AI assistant. No geofencing. No giving nudges. No war room. No cafe ordering. They\'re not building for 2026.', highlight: 'Solomon AI is.', color: '#8b5cf6' },
            ].map(card => (
              <div key={card.title} style={{ background: S.white, borderRadius: 16, padding: 28, border: `1px solid ${S.border}`, boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
                <h3 style={{ fontSize: 18, fontWeight: 700, color: S.textDark, margin: '0 0 12px 0' }}>{card.title}</h3>
                <p style={{ fontSize: 14, color: S.textGray, lineHeight: 1.7, margin: '0 0 12px 0', whiteSpace: 'pre-line' }}>{card.body}</p>
                {card.highlight && <p style={{ fontSize: 14, fontWeight: 700, color: card.color, margin: 0 }}>{card.highlight}</p>}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── THE SOLUTION — FEATURE CARDS ── */}
      <section style={{ background: S.white, padding: '80px 32px' }} data-testid="solution-section">
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <p style={{ fontSize: 12, fontWeight: 700, color: S.blue, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12 }}>Everything Your Church Needs</p>
          <h2 style={{ fontSize: 'clamp(28px, 3vw, 40px)', fontWeight: 800, color: S.textDark, letterSpacing: '-0.02em', margin: '0 0 48px 0', lineHeight: 1.15 }}>
            One platform. Every ministry.<br />Powered by AI.
          </h2>
          <div className="lp-grid-3" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
            {[
              { icon: Heart, title: 'Give', desc: 'One tap. Any fund. Any amount. Giving the way it was always meant to be.' },
              { icon: Tv, title: 'Watch', desc: "MasterClass-quality. Your pastor's best messages \u2014 always on, always available." },
              { icon: Baby, title: 'Check-In', desc: 'Sunday morning peace of mind. Check in. QR code. Done in 10 seconds.' },
              { icon: Users, title: 'Groups', desc: '140+ groups. One place to belong. Community starts here.' },
              { icon: Calendar, title: 'Events', desc: 'Every gathering. Every opportunity. Register in two taps.' },
              { icon: Zap, title: 'Ask Solomon', desc: "Ask anything. Get answers instantly. Your church's AI \u2014 always on duty." },
            ].map(f => (
              <div key={f.title} style={{ background: S.grayLight, borderRadius: 14, padding: 28, border: `1px solid ${S.border}` }} data-testid={`feature-card-${f.title.toLowerCase().replace(/\s+/g, '-')}`}>
                <f.icon style={{ width: 28, height: 28, color: S.blue, marginBottom: 16 }} />
                <h3 style={{ fontSize: 18, fontWeight: 700, color: S.textDark, margin: '0 0 8px 0' }}>{f.title}</h3>
                <p style={{ fontSize: 14, color: S.textGray, lineHeight: 1.6, margin: 0 }}>{f.desc}</p>
              </div>
            ))}
          </div>
          <p style={{ textAlign: 'center', fontSize: 15, color: S.textGray, fontWeight: 500, marginTop: 40 }} data-testid="trusted-line">
            Built for leaders. Designed for growth. Trusted by the church.
          </p>
        </div>
      </section>

      {/* ── WHY CHURCHES ARE SWITCHING ── */}
      <section style={{ background: S.grayLight, padding: '80px 32px' }} data-testid="comparison-section">
        <div style={{ maxWidth: 900, margin: '0 auto' }}>
          <p style={{ fontSize: 12, fontWeight: 700, color: S.blue, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12, textAlign: 'center' }}>How We Compare</p>
          <h2 style={{ fontSize: 'clamp(28px, 3vw, 36px)', fontWeight: 800, color: S.textDark, letterSpacing: '-0.02em', margin: '0 0 12px 0', textAlign: 'center', lineHeight: 1.15 }}>
            We respect the platforms that came before us.
          </h2>
          <p style={{ fontSize: 16, color: S.textGray, textAlign: 'center', maxWidth: 620, margin: '0 auto 40px auto', lineHeight: 1.6 }}>
            Planning Center and Church Center paved the way for church technology. Solomon AI is built for what comes next.
          </p>
          <div className="lp-table-wrap" style={{ background: S.white, borderRadius: 16, overflow: 'hidden', border: `1px solid ${S.border}`, boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr style={{ borderBottom: `2px solid ${S.border}` }}>
                  <th style={{ padding: '16px 20px', textAlign: 'left', fontWeight: 600, color: S.textGray }}>Capability</th>
                  <th style={{ padding: '16px 16px', textAlign: 'center', fontWeight: 700, color: S.blue }}>Solomon AI</th>
                  <th style={{ padding: '16px 16px', textAlign: 'center', fontWeight: 600, color: S.textGray }}>Planning Center<br /><span style={{ fontSize: 11, fontWeight: 400 }}>+ Church Center</span></th>
                </tr>
              </thead>
              <tbody>
                {[
                  ['Member Management', true, true],
                  ['Kids Check-In (QR)', true, true],
                  ['Small Groups', true, true],
                  ['Events & Registration', true, true],
                  ['Sermon Library', true, false],
                  ['Cafe & Merch Ordering', true, false],
                  ['AI Church Assistant', true, false],
                  ['Geofence Check-in', true, false],
                  ['Real-time War Room', true, false],
                  ['Multi-campus (1 bill)', true, false],
                  ['Flat Monthly Price', true, false],
                ].map(([feature, sol, pc], i) => (
                  <tr key={feature} style={{ borderBottom: `1px solid ${S.border}`, background: i % 2 === 0 ? S.white : S.grayLight }}>
                    <td style={{ padding: '12px 20px', color: S.textDark, fontWeight: 500 }}>{feature}</td>
                    <td style={{ padding: '12px 16px', textAlign: 'center' }}>{sol ? <Check style={{ width: 18, height: 18, color: '#22c55e', margin: '0 auto' }} /> : <X style={{ width: 18, height: 18, color: '#d1d5db', margin: '0 auto' }} />}</td>
                    <td style={{ padding: '12px 16px', textAlign: 'center' }}>{pc ? <Check style={{ width: 18, height: 18, color: '#22c55e', margin: '0 auto' }} /> : <X style={{ width: 18, height: 18, color: '#d1d5db', margin: '0 auto' }} />}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Honest note about giving */}
          <div style={{ background: S.white, border: `1px solid ${S.border}`, borderRadius: 12, padding: '24px 28px', marginTop: 24, display: 'flex', gap: 16, alignItems: 'flex-start' }}>
            <DollarSign style={{ width: 20, height: 20, color: S.gold, flexShrink: 0, marginTop: 2 }} />
            <div>
              <p style={{ fontSize: 14, fontWeight: 700, color: S.textDark, margin: '0 0 6px 0' }}>
                What about giving?
              </p>
              <p style={{ fontSize: 14, color: S.textGray, lineHeight: 1.6, margin: 0 }}>
                Today, Solomon AI works alongside your church's current giving provider &mdash; Pushpay, SecureGive, Tithe.ly, or whoever you trust.
                We're building <strong style={{ color: S.textDark }}>Solomon Pay</strong>, our own giving platform with the lowest transaction fees in the industry. It launches later this year. <a href="#" onClick={openLeadForm} style={{ color: S.blue, fontWeight: 600, textDecoration: 'none' }}>Request a demo</a> to learn more.
              </p>
            </div>
          </div>

          {/* Why switch card */}
          <div className="lp-grid-3" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginTop: 24 }}>
            {[
              { num: '1', title: 'One platform, not six', body: 'Stop paying for check-in, giving, groups, events, and sermons separately. Solomon AI replaces them all.' },
              { num: '2', title: 'Built for 2026, not 2006', body: 'AI assistant, geofencing, real-time analytics, cafe ordering. Features your current tools will never build.' },
              { num: '3', title: 'One bill, every campus', body: 'Planning Center charges per module per campus. Solomon AI covers every feature, every campus, one price.' },
            ].map(card => (
              <div key={card.num} style={{ background: S.white, borderRadius: 12, padding: '24px', border: `1px solid ${S.border}` }}>
                <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 800, color: S.blue, marginBottom: 12 }}>{card.num}</div>
                <h4 style={{ fontSize: 15, fontWeight: 700, color: S.textDark, margin: '0 0 6px 0' }}>{card.title}</h4>
                <p style={{ fontSize: 13, color: S.textGray, lineHeight: 1.6, margin: 0 }}>{card.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── PRICING ── */}
      <section style={{ background: S.white, padding: '80px 32px' }} data-testid="pricing-section">
        <div style={{ maxWidth: 1000, margin: '0 auto', textAlign: 'center' }}>
          <p style={{ fontSize: 12, fontWeight: 700, color: S.blue, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12 }}>Pricing</p>
          <h2 style={{ fontSize: 'clamp(28px, 3vw, 40px)', fontWeight: 800, color: S.textDark, letterSpacing: '-0.02em', margin: '0 0 8px 0' }}>Simple pricing. No surprises.</h2>
          <p style={{ fontSize: 16, color: S.textGray, margin: '0 0 48px 0' }}>One price. Every feature. All campuses included.</p>
          <div className="lp-pricing-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20, textAlign: 'left' }}>
            {[
              { name: 'Starter', price: '$499', period: '/mo', desc: 'Up to 500 members', features: ['All features included', '1 campus', 'Email support'], popular: false, cta: 'Get Started' },
              { name: 'Growth', price: '$1,499', period: '/mo', desc: 'Up to 5,000 members', features: ['All features included', 'Up to 3 campuses', 'Priority support', 'Onboarding included'], popular: true, cta: 'Get Started' },
              { name: 'Enterprise', price: '$2,999', period: '/mo', desc: 'Unlimited members', features: ['All features included', 'Unlimited campuses', 'Dedicated success manager', 'Custom integrations', 'SLA guarantee'], popular: false, cta: 'Contact Sales' },
            ].map(plan => (
              <div key={plan.name} style={{ background: S.white, borderRadius: 16, padding: 32, border: plan.popular ? `2px solid ${S.gold}` : `1px solid ${S.border}`, position: 'relative', boxShadow: plan.popular ? '0 4px 24px rgba(245,158,11,0.12)' : 'none' }}>
                {plan.popular && <div style={{ position: 'absolute', top: -14, left: '50%', transform: 'translateX(-50%)', padding: '4px 16px', background: S.gold, borderRadius: 100, fontSize: 11, fontWeight: 700, color: '#fff', letterSpacing: '0.04em' }}>MOST POPULAR</div>}
                <h3 style={{ fontSize: 20, fontWeight: 700, color: S.textDark, margin: '0 0 4px 0' }}>{plan.name}</h3>
                <p style={{ fontSize: 12, color: S.textGray, margin: '0 0 16px 0' }}>{plan.desc}</p>
                <div style={{ margin: '0 0 24px 0' }}>
                  <span style={{ fontSize: 40, fontWeight: 800, color: S.textDark }}>{plan.price}</span>
                  <span style={{ fontSize: 16, color: S.textGray }}>{plan.period}</span>
                </div>
                <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 28px 0' }}>
                  {plan.features.map(f => (
                    <li key={f} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: S.textGray, padding: '6px 0' }}>
                      <Check style={{ width: 16, height: 16, color: '#22c55e', flexShrink: 0 }} /> {f}
                    </li>
                  ))}
                </ul>
                <Link to={plan.cta === 'Contact Sales' ? '/demo' : '/signup'} style={{ display: 'block', textAlign: 'center', padding: '14px 0', background: plan.popular ? S.blue : S.navy, color: '#fff', borderRadius: 10, fontSize: 15, fontWeight: 700, textDecoration: 'none' }} data-testid={`pricing-cta-${plan.name.toLowerCase()}`}>
                  {plan.cta} <ArrowRight style={{ width: 14, height: 14, display: 'inline', verticalAlign: 'middle' }} />
                </Link>
              </div>
            ))}
          </div>

          {/* FAQ */}
          <div style={{ maxWidth: 700, margin: '60px auto 0', textAlign: 'left' }}>
            {[
              { q: 'Do you charge per campus?', a: "No. One account covers all your campuses. Three campuses, five campuses, ten campuses: one bill." },
              { q: 'Are there transaction fees on giving?', a: 'Currently we process through Stripe at standard rates. In 2026 we launch Solomon Pay — our own payment processor at lower rates than SecureGive, Pushpay, or Venmo.' },
              { q: 'How long does onboarding take?', a: 'Week 1: we import your member list from your current system (Excel, CSV, or Planning Center export). Week 2: staff training. Week 3: you\'re live.' },
            ].map(faq => (
              <div key={faq.q} style={{ padding: '20px 0', borderBottom: `1px solid ${S.border}` }}>
                <h4 style={{ fontSize: 15, fontWeight: 700, color: S.textDark, margin: '0 0 8px 0' }}>{faq.q}</h4>
                <p style={{ fontSize: 14, color: S.textGray, lineHeight: 1.6, margin: 0 }}>{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── THE VISION ── */}
      <section style={{ background: S.navy, padding: '80px 32px', color: '#fff' }} data-testid="vision-section">
        <div style={{ maxWidth: 800, margin: '0 auto', textAlign: 'center' }}>
          <p style={{ fontSize: 12, fontWeight: 700, color: S.gold, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12 }}>The Future</p>
          <h2 style={{ fontSize: 'clamp(28px, 3vw, 40px)', fontWeight: 800, letterSpacing: '-0.02em', margin: '0 0 56px 0', lineHeight: 1.15 }}>
            We're building the financial<br />infrastructure of the church.
          </h2>
          <div className="lp-grid-3" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24, textAlign: 'left' }}>
            {[
              { label: 'NOW', title: 'Church Management', desc: 'Replace Planning Center + Church Center + SecureGive in one platform.', status: 'Live' },
              { label: '2026', title: 'Solomon Pay', desc: 'Our own payment processor. Transaction fees lower than Venmo. Lower than Pushpay. Lower than anyone. Every dollar stays in ministry.', status: 'Coming' },
              { label: 'BEYOND', title: 'The Church OS', desc: 'Every API. Every integration. Every system a church uses — connected through Solomon AI. The operating system of the American church.', status: 'Vision' },
            ].map(item => (
              <div key={item.label} style={{ background: 'rgba(30,41,59,0.5)', border: '1px solid rgba(51,65,85,0.5)', borderRadius: 14, padding: 28 }}>
                <div style={{ display: 'inline-block', padding: '4px 12px', borderRadius: 6, fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 16, background: item.label === 'NOW' ? 'rgba(34,197,94,0.15)' : item.label === '2026' ? 'rgba(59,130,246,0.15)' : 'rgba(168,85,247,0.15)', color: item.label === 'NOW' ? '#4ade80' : item.label === '2026' ? '#60a5fa' : '#c084fc' }}>
                  {item.label} — {item.status}
                </div>
                <h3 style={{ fontSize: 18, fontWeight: 700, margin: '0 0 8px 0' }}>{item.title}</h3>
                <p style={{ fontSize: 14, color: S.textMuted, lineHeight: 1.6, margin: 0 }}>{item.desc}</p>
              </div>
            ))}
          </div>

          {/* Solomon Pay Waitlist */}
          <div style={{ marginTop: 48, padding: '28px 32px', background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 14 }} data-testid="waitlist-form">
            {waitlistSent ? (
              <p style={{ fontSize: 16, color: S.gold, fontWeight: 600 }}>You're on the Solomon Pay waitlist! We'll be in touch.</p>
            ) : (
              <>
                <p style={{ fontSize: 15, fontWeight: 700, color: S.gold, marginBottom: 16 }}>Join the waitlist for Solomon Pay</p>
                <div className="lp-waitlist-row" style={{ display: 'flex', gap: 8, maxWidth: 540, margin: '0 auto', flexWrap: 'wrap', justifyContent: 'center' }}>
                  <input value={waitlistEmail} onChange={e => setWaitlistEmail(e.target.value)} placeholder="Email" style={{ flex: '1 1 180px', minWidth: 160, padding: '12px 16px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(15,23,42,0.6)', color: '#fff', fontSize: 14 }} data-testid="waitlist-email" />
                  <input value={waitlistChurch} onChange={e => setWaitlistChurch(e.target.value)} placeholder="Church name" style={{ flex: '1 1 180px', minWidth: 160, padding: '12px 16px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(15,23,42,0.6)', color: '#fff', fontSize: 14 }} data-testid="waitlist-church" />
                  <button onClick={submitWaitlist} style={{ padding: '12px 24px', background: S.gold, color: '#fff', borderRadius: 8, border: 'none', fontWeight: 700, fontSize: 14, cursor: 'pointer', whiteSpace: 'nowrap', minWidth: 'auto' }} data-testid="waitlist-submit">Join Waitlist</button>
                </div>
              </>
            )}
          </div>
        </div>
      </section>

      {/* ── FINAL CTA ── */}
      <section style={{ background: `linear-gradient(135deg, ${S.navy} 0%, #1a2744 100%)`, padding: '80px 32px', textAlign: 'center' }} data-testid="final-cta-section">
        <div style={{ maxWidth: 700, margin: '0 auto' }}>
          <h2 style={{ fontSize: 'clamp(32px, 4vw, 48px)', fontWeight: 800, color: '#fff', letterSpacing: '-0.02em', lineHeight: 1.15, margin: '0 0 24px 0' }} data-testid="final-cta-headline">
            The future of your church<br />starts with one decision.
          </h2>
          <p style={{ fontSize: 16, color: '#94a3b8', lineHeight: 1.7, maxWidth: 540, margin: '0 auto 36px auto' }} data-testid="final-cta-sub">
            Join the churches that are giving more, growing faster, and leading with confidence. Solomon AI handles the platform. You handle the mission.
          </p>
          <button onClick={openLeadForm} style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '18px 40px', background: S.gold, color: '#fff', fontSize: 18, fontWeight: 800, borderRadius: 12, border: 'none', cursor: 'pointer' }} data-testid="final-cta-btn">
            Request a Demo <ArrowRight style={{ width: 20, height: 20 }} />
          </button>
          <p style={{ fontSize: 13, color: '#64748b', marginTop: 16 }}>No credit card required &middot; 30-day free trial &middot; Cancel anytime</p>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer style={{ background: S.navy, padding: '48px 32px 24px', borderTop: '1px solid rgba(51,65,85,0.4)' }} data-testid="landing-footer">
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <div className="lp-footer-grid" style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: 40, marginBottom: 40 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 12 }}>
                <span style={{ fontSize: 16, fontWeight: 200, letterSpacing: 6, color: '#fff' }}>SOLOMON</span>
                <span style={{ fontSize: 16, fontWeight: 700, color: S.blue }}>AI</span>
              </div>
              <p style={{ fontSize: 13, color: '#64748b', lineHeight: 1.6, maxWidth: 280 }}>The church platform built for what's next.</p>
            </div>
            <div>
              <h4 style={{ fontSize: 12, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 16px 0' }}>Product</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <Link to="/" style={{ fontSize: 13, color: '#64748b', textDecoration: 'none' }}>Features</Link>
                <Link to="/pricing" style={{ fontSize: 13, color: '#64748b', textDecoration: 'none' }}>Pricing</Link>
                <Link to="/demo" style={{ fontSize: 13, color: '#64748b', textDecoration: 'none' }}>Demo</Link>
              </div>
            </div>
            <div>
              <h4 style={{ fontSize: 12, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 16px 0' }}>Company</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <span style={{ fontSize: 13, color: '#64748b' }}>About</span>
                <span style={{ fontSize: 13, color: '#64748b' }}>Blog</span>
                <span style={{ fontSize: 13, color: '#64748b' }}>Contact</span>
              </div>
            </div>
            <div>
              <h4 style={{ fontSize: 12, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 16px 0' }}>Legal</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <span style={{ fontSize: 13, color: '#64748b' }}>Privacy</span>
                <span style={{ fontSize: 13, color: '#64748b' }}>Terms</span>
                <span style={{ fontSize: 13, color: '#64748b' }}>Security</span>
              </div>
            </div>
          </div>
          <div className="lp-footer-bottom" style={{ borderTop: '1px solid rgba(51,65,85,0.4)', paddingTop: 20, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <p style={{ fontSize: 12, color: '#475569', margin: 0 }} data-testid="footer-credit">&copy; 2026 Solomon AI &middot; Built on Google Cloud Platform &middot; Powered by Anthropic</p>
            <p style={{ fontSize: 11, color: '#475569', margin: 0 }}>SOC 2 Type II In Progress &middot; PCI DSS Ready</p>
          </div>
        </div>
      </footer>

      {/* ── LEAD CAPTURE MODAL ── */}
      {showLeadForm && (
        <div
          onClick={() => { if (!leadSubmitted) setShowLeadForm(false); }}
          style={{ position: 'fixed', inset: 0, zIndex: 200, background: 'rgba(15,23,42,0.7)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
          data-testid="lead-capture-overlay"
        >
          <div onClick={e => e.stopPropagation()} style={{ background: '#fff', borderRadius: 20, maxWidth: 480, width: '100%', padding: '40px 36px', position: 'relative', boxShadow: '0 24px 64px rgba(0,0,0,0.2)' }}>
            {!leadSubmitted && (
              <button onClick={() => setShowLeadForm(false)} style={{ position: 'absolute', top: 16, right: 16, background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: 4 }} data-testid="lead-form-close">
                <X style={{ width: 20, height: 20 }} />
              </button>
            )}

            {leadSubmitted ? (
              <div style={{ textAlign: 'center', padding: '20px 0' }} data-testid="lead-form-success">
                <div style={{ width: 64, height: 64, borderRadius: '50%', background: '#dcfce7', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
                  <Check style={{ width: 32, height: 32, color: '#16a34a' }} />
                </div>
                <h2 style={{ fontSize: 24, fontWeight: 800, color: S.textDark, margin: '0 0 12px 0' }}>Thank You!</h2>
                <p style={{ fontSize: 15, color: S.textGray, lineHeight: 1.6, margin: '0 0 8px 0' }}>
                  We've received your request and will contact you within 24 hours.
                </p>
                <p style={{ fontSize: 14, color: S.textGray, lineHeight: 1.6 }}>
                  Our team is excited to show you how Solomon AI can transform your church management.
                </p>
                <button onClick={() => setShowLeadForm(false)} style={{ marginTop: 24, padding: '12px 32px', background: S.navy, color: '#fff', border: 'none', borderRadius: 10, fontSize: 15, fontWeight: 600, cursor: 'pointer' }} data-testid="lead-form-done-btn">Done</button>
              </div>
            ) : (
              <>
                <div style={{ textAlign: 'center', marginBottom: 28 }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, justifyContent: 'center', marginBottom: 8 }}>
                    <span style={{ fontSize: 16, fontWeight: 200, letterSpacing: 6, color: S.navy }}>SOLOMON</span>
                    <span style={{ fontSize: 16, fontWeight: 700, color: S.blue }}>AI</span>
                  </div>
                  <h2 style={{ fontSize: 22, fontWeight: 800, color: S.textDark, margin: '0 0 6px 0' }}>Request a Demo</h2>
                  <p style={{ fontSize: 14, color: S.textGray, margin: 0 }}>See how Solomon AI can serve your church</p>
                </div>
                <form onSubmit={submitLeadForm} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <input
                    required value={leadData.church_name}
                    onChange={e => setLeadData({ ...leadData, church_name: e.target.value })}
                    placeholder="Church name *"
                    style={{ padding: '12px 16px', border: '1px solid #d1d5db', borderRadius: 10, fontSize: 15, outline: 'none' }}
                    data-testid="lead-church-name"
                  />
                  <input
                    required value={leadData.name}
                    onChange={e => setLeadData({ ...leadData, name: e.target.value })}
                    placeholder="Your name *"
                    style={{ padding: '12px 16px', border: '1px solid #d1d5db', borderRadius: 10, fontSize: 15, outline: 'none' }}
                    data-testid="lead-name"
                  />
                  <input
                    required type="email" value={leadData.email}
                    onChange={e => setLeadData({ ...leadData, email: e.target.value })}
                    placeholder="Email address *"
                    style={{ padding: '12px 16px', border: '1px solid #d1d5db', borderRadius: 10, fontSize: 15, outline: 'none' }}
                    data-testid="lead-email"
                  />
                  <input
                    type="tel" value={leadData.phone}
                    onChange={e => setLeadData({ ...leadData, phone: e.target.value })}
                    placeholder="Phone number"
                    style={{ padding: '12px 16px', border: '1px solid #d1d5db', borderRadius: 10, fontSize: 15, outline: 'none' }}
                    data-testid="lead-phone"
                  />
                  <select
                    value={leadData.current_software}
                    onChange={e => setLeadData({ ...leadData, current_software: e.target.value })}
                    style={{ padding: '12px 16px', border: '1px solid #d1d5db', borderRadius: 10, fontSize: 15, color: leadData.current_software ? S.textDark : '#9ca3af', outline: 'none', background: '#fff' }}
                    data-testid="lead-current-software"
                  >
                    <option value="">Current software</option>
                    <option value="planning-center">Planning Center</option>
                    <option value="ccb">Church Community Builder</option>
                    <option value="breeze">Breeze ChMS</option>
                    <option value="fellowshipone">FellowshipOne</option>
                    <option value="pushpay">Pushpay</option>
                    <option value="other">Other</option>
                    <option value="none">None</option>
                  </select>
                  <select
                    value={leadData.church_size}
                    onChange={e => setLeadData({ ...leadData, church_size: e.target.value })}
                    style={{ padding: '12px 16px', border: '1px solid #d1d5db', borderRadius: 10, fontSize: 15, color: leadData.church_size ? S.textDark : '#9ca3af', outline: 'none', background: '#fff' }}
                    data-testid="lead-church-size"
                  >
                    <option value="">Church size</option>
                    <option value="<100">Under 100 members</option>
                    <option value="100-500">100 - 500 members</option>
                    <option value="500-1000">500 - 1,000 members</option>
                    <option value="1000-5000">1,000 - 5,000 members</option>
                    <option value="5000+">5,000+ members</option>
                  </select>
                  <button
                    type="submit"
                    disabled={leadLoading}
                    style={{ padding: '14px 24px', background: leadLoading ? '#94a3b8' : S.blue, color: '#fff', border: 'none', borderRadius: 10, fontSize: 16, fontWeight: 700, cursor: leadLoading ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: 4 }}
                    data-testid="lead-submit-btn"
                  >
                    {leadLoading ? <><Loader2 style={{ width: 18, height: 18, animation: 'spin 1s linear infinite' }} /> Submitting...</> : <>Request Demo <ArrowRight style={{ width: 16, height: 16 }} /></>}
                  </button>
                </form>
                <p style={{ fontSize: 12, color: '#94a3b8', textAlign: 'center', marginTop: 16 }}>11 churches already trust Solomon AI</p>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
