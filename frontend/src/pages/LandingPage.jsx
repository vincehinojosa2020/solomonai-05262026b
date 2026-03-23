import { Link } from 'react-router-dom';
import { 
  Smartphone, Bot, ShieldCheck, Heart, Tv, QrCode, 
  Users, CalendarDays, MessageCircle, ArrowRight, Mail, Phone, ChevronRight
} from 'lucide-react';

const NAV_HEIGHT = 64;

function Header() {
  return (
    <header 
      className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-100"
      style={{ height: NAV_HEIGHT }}
      data-testid="landing-header"
    >
      <div className="max-w-6xl mx-auto h-full flex items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-1.5 select-none" data-testid="landing-logo">
          <span className="text-xl font-bold tracking-tight" style={{ color: '#1e3a5f' }}>
            SOLOMON
          </span>
          <span className="text-xl font-bold tracking-tight" style={{ color: '#3b82f6' }}>
            AI
          </span>
        </Link>
        <Link
          to="/login"
          className="px-5 py-2 text-sm font-semibold rounded-lg border-2 transition-all duration-200 hover:shadow-md"
          style={{ borderColor: '#3b82f6', color: '#3b82f6' }}
          data-testid="landing-login-btn"
        >
          Login
        </Link>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white" data-testid="landing-footer">
      <div className="max-w-6xl mx-auto px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-3">
        <p className="text-sm text-slate-500">
          &copy; 2026 Solomon AI LLC. All rights reserved.
        </p>
        <div className="flex items-center gap-6">
          <Link to="/support" className="text-sm text-slate-500 hover:text-slate-800 transition-colors">
            Support
          </Link>
          <span className="text-sm text-slate-400 cursor-default">Privacy</span>
        </div>
      </div>
    </footer>
  );
}

const VALUE_PROPS = [
  {
    icon: Smartphone,
    title: 'One App, Not Seven',
    desc: 'Stop juggling Planning Center, Pushpay, and five other logins. Everything your church needs, unified.',
  },
  {
    icon: Bot,
    title: 'AI That Actually Helps',
    desc: 'Ask Solomon anything — service times, giving history, group signups. Your members get answers instantly.',
  },
  {
    icon: ShieldCheck,
    title: 'Safe & Secure',
    desc: 'Kids check-in with QR verification. PCI-compliant giving. Your congregation\'s data, protected.',
  },
];

const FEATURES = [
  { icon: Heart, label: 'Give', desc: 'Effortless generosity' },
  { icon: Tv, label: 'Watch', desc: 'Sermons on demand' },
  { icon: QrCode, label: 'Check-In', desc: 'Kids secured with QR' },
  { icon: Users, label: 'Groups', desc: 'Find your people' },
  { icon: CalendarDays, label: 'Events', desc: 'Never miss a moment' },
  { icon: MessageCircle, label: 'Ask Solomon', desc: 'AI assistant built in' },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white" data-testid="landing-page">
      <Header />

      {/* ===== HERO ===== */}
      <section
        className="relative overflow-hidden"
        style={{ paddingTop: NAV_HEIGHT }}
        data-testid="hero-section"
      >
        {/* Subtle gradient bg */}
        <div className="absolute inset-0 pointer-events-none" style={{
          background: 'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(59,130,246,0.06) 0%, transparent 70%)',
        }} />

        <div className="relative max-w-3xl mx-auto text-center px-6 pt-20 pb-16 sm:pt-28 sm:pb-24">
          <h1
            className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight tracking-tight"
            style={{ color: '#1e3a5f' }}
          >
            One App for Your<br className="hidden sm:block" /> Entire Church
          </h1>

          <p className="mt-6 text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Giving. Check-in. Sermons. Groups. Events. Prayer.<br className="hidden sm:block" />
            All in one place — powered by AI that actually helps.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              className="w-full sm:w-auto px-8 py-3.5 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center gap-2"
              style={{ background: '#3b82f6' }}
              data-testid="hero-demo-btn"
              onClick={() => {
                const el = document.getElementById('demo');
                if (el) el.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              Request a Demo
              <ArrowRight className="w-4 h-4" />
            </button>
            <a
              href="sms:+14084176674"
              className="w-full sm:w-auto px-8 py-3.5 font-semibold rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-50 transition-all duration-200 flex items-center justify-center gap-2"
              data-testid="hero-text-btn"
            >
              <Phone className="w-4 h-4 text-slate-400" />
              Text to Start: (408) 417-6674
            </a>
          </div>
        </div>
      </section>

      {/* ===== VALUE PROPS ===== */}
      <section className="py-16 sm:py-24 bg-slate-50/60" data-testid="value-props-section">
        <div className="max-w-5xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            {VALUE_PROPS.map((v, i) => (
              <div key={i} className="text-center" data-testid={`value-prop-${i}`}>
                <div
                  className="mx-auto w-14 h-14 rounded-2xl flex items-center justify-center mb-5"
                  style={{ background: 'rgba(59,130,246,0.08)' }}
                >
                  <v.icon className="w-6 h-6" style={{ color: '#3b82f6' }} />
                </div>
                <h3 className="text-lg font-bold mb-2" style={{ color: '#1e3a5f' }}>
                  {v.title}
                </h3>
                <p className="text-sm text-slate-600 leading-relaxed">{v.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== FEATURES GRID ===== */}
      <section className="py-16 sm:py-24" data-testid="features-section">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-center text-base sm:text-lg font-bold uppercase tracking-widest mb-2" style={{ color: '#3b82f6' }}>
            Everything Built In
          </h2>
          <p className="text-center text-2xl sm:text-3xl font-bold mb-14" style={{ color: '#1e3a5f' }}>
            Church tech that just works.
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-6">
            {FEATURES.map((f, i) => (
              <div
                key={i}
                className="group p-6 rounded-2xl border border-slate-100 hover:border-blue-200 hover:shadow-lg transition-all duration-300 cursor-default"
                data-testid={`feature-card-${i}`}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center mb-4 transition-colors"
                  style={{ background: 'rgba(59,130,246,0.06)' }}
                >
                  <f.icon className="w-5 h-5" style={{ color: '#3b82f6' }} />
                </div>
                <h4 className="font-bold text-sm" style={{ color: '#1e3a5f' }}>{f.label}</h4>
                <p className="text-xs text-slate-500 mt-1">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== TRUST LINE ===== */}
      <section className="py-10 text-center">
        <p className="text-sm font-medium text-slate-400 tracking-wide">
          Trusted by churches ready for what&apos;s next.
        </p>
      </section>

      {/* ===== CTA BANNER ===== */}
      <section
        id="demo"
        className="py-16 sm:py-20"
        style={{ background: 'linear-gradient(135deg, #1e3a5f 0%, #1e3a5f 60%, #2563eb 100%)' }}
        data-testid="cta-section"
      >
        <div className="max-w-2xl mx-auto text-center px-6">
          <h2 className="text-2xl sm:text-3xl font-bold text-white mb-4">
            Ready to simplify your church&apos;s tech?
          </h2>
          <p className="text-blue-200 mb-10 text-sm sm:text-base">
            Built for the next generation of church leaders. Modern, intuitive, and actually easy to use.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href="mailto:support@solomonai.us?subject=Demo%20Request"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 bg-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200"
              style={{ color: '#1e3a5f' }}
              data-testid="cta-demo-btn"
            >
              Request a Demo
              <ChevronRight className="w-4 h-4" />
            </a>
            <a
              href="sms:+14084176674"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 border border-white/30 text-white font-semibold rounded-xl hover:bg-white/10 transition-all duration-200"
              data-testid="cta-text-btn"
            >
              <Phone className="w-4 h-4" />
              Text us: (408) 417-6674
            </a>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
