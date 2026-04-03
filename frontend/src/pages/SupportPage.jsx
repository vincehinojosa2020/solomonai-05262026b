import { Link } from 'react-router-dom';
import { Mail, Phone, Clock, ChevronDown } from 'lucide-react';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';

const NAV_HEIGHT = 64;

function Header() {
  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-100"
      style={{ height: NAV_HEIGHT }}
      data-testid="support-header"
    >
      <div className="max-w-6xl mx-auto h-full flex items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-1.5 select-none" data-testid="support-logo">
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
          data-testid="support-login-btn"
        >
          Login
        </Link>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white" data-testid="support-footer">
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

const FAQ_ITEMS = [
  {
    q: 'How do I reset my password?',
    a: 'On the login page, tap "Forgot password?" and enter your email. You\'ll receive a reset link within minutes. If you don\'t see it, check your spam folder or text us for help.',
  },
  {
    q: 'How do I set up Kids Check-In?',
    a: 'Go to Admin > Kids Check-In to configure rooms and age groups. Parents scan a QR code at drop-off and receive a unique pickup code. It\'s that simple.',
  },
  {
    q: 'How do I connect my payment processor?',
    a: 'Navigate to Admin > Integrations and select Solomon Pay as your processor. Solomon Pay is built-in — giving flows through immediately with no third-party accounts required.',
  },
  {
    q: 'Can I manage multiple campuses?',
    a: 'Yes. Solomon AI supports multi-campus organizations. Admins with multi-campus access see a campus switcher in the top bar to toggle between locations seamlessly.',
  },
  {
    q: 'Is my church\'s data secure?',
    a: 'Absolutely. We use encrypted connections (TLS), PCI-compliant payment processing, and role-based access control with 40+ granular permissions. Your data is protected at every level.',
  },
];

export default function SupportPage() {
  return (
    <div className="min-h-screen bg-white flex flex-col" data-testid="support-page">
      <Header />

      <main className="flex-1" style={{ paddingTop: NAV_HEIGHT }}>
        {/* Hero */}
        <section className="pt-16 sm:pt-24 pb-12 text-center px-6">
          <h1
            className="text-3xl sm:text-4xl font-extrabold tracking-tight"
            style={{ color: '#1e3a5f' }}
          >
            We&apos;re Here to Help
          </h1>
          <p className="mt-4 text-base text-slate-600 max-w-lg mx-auto">
            Have questions about Solomon AI? Reach out and we&apos;ll get back to you quickly.
          </p>
        </section>

        {/* Contact Cards */}
        <section className="max-w-2xl mx-auto px-6 pb-16" data-testid="contact-section">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            <a
              href="mailto:support@solomonai.us"
              className="flex flex-col items-center gap-3 p-6 rounded-2xl border border-slate-100 hover:border-blue-200 hover:shadow-lg transition-all duration-300"
              data-testid="contact-email"
            >
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{ background: 'rgba(59,130,246,0.08)' }}
              >
                <Mail className="w-5 h-5" style={{ color: '#3b82f6' }} />
              </div>
              <span className="text-sm font-semibold" style={{ color: '#1e3a5f' }}>Email Us</span>
              <span className="text-xs text-slate-500">support@solomonai.us</span>
            </a>

            <a
              href="tel:+14084176674"
              className="flex flex-col items-center gap-3 p-6 rounded-2xl border border-slate-100 hover:border-blue-200 hover:shadow-lg transition-all duration-300"
              data-testid="contact-phone"
            >
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{ background: 'rgba(59,130,246,0.08)' }}
              >
                <Phone className="w-5 h-5" style={{ color: '#3b82f6' }} />
              </div>
              <span className="text-sm font-semibold" style={{ color: '#1e3a5f' }}>Text / Call</span>
              <span className="text-xs text-slate-500">(408) 417-6674</span>
            </a>

            <div className="flex flex-col items-center gap-3 p-6 rounded-2xl border border-slate-100">
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{ background: 'rgba(34,197,94,0.08)' }}
              >
                <Clock className="w-5 h-5" style={{ color: '#22c55e' }} />
              </div>
              <span className="text-sm font-semibold" style={{ color: '#1e3a5f' }}>Response Time</span>
              <span className="text-xs text-slate-500">Within 24 hours</span>
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section className="max-w-2xl mx-auto px-6 pb-20" data-testid="faq-section">
          <h2 className="text-xl font-bold mb-6" style={{ color: '#1e3a5f' }}>
            Frequently Asked Questions
          </h2>
          <Accordion type="single" collapsible className="w-full">
            {FAQ_ITEMS.map((item, i) => (
              <AccordionItem key={i} value={`faq-${i}`}>
                <AccordionTrigger className="text-sm font-semibold text-left" style={{ color: '#1e3a5f' }}>
                  {item.q}
                </AccordionTrigger>
                <AccordionContent className="text-sm text-slate-600 leading-relaxed">
                  {item.a}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </section>
      </main>

      <Footer />
    </div>
  );
}
