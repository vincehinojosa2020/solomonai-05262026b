import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, Check, X, ChevronRight, Tv, Baby, Heart, Coffee, Zap, Users, ShoppingBag, MessageSquare, Play } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

const S = {
  navy: '#0f172a', navyLight: '#1e293b', blue: '#3b82f6', gold: '#f59e0b',
  grayLight: '#f8fafc', white: '#ffffff', textPrimary: '#f8fafc', textMuted: '#94a3b8',
  textDark: '#111827', textGray: '#6b7280', border: '#e5e7eb',
};

export default function LandingPage() {
  const navigate = useNavigate();
  const [waitlistEmail, setWaitlistEmail] = useState('');
  const [waitlistChurch, setWaitlistChurch] = useState('');
  const [waitlistSent, setWaitlistSent] = useState(false);

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

  return (
    <div style={{ background: S.white, color: S.textDark, fontFamily: "'Inter',-apple-system,BlinkMacSystemFont,sans-serif" }} data-testid="landing-page">

      {/* ── NAV ── */}
      <nav style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100, background: 'rgba(15,23,42,0.95)', backdropFilter: 'blur(12px)', borderBottom: '1px solid rgba(255,255,255,0.06)' }} data-testid="landing-header">
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 32px', height: 64, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'baseline', gap: 6 }} data-testid="landing-logo">
            <span style={{ fontSize: 18, fontWeight: 200, letterSpacing: 6, color: '#fff' }}>SOLOMON</span>
            <span style={{ fontSize: 18, fontWeight: 700, color: S.blue }}>AI</span>
          </Link>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Link to="/login" style={{ padding: '8px 20px', fontSize: 14, fontWeight: 600, color: '#fff', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 8, textDecoration: 'none' }} data-testid="landing-login-btn">Sign In</Link>
            <Link to="/signup" style={{ padding: '8px 20px', fontSize: 14, fontWeight: 700, color: '#fff', background: S.blue, borderRadius: 8, textDecoration: 'none' }} data-testid="landing-get-started-btn">Get Started</Link>
          </div>
        </div>
      </nav>

      {/* ── 1.1 HERO ── */}
      <section style={{ background: `linear-gradient(160deg, ${S.navy} 0%, #0c1220 60%, ${S.navyLight} 100%)`, minHeight: '100vh', paddingTop: 120, paddingBottom: 80 }} data-testid="hero-section">
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 32px', display: 'flex', alignItems: 'center', gap: 60 }}>
          <div style={{ flex: '1 1 55%' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 16px', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 100, marginBottom: 28 }}>
              <span style={{ color: S.gold, fontSize: 13, fontWeight: 600 }}>Trusted by 11 churches &middot; 64,500 members</span>
            </div>
            <h1 style={{ fontSize: 'clamp(40px, 5vw, 64px)', fontWeight: 800, color: '#fff', lineHeight: 1.08, letterSpacing: '-0.03em', margin: '0 0 24px 0' }} data-testid="hero-headline">
              Your church deserves<br />better technology.
            </h1>
            <p style={{ fontSize: 'clamp(16px, 1.5vw, 20px)', color: S.textMuted, lineHeight: 1.6, maxWidth: 560, margin: '0 0 40px 0' }}>
              Solomon AI replaces Planning Center, Church Center, and SecureGive — in one platform, at one price, powered by AI.
            </p>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              <Link to="/signup" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '16px 32px', background: S.blue, color: '#fff', fontSize: 16, fontWeight: 700, borderRadius: 10, textDecoration: 'none', transition: 'transform 0.2s' }} data-testid="hero-cta-trial">
                Start Free Trial <ArrowRight style={{ width: 18, height: 18 }} />
              </Link>
              <Link to="/demo" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '16px 28px', border: '1px solid rgba(255,255,255,0.2)', color: '#fff', fontSize: 16, fontWeight: 600, borderRadius: 10, textDecoration: 'none' }} data-testid="hero-cta-demo">
                <Play style={{ width: 16, height: 16 }} /> Watch Demo
              </Link>
            </div>
            <p style={{ fontSize: 13, color: '#64748b', marginTop: 20 }}>
              Join churches saving $2,000+/month vs Planning Center + SecureGive combined
            </p>
          </div>
          <div style={{ flex: '1 1 45%', position: 'relative' }} data-testid="hero-visual">
            <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: 16, padding: 24, boxShadow: '0 0 80px rgba(59,130,246,0.12)', position: 'relative' }}>
              <div style={{ position: 'absolute', top: -10, right: -10, padding: '4px 12px', background: S.blue, borderRadius: 6, fontSize: 10, fontWeight: 700, color: '#fff', letterSpacing: '0.06em' }}>LIVE DEMO DATA</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
                {[
                  { label: 'Members', val: '312', sub: 'Present today', color: '#60a5fa' },
                  { label: 'Kids', val: '47', sub: 'Checked in', color: '#4ade80' },
                  { label: 'Given Today', val: '$28,450', sub: 'General + Building', color: '#34d399' },
                  { label: 'Cafe Orders', val: '34', sub: 'Before service', color: '#fbbf24' },
                ].map(k => (
                  <div key={k.label} style={{ background: 'rgba(30,41,59,0.8)', borderRadius: 10, padding: '14px 16px' }}>
                    <p style={{ fontSize: 10, color: '#64748b', margin: 0, textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>{k.label}</p>
                    <p style={{ fontSize: 24, fontWeight: 800, fontFamily: 'monospace', color: k.color, margin: '4px 0 0 0' }}>{k.val}</p>
                    <p style={{ fontSize: 11, color: '#475569', margin: 0 }}>{k.sub}</p>
                  </div>
                ))}
              </div>
              <div style={{ background: 'rgba(30,41,59,0.8)', borderRadius: 10, padding: 14 }}>
                <p style={{ fontSize: 10, color: '#64748b', margin: '0 0 8px 0', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>Live Activity</p>
                {['Emma Davis checked in to PreK', 'Anonymous gave $100 to General Fund', 'James Wilson ordered Latte'].map((t, i) => (
                  <div key={i} style={{ fontSize: 12, color: '#94a3b8', padding: '6px 0', borderTop: i > 0 ? '1px solid rgba(51,65,85,0.4)' : 'none' }}>{t}</div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 1.2 SOCIAL PROOF BAR ── */}
      <section style={{ background: S.white, padding: '48px 32px', borderBottom: `1px solid ${S.border}` }} data-testid="social-proof-section">
        <div style={{ maxWidth: 1000, margin: '0 auto', textAlign: 'center' }}>
          <p style={{ fontSize: 12, color: S.textGray, textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: 28 }}>Powering churches across America</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 32 }}>
            {[
              { num: '11', label: 'Churches', sub: 'Active' },
              { num: '64,500', label: 'Members', sub: 'Engaged' },
              { num: '$151M', label: 'YTD Given', sub: 'Processed' },
              { num: '3', label: 'Campuses', sub: 'Abundant' },
            ].map(s => (
              <div key={s.label}>
                <p style={{ fontSize: 40, fontWeight: 800, color: S.textDark, margin: 0, fontFamily: 'monospace', letterSpacing: '-0.03em' }}>{s.num}</p>
                <p style={{ fontSize: 14, fontWeight: 600, color: S.textDark, margin: '4px 0 0 0' }}>{s.label}</p>
                <p style={{ fontSize: 12, color: S.textGray, margin: 0 }}>{s.sub}</p>
              </div>
            ))}
          </div>
          <p style={{ fontSize: 12, color: S.textGray, marginTop: 20 }}>Real data. Live platform.</p>
        </div>
      </section>

      {/* ── 1.3 THE PROBLEM ── */}
      <section style={{ background: S.grayLight, padding: '80px 32px' }} data-testid="problem-section">
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <p style={{ fontSize: 12, fontWeight: 700, color: S.blue, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12 }}>The Problem</p>
          <h2 style={{ fontSize: 'clamp(28px, 3vw, 40px)', fontWeight: 800, color: S.textDark, letterSpacing: '-0.02em', margin: '0 0 48px 0', lineHeight: 1.15 }}>
            Your church is paying too much<br />for too little.
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
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

      {/* ── 1.4 THE SOLUTION ── */}
      <section style={{ background: S.white, padding: '80px 32px' }} data-testid="solution-section">
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <p style={{ fontSize: 12, fontWeight: 700, color: S.blue, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12 }}>Everything Your Church Needs</p>
          <h2 style={{ fontSize: 'clamp(28px, 3vw, 40px)', fontWeight: 800, color: S.textDark, letterSpacing: '-0.02em', margin: '0 0 48px 0', lineHeight: 1.15 }}>
            One platform. Every ministry.<br />Powered by AI.
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20 }}>
            {[
              { icon: Tv, title: 'Watch', desc: 'MasterClass-quality sermon library. Members watch Monday. They come back Sunday.' },
              { icon: Baby, title: 'Kids Check-In', desc: 'QR codes. Real-time bidirectional sync. Parent checks in on iPhone. Admin scans instantly. No paper.' },
              { icon: Heart, title: 'Give', desc: 'One tap to give. Every fund. Recurring. Beautiful thank-you experience. Tax statements auto-generated.' },
              { icon: Coffee, title: 'Cafe + Merch', desc: 'Order Sunday coffee before you arrive. Buy church merchandise in 3 taps. Every order includes a giving nudge.' },
              { icon: MessageSquare, title: 'Ask Solomon AI', desc: "An AI pastor's assistant. 'What time is the marriage retreat?' 'Who's preaching Sunday?' — instant answers." },
              { icon: Zap, title: 'War Room', desc: 'Live Sunday command center. Kids checked in. Giving flowing. Cafe ordered. All on one screen.' },
            ].map(f => (
              <div key={f.title} style={{ background: S.grayLight, borderRadius: 14, padding: 28, border: `1px solid ${S.border}` }}>
                <f.icon style={{ width: 28, height: 28, color: S.blue, marginBottom: 16 }} />
                <h3 style={{ fontSize: 18, fontWeight: 700, color: S.textDark, margin: '0 0 8px 0' }}>{f.title}</h3>
                <p style={{ fontSize: 14, color: S.textGray, lineHeight: 1.6, margin: 0 }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 1.5 COMPARISON TABLE ── */}
      <section style={{ background: S.grayLight, padding: '80px 32px' }} data-testid="comparison-section">
        <div style={{ maxWidth: 900, margin: '0 auto' }}>
          <h2 style={{ fontSize: 'clamp(28px, 3vw, 36px)', fontWeight: 800, color: S.textDark, letterSpacing: '-0.02em', margin: '0 0 40px 0', textAlign: 'center' }}>
            Everything they have.<br />Everything they don't.
          </h2>
          <div style={{ background: S.white, borderRadius: 16, overflow: 'hidden', border: `1px solid ${S.border}`, boxShadow: '0 2px 8px rgba(0,0,0,0.04)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr style={{ borderBottom: `2px solid ${S.border}` }}>
                  <th style={{ padding: '16px 20px', textAlign: 'left', fontWeight: 600, color: S.textGray }}>Feature</th>
                  <th style={{ padding: '16px 16px', textAlign: 'center', fontWeight: 700, color: S.blue }}>Solomon AI</th>
                  <th style={{ padding: '16px 16px', textAlign: 'center', fontWeight: 600, color: S.textGray }}>Planning Center</th>
                  <th style={{ padding: '16px 16px', textAlign: 'center', fontWeight: 600, color: S.textGray }}>SecureGive</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ['Member Management', true, true, false],
                  ['Kids Check-In (QR)', true, true, false],
                  ['Online Giving', true, true, true],
                  ['Small Groups', true, true, false],
                  ['Events & Registration', true, true, false],
                  ['Sermon Library', true, false, false],
                  ['Cafe Ordering', true, false, false],
                  ['Merch Store', true, false, false],
                  ['AI Assistant', true, false, false],
                  ['Geofencing Check-in', true, false, false],
                  ['Real-time War Room', true, false, false],
                  ['White-label App', true, false, false],
                  ['Multi-campus (1 bill)', true, false, false],
                  ['Flat Monthly Price', true, false, false],
                ].map(([feature, sol, pc, sg], i) => (
                  <tr key={feature} style={{ borderBottom: `1px solid ${S.border}`, background: i % 2 === 0 ? S.white : S.grayLight }}>
                    <td style={{ padding: '12px 20px', color: S.textDark, fontWeight: 500 }}>{feature}</td>
                    <td style={{ padding: '12px 16px', textAlign: 'center' }}>{sol ? <Check style={{ width: 18, height: 18, color: '#22c55e', margin: '0 auto' }} /> : <X style={{ width: 18, height: 18, color: '#d1d5db', margin: '0 auto' }} />}</td>
                    <td style={{ padding: '12px 16px', textAlign: 'center' }}>{pc ? <Check style={{ width: 18, height: 18, color: '#22c55e', margin: '0 auto' }} /> : <X style={{ width: 18, height: 18, color: '#d1d5db', margin: '0 auto' }} />}</td>
                    <td style={{ padding: '12px 16px', textAlign: 'center' }}>{sg ? <Check style={{ width: 18, height: 18, color: '#22c55e', margin: '0 auto' }} /> : <X style={{ width: 18, height: 18, color: '#d1d5db', margin: '0 auto' }} />}</td>
                  </tr>
                ))}
                <tr style={{ background: '#f0f9ff' }}>
                  <td style={{ padding: '14px 20px', fontWeight: 700, color: S.textDark }}>Monthly Cost</td>
                  <td style={{ padding: '14px 16px', textAlign: 'center', fontWeight: 700, color: S.blue }}>$499-$2,999</td>
                  <td style={{ padding: '14px 16px', textAlign: 'center', color: S.textGray }}>$700-$2,400+</td>
                  <td style={{ padding: '14px 16px', textAlign: 'center', color: S.textGray }}>$99-$199+2%</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div style={{ background: '#fef3c7', border: '1px solid #fde68a', borderRadius: 12, padding: '20px 24px', marginTop: 24, textAlign: 'center' }}>
            <p style={{ fontSize: 15, fontWeight: 700, color: '#92400e', margin: '0 0 4px 0' }}>
              A 50,000-member church on SecureGive pays $20,000/month in transaction fees alone.
            </p>
            <p style={{ fontSize: 14, color: '#a16207', margin: 0 }}>
              Solomon AI: one flat price. No transaction fees.* <span style={{ fontSize: 12 }}>*Until we launch Solomon Pay in 2026.</span>
            </p>
          </div>
        </div>
      </section>

      {/* ── 1.6 PRICING ── */}
      <section style={{ background: S.white, padding: '80px 32px' }} data-testid="pricing-section">
        <div style={{ maxWidth: 1000, margin: '0 auto', textAlign: 'center' }}>
          <p style={{ fontSize: 12, fontWeight: 700, color: S.blue, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12 }}>Pricing</p>
          <h2 style={{ fontSize: 'clamp(28px, 3vw, 40px)', fontWeight: 800, color: S.textDark, letterSpacing: '-0.02em', margin: '0 0 8px 0' }}>Simple pricing. No surprises.</h2>
          <p style={{ fontSize: 16, color: S.textGray, margin: '0 0 48px 0' }}>One price. Every feature. All campuses included.</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 20, textAlign: 'left' }}>
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
              { q: 'Do you charge per campus?', a: "No. One account covers all your campuses. Abundant Church's 3 campuses: one bill." },
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

      {/* ── 1.7 THE VISION ── */}
      <section style={{ background: S.navy, padding: '80px 32px', color: '#fff' }} data-testid="vision-section">
        <div style={{ maxWidth: 800, margin: '0 auto', textAlign: 'center' }}>
          <p style={{ fontSize: 12, fontWeight: 700, color: S.gold, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12 }}>The Future</p>
          <h2 style={{ fontSize: 'clamp(28px, 3vw, 40px)', fontWeight: 800, letterSpacing: '-0.02em', margin: '0 0 56px 0', lineHeight: 1.15 }}>
            We're building the financial<br />infrastructure of the church.
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24, textAlign: 'left' }}>
            {[
              { label: 'NOW', badge: 'bg-green-500', title: 'Church Management', desc: 'Replace Planning Center + Church Center + SecureGive in one platform.', status: 'Live' },
              { label: '2026', badge: 'bg-blue-500', title: 'Solomon Pay', desc: 'Our own payment processor. Transaction fees lower than Venmo. Lower than Pushpay. Lower than anyone. Every dollar stays in ministry.', status: 'Coming' },
              { label: 'BEYOND', badge: 'bg-purple-500', title: 'The Church OS', desc: 'Every API. Every integration. Every system a church uses — connected through Solomon AI. The operating system of the American church.', status: 'Vision' },
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

          {/* Waitlist form */}
          <div style={{ marginTop: 48, padding: '28px 32px', background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 14 }} data-testid="waitlist-form">
            {waitlistSent ? (
              <p style={{ fontSize: 16, color: S.gold, fontWeight: 600 }}>You're on the Solomon Pay waitlist! We'll be in touch.</p>
            ) : (
              <>
                <p style={{ fontSize: 15, fontWeight: 700, color: S.gold, marginBottom: 16 }}>Join the waitlist for Solomon Pay</p>
                <div style={{ display: 'flex', gap: 8, maxWidth: 500, margin: '0 auto' }}>
                  <input value={waitlistEmail} onChange={e => setWaitlistEmail(e.target.value)} placeholder="Email" style={{ flex: 1, padding: '12px 16px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(15,23,42,0.6)', color: '#fff', fontSize: 14 }} data-testid="waitlist-email" />
                  <input value={waitlistChurch} onChange={e => setWaitlistChurch(e.target.value)} placeholder="Church name" style={{ flex: 1, padding: '12px 16px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(15,23,42,0.6)', color: '#fff', fontSize: 14 }} data-testid="waitlist-church" />
                  <button onClick={submitWaitlist} style={{ padding: '12px 20px', background: S.gold, color: '#fff', borderRadius: 8, border: 'none', fontWeight: 700, fontSize: 14, cursor: 'pointer' }} data-testid="waitlist-submit">Join</button>
                </div>
              </>
            )}
          </div>
        </div>
      </section>

      {/* ── 1.8 FINAL CTA ── */}
      <section style={{ background: `linear-gradient(135deg, ${S.navy} 0%, #1a2744 100%)`, padding: '80px 32px', textAlign: 'center' }} data-testid="final-cta-section">
        <div style={{ maxWidth: 700, margin: '0 auto' }}>
          <h2 style={{ fontSize: 'clamp(32px, 4vw, 48px)', fontWeight: 800, color: '#fff', letterSpacing: '-0.02em', lineHeight: 1.15, margin: '0 0 32px 0' }}>
            Your church deserves<br />better technology.<br />Starting today.
          </h2>
          <Link to="/signup" style={{ display: 'inline-flex', alignItems: 'center', gap: 10, padding: '18px 40px', background: S.gold, color: '#fff', fontSize: 18, fontWeight: 800, borderRadius: 12, textDecoration: 'none' }} data-testid="final-cta-btn">
            Start Free Trial <ArrowRight style={{ width: 20, height: 20 }} />
          </Link>
          <p style={{ fontSize: 13, color: '#64748b', marginTop: 16 }}>No credit card required &middot; 30-day free trial &middot; Cancel anytime</p>
        </div>
      </section>

      {/* ── 1.9 FOOTER ── */}
      <footer style={{ background: S.navy, padding: '48px 32px 24px', borderTop: '1px solid rgba(51,65,85,0.4)' }} data-testid="landing-footer">
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: 40, marginBottom: 40 }}>
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
          <div style={{ borderTop: '1px solid rgba(51,65,85,0.4)', paddingTop: 20, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <p style={{ fontSize: 12, color: '#475569', margin: 0 }}>&copy; 2026 Solomon AI &middot; Built on Google Cloud &middot; Powered by Anthropic Claude</p>
            <p style={{ fontSize: 11, color: '#475569', margin: 0 }}>SOC 2 Type II In Progress &middot; PCI DSS Ready</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
