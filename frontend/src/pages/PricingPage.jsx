import { Link } from 'react-router-dom';
import { Check, ArrowRight, X, Zap, Building2, Crown } from 'lucide-react';
import { Button } from '@/components/ui/button';

const PLANS = [
  {
    name: 'Starter',
    price: 499,
    period: '/month',
    members: 'Under 1,000 members',
    desc: 'Perfect for new church plants and small congregations getting started.',
    icon: Zap,
    accent: '#3b82f6',
    features: [
      { text: 'Up to 1,000 members', included: true },
      { text: 'Member portal', included: true },
      { text: 'Solomon Pay (1.9% + $0.30 card)', included: true },
      { text: 'Online giving + recurring', included: true },
      { text: 'Basic Kids Check-In', included: true },
      { text: 'Core reporting', included: true },
      { text: 'Ask Solomon AI', included: false },
      { text: 'Multi-campus', included: false },
      { text: 'Custom branding', included: false },
    ],
    cta: 'Get Started',
    popular: false,
  },
  {
    name: 'Growth',
    price: 999,
    period: '/month',
    members: '1,000 – 4,999 members',
    desc: 'For growing churches ready to engage their congregation at scale.',
    icon: Building2,
    accent: '#8b5cf6',
    features: [
      { text: '1,000–4,999 members', included: true },
      { text: 'Everything in Starter', included: true },
      { text: 'Kids check-in with QR + kiosk', included: true },
      { text: 'Ask Solomon AI assistant', included: true },
      { text: 'Volunteer scheduling', included: true },
      { text: 'Service planning + Live Mode', included: true },
      { text: 'Advanced analytics', included: true },
      { text: 'Custom branding', included: true },
      { text: 'Multi-campus', included: false },
    ],
    cta: 'Start 14-Day Trial',
    popular: true,
  },
  {
    name: 'Professional',
    price: 1499,
    period: '/month',
    members: '5,000 – 9,999 members',
    desc: 'For established churches with complex ministry needs.',
    icon: Building2,
    accent: '#10b981',
    features: [
      { text: '5,000–9,999 members', included: true },
      { text: 'Everything in Growth', included: true },
      { text: 'Multi-campus support', included: true },
      { text: 'Household management', included: true },
      { text: 'Custom report builder', included: true },
      { text: 'Workflow automation', included: true },
      { text: 'Priority support (4h SLA)', included: true },
      { text: 'API access', included: true },
      { text: 'Dedicated account manager', included: false },
    ],
    cta: 'Contact Sales',
    popular: false,
  },
  {
    name: 'Enterprise',
    price: 2000,
    period: '/month+',
    members: '10,000+ members',
    desc: 'Full platform power for large churches and multi-campus organizations.',
    icon: Crown,
    accent: '#f59e0b',
    features: [
      { text: 'Unlimited members', included: true },
      { text: 'Everything in Professional', included: true },
      { text: 'Unlimited campuses', included: true },
      { text: 'Church directory', included: true },
      { text: 'War room analytics', included: true },
      { text: 'Custom integrations', included: true },
      { text: 'Dedicated account manager', included: true },
      { text: 'Custom SLA', included: true },
      { text: 'On-site training', included: true },
    ],
    cta: 'Contact Sales',
    popular: false,
  },
];

const FAQ = [
  { q: 'Can I switch plans later?', a: 'Absolutely. Upgrade or downgrade any time from your Settings page. Changes take effect on your next billing cycle.' },
  { q: 'Is there a contract?', a: 'No long-term contracts. All plans are month-to-month. Cancel any time with no penalties.' },
  { q: 'What payment processors are supported?', a: 'Solomon AI uses Solomon Pay — our proprietary payment processor built for churches. Solomon Pay supports credit/debit cards, ACH bank transfers, and digital wallets. No third-party accounts required.' },
  { q: 'Can we import data from Planning Center?', a: 'Yes! We offer one-click import from Planning Center, Church Community Builder, and CSV files.' },
];

function PricingHeader() {
  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-100"
      style={{ height: 64 }}
      data-testid="pricing-header"
    >
      <div className="max-w-6xl mx-auto h-full flex items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-1.5 select-none" data-testid="pricing-logo">
          <span className="text-xl font-bold tracking-tight" style={{ color: '#1e3a5f' }}>SOLOMON</span>
          <span className="text-xl font-bold tracking-tight" style={{ color: '#3b82f6' }}>AI</span>
        </Link>
        <div className="flex items-center gap-3">
          <Link to="/support" className="text-sm text-slate-500 hover:text-slate-800 transition-colors hidden sm:block">Support</Link>
          <Link
            to="/login"
            className="px-5 py-2 text-sm font-semibold rounded-lg border-2 transition-all duration-200 hover:shadow-md"
            style={{ borderColor: '#3b82f6', color: '#3b82f6' }}
            data-testid="pricing-login-btn"
          >
            Login
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-slate-50" data-testid="pricing-page">
      <PricingHeader />

      {/* Hero */}
      <section className="pt-28 pb-16 px-6 text-center" data-testid="pricing-hero">
        <p className="text-sm font-semibold text-blue-600 uppercase tracking-widest mb-3">Pricing</p>
        <h1 className="text-4xl sm:text-5xl font-bold text-slate-900 tracking-tight leading-tight max-w-2xl mx-auto">
          Simple, transparent pricing
        </h1>
        <p className="mt-4 text-lg text-slate-500 max-w-xl mx-auto">
          No hidden fees. No per-member charges. Pick the plan that fits your church and grow without limits.
        </p>
      </section>

      {/* Plans Grid */}
      <section className="max-w-5xl mx-auto px-6 pb-20" data-testid="pricing-plans">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className="relative flex flex-col bg-white border rounded-2xl overflow-hidden transition-shadow duration-300 hover:shadow-lg"
              style={{ borderColor: plan.popular ? plan.accent : '#e2e8f0' }}
              data-testid={`pricing-plan-${plan.name.toLowerCase()}`}
            >
              {plan.popular && (
                <div
                  className="text-center text-xs font-bold uppercase tracking-wider py-1.5 text-white"
                  style={{ background: plan.accent }}
                  data-testid="pricing-popular-badge"
                >
                  Most Popular
                </div>
              )}

              <div className="p-6 flex-1 flex flex-col">
                <div className="flex items-center gap-2 mb-2">
                  <plan.icon className="w-5 h-5" style={{ color: plan.accent }} />
                  <h3 className="text-lg font-bold text-slate-900">{plan.name}</h3>
                </div>
                {plan.members && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full mb-3 inline-block w-fit" style={{ background: `${plan.accent}20`, color: plan.accent }}>
                    {plan.members}
                  </span>
                )}

                <div className="mb-3">
                  <span className="text-4xl font-extrabold text-slate-900">
                    {plan.price === 0 ? 'Free' : `$${plan.price.toLocaleString()}`}
                  </span>
                  {plan.price > 0 && (
                    <span className="text-sm text-slate-500 ml-1">{plan.period}</span>
                  )}
                </div>

                <p className="text-sm text-slate-500 mb-6 leading-relaxed">{plan.desc}</p>

                <ul className="space-y-2.5 mb-8 flex-1">
                  {plan.features.map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      {f.included ? (
                        <Check className="w-4 h-4 mt-0.5 text-emerald-500 flex-shrink-0" />
                      ) : (
                        <X className="w-4 h-4 mt-0.5 text-slate-300 flex-shrink-0" />
                      )}
                      <span className={f.included ? 'text-slate-700' : 'text-slate-400'}>{f.text}</span>
                    </li>
                  ))}
                </ul>

                <Link to={plan.name === 'Enterprise' ? '/support' : '/signup'} className="w-full">
                  <Button
                    className="w-full font-semibold text-sm py-5"
                    style={plan.popular ? { background: plan.accent, color: '#fff' } : {}}
                    variant={plan.popular ? 'default' : 'outline'}
                    data-testid={`pricing-cta-${plan.name.toLowerCase()}`}
                  >
                    {plan.cta}
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="max-w-3xl mx-auto px-6 pb-24" data-testid="pricing-faq">
        <h2 className="text-2xl font-bold text-slate-900 text-center mb-10">Frequently Asked Questions</h2>
        <div className="space-y-5">
          {FAQ.map((item, idx) => (
            <div key={`faq-${idx}`} className="bg-white border border-slate-200 rounded-xl p-5" data-testid={`pricing-faq-${idx}`}>
              <h4 className="font-semibold text-slate-900 mb-1.5">{item.q}</h4>
              <p className="text-sm text-slate-500 leading-relaxed">{item.a}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white" data-testid="pricing-footer">
        <div className="max-w-6xl mx-auto px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-sm text-slate-500">&copy; 2026 Solomon AI LLC. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <Link to="/support" className="text-sm text-slate-500 hover:text-slate-800 transition-colors">Support</Link>
            <Link to="/" className="text-sm text-slate-500 hover:text-slate-800 transition-colors">Home</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
