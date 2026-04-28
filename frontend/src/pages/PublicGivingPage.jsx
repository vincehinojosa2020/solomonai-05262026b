/**
 * PublicGivingPage — Guest, no-auth, church-branded giving experience.
 *
 * Routed at: /give/:churchSlug
 *
 * Flow:
 *   1. Load church config from /api/churches/:slug/public-config
 *   2. Load Stripe.js dynamically (https://js.stripe.com/v3)
 *   3. Initialize Stripe Elements with publishable key from /api/stripe/elements/config
 *   4. On submit:
 *        → POST /api/stripe/create-payment-intent (server computes total + fees)
 *        → stripe.confirmCardPayment(client_secret, { payment_method: { card, billing_details } })
 *        → POST /api/stripe/confirm-donation (server persists donation)
 *   5. Show receipt screen with real Stripe IDs.
 *
 * Theming — every color/font pulls from the church config so each tenant's
 * giving page looks native to their brand. Eden Church gets its black + cyan
 * Playfair look; other churches render as white + their primary_color.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { API_URL } from '@/lib/utils';

const STRIPE_JS_URL = 'https://js.stripe.com/v3';

// ---------- helpers -------------------------------------------------------
const formatCurrency = (n) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n || 0);

const loadStripeJs = () =>
  new Promise((resolve, reject) => {
    if (window.Stripe) return resolve(window.Stripe);
    const existing = document.querySelector(`script[src^="${STRIPE_JS_URL}"]`);
    if (existing) {
      existing.addEventListener('load', () => resolve(window.Stripe));
      existing.addEventListener('error', reject);
      return;
    }
    const s = document.createElement('script');
    s.src = STRIPE_JS_URL;
    s.async = true;
    s.onload = () => resolve(window.Stripe);
    s.onerror = () => reject(new Error('Failed to load payment system'));
    document.head.appendChild(s);
  });

// ---------- theme resolver -----------------------------------------------
/**
 * Eden Church gets the bespoke black + cyan + Playfair treatment. Every
 * other tenant renders on a light background with their primary color as
 * the accent. Keep this mapping narrow; branding per tenant should live
 * in the tenant doc in a future iteration.
 */
function resolveTheme(config) {
  const isEden = config?.slug === 'eden-church';
  if (isEden) {
    return {
      mode: 'eden',
      bg: '#000000',
      panel: '#111111',
      text: '#ffffff',
      muted: '#888888',
      accent: '#2dd4bf',
      border: 'rgba(255,255,255,0.1)',
      inputBg: '#111111',
      primaryBtnBg: '#ffffff',
      primaryBtnText: '#000000',
      primaryBtnHover: '#2dd4bf',
      headingFont: '"Playfair Display", Georgia, serif',
      bodyFont: '"Space Grotesk", -apple-system, BlinkMacSystemFont, sans-serif',
      radius: 0,
      navLabel: 'ONLINE GIVING',
      logoText: 'EDEN',
      logoAccent: 'X',
    };
  }
  return {
    mode: 'default',
    bg: '#ffffff',
    panel: '#f8fafc',
    text: '#0f172a',
    muted: '#64748b',
    accent: config?.accent_color || config?.primary_color || '#3b82f6',
    border: '#e2e8f0',
    inputBg: '#ffffff',
    primaryBtnBg: config?.primary_color || '#111827',
    primaryBtnText: '#ffffff',
    primaryBtnHover: config?.accent_color || '#3b82f6',
    headingFont: 'Inter, -apple-system, sans-serif',
    bodyFont: 'Inter, -apple-system, sans-serif',
    radius: 10,
    navLabel: 'Online Giving',
    logoText: config?.name || 'Church',
    logoAccent: '',
  };
}

// ---------- main ----------------------------------------------------------
export default function PublicGivingPage() {
  const { churchSlug } = useParams();
  const [config, setConfig] = useState(null);
  const [loadError, setLoadError] = useState('');
  const [amount, setAmount] = useState(100);
  const [customAmount, setCustomAmount] = useState('');
  const [fund, setFund] = useState('Tithes');
  const [frequency, setFrequency] = useState('one-time');
  const [coverFees, setCoverFees] = useState(true);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [completed, setCompleted] = useState(null);
  const [error, setError] = useState('');
  const [stripeReady, setStripeReady] = useState(false);
  const [cardComplete, setCardComplete] = useState(false);

  // Stripe refs — live outside React state since the SDK holds DOM handles
  const stripeRef = useRef(null);
  const cardElementRef = useRef(null);
  const cardMountRef = useRef(null);

  // 1. Load church config
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await fetch(`${API_URL}/churches/${churchSlug}/public-config`);
        if (!res.ok) throw new Error(`Church not found: ${churchSlug}`);
        const cfg = await res.json();
        if (!alive) return;
        setConfig(cfg);
        setFund(cfg.funds?.[0] || 'General Fund');
        setCoverFees(!!cfg.cover_fees_default);
      } catch (e) {
        if (alive) setLoadError(e.message || 'Failed to load giving page');
      }
    })();
    return () => { alive = false; };
  }, [churchSlug]);

  // 1b. Dynamic browser tab title + favicon per church. Restores the original
  // Solomon AI title/favicon when the user navigates away so this never
  // bleeds into other routes.
  useEffect(() => {
    if (!config) return;

    const originalTitle = document.title;
    const faviconLink =
      document.querySelector("link[rel~='icon']") || (() => {
        const l = document.createElement('link');
        l.rel = 'icon';
        document.head.appendChild(l);
        return l;
      })();
    const originalHref = faviconLink.getAttribute('href');
    const originalType = faviconLink.getAttribute('type');

    document.title = `Give to ${config.name}`;
    // Only Eden Church has a hardcoded custom favicon for now. Other tenants
    // keep the default Solomon AI favicon until the per-church branding
    // upload lands.
    if (config.slug === 'eden-church') {
      faviconLink.setAttribute('type', 'image/svg+xml');
      faviconLink.setAttribute('href', '/eden-logo.svg');
    }

    return () => {
      document.title = originalTitle;
      if (originalHref !== null) {
        faviconLink.setAttribute('href', originalHref);
      }
      if (originalType !== null) {
        faviconLink.setAttribute('type', originalType);
      } else {
        faviconLink.removeAttribute('type');
      }
    };
  }, [config]);

  const theme = useMemo(() => resolveTheme(config), [config]);

  // 2. Initialize Stripe Elements once config arrives
  useEffect(() => {
    if (!config || stripeRef.current) return;
    let disposed = false;
    (async () => {
      try {
        await loadStripeJs();
        const { publishable_key } = await fetch(`${API_URL}/stripe/elements/config`).then((r) => r.json());
        if (!publishable_key) throw new Error('Payments not configured');
        if (disposed) return;

        // Connect (BLOCKER #1): if the church has an active Connect account,
        // initialize Stripe with stripeAccount so the card element + later
        // confirmCardPayment talk to the connected account directly.
        const stripeOpts = config.connected_account_id
          ? { stripeAccount: config.connected_account_id }
          : undefined;
        const stripe = window.Stripe(publishable_key, stripeOpts);
        stripeRef.current = stripe;

        const elements = stripe.elements();
        const card = elements.create('card', {
          hidePostalCode: false,
          disableLink: true,
          style: {
            base: {
              fontSize: '16px',
              color: theme.text,
              fontFamily: theme.bodyFont,
              '::placeholder': { color: theme.muted },
              iconColor: theme.accent,
            },
            invalid: { color: '#ef4444', iconColor: '#ef4444' },
          },
        });
        cardElementRef.current = card;
        card.on('change', (e) => {
          setCardComplete(!!e.complete);
          setError(e.error?.message || '');
        });
        // Mount once the ref is available
        const tryMount = () => {
          if (cardMountRef.current) {
            card.mount(cardMountRef.current);
            setStripeReady(true);
          } else {
            requestAnimationFrame(tryMount);
          }
        };
        tryMount();
      } catch (e) {
        setError(e.message || 'Payment system failed to load');
      }
    })();
    return () => {
      disposed = true;
      try { cardElementRef.current?.destroy(); } catch { /* ignore */ }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config]);

  const finalAmount = useMemo(() => {
    const v = customAmount ? parseFloat(customAmount) : amount;
    return Number.isFinite(v) && v > 0 ? v : 0;
  }, [amount, customAmount]);

  const feeAmount = coverFees ? Math.round((finalAmount * 0.019 + 0.3) * 100) / 100 : 0;
  const totalCharge = Math.round((finalAmount + feeAmount) * 100) / 100;

  const handleGive = async () => {
    setError('');
    if (finalAmount < 1) return setError('Please enter an amount of at least $1.00');
    if (!firstName.trim() || !email.trim()) return setError('Please enter your name and email');
    if (!stripeReady || !cardComplete) return setError('Please enter your card details');

    setSubmitting(true);
    try {
      // Step 1 — create intent
      const intentRes = await fetch(`${API_URL}/stripe/create-payment-intent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: finalAmount,
          fund,
          frequency,
          donor_first_name: firstName.trim(),
          donor_last_name: lastName.trim(),
          donor_email: email.trim(),
          cover_fees: coverFees,
          church_slug: churchSlug,
          message: message.trim(),
        }),
      });
      if (!intentRes.ok) {
        const body = await intentRes.json().catch(() => ({}));
        throw new Error(body.detail || 'Could not start payment');
      }
      const { client_secret, payment_intent_id } = await intentRes.json();

      // Step 2 — confirm on-page
      const { error: stripeErr, paymentIntent } = await stripeRef.current.confirmCardPayment(
        client_secret,
        {
          payment_method: {
            card: cardElementRef.current,
            billing_details: {
              name: `${firstName} ${lastName}`.trim(),
              email: email.trim(),
            },
          },
        },
      );
      if (stripeErr) throw new Error(stripeErr.message);
      if (paymentIntent?.status !== 'succeeded') {
        throw new Error(`Payment not completed (status: ${paymentIntent?.status})`);
      }

      // Step 3 — persist server-side
      const confirmRes = await fetch(`${API_URL}/stripe/confirm-donation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payment_intent_id, church_slug: churchSlug }),
      });
      const confirm = await confirmRes.json();
      if (!confirmRes.ok) throw new Error(confirm.detail || 'Server could not record donation');

      setCompleted(confirm.donation || null);
    } catch (e) {
      setError(e.message || 'Something went wrong');
    } finally {
      setSubmitting(false);
    }
  };

  // ------- render: error / loading / confirmation / form ------------------
  if (loadError) {
    return (
      <div style={{ minHeight: '100vh', background: '#000', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24, fontFamily: 'system-ui, sans-serif' }}>
        <div style={{ textAlign: 'center' }}>
          <h1 style={{ fontSize: 24, margin: 0, marginBottom: 8 }}>Giving page unavailable</h1>
          <p style={{ color: '#888', margin: 0 }}>{loadError}</p>
        </div>
      </div>
    );
  }
  if (!config) {
    return <div style={{ minHeight: '100vh', background: '#000' }} data-testid="give-page-loading" />;
  }

  const shell = {
    minHeight: '100vh',
    background: theme.bg,
    color: theme.text,
    fontFamily: theme.bodyFont,
  };

  if (completed) {
    return (
      <div style={shell} data-testid="give-success">
        <TopNav theme={theme} />
        <main style={{ maxWidth: 560, margin: '0 auto', padding: '48px 24px' }}>
          <h1
            style={{
              fontFamily: theme.headingFont,
              fontStyle: 'italic',
              color: theme.accent,
              fontSize: 'clamp(2.5rem, 8vw, 4rem)',
              margin: 0,
              marginBottom: 12,
            }}
            data-testid="give-thankyou"
          >
            Thank you
          </h1>
          <p style={{ color: theme.muted, fontSize: 16, marginTop: 0, marginBottom: 32 }}>
            {firstName ? `${firstName}, your gift means everything.` : 'Your gift means everything.'}
          </p>
          <div style={{ background: theme.panel, border: `1px solid ${theme.border}`, padding: 24, borderRadius: theme.radius }}>
            <Receipt theme={theme} donation={completed} />
          </div>
          <p style={{ marginTop: 32, fontSize: 11, color: theme.muted, letterSpacing: '0.15em', textTransform: 'uppercase' }}>
            Powered by Solomon Pay
          </p>
        </main>
      </div>
    );
  }

  return (
    <div style={shell} data-testid="public-giving-page">
      {config.stripe_test_mode && <TestBanner theme={theme} />}
      <TopNav theme={theme} />
      <main style={{ maxWidth: 500, margin: '0 auto', padding: '32px 24px 96px' }}>
        <h1
          style={{
            fontFamily: theme.headingFont,
            fontStyle: theme.mode === 'eden' ? 'italic' : 'normal',
            color: theme.mode === 'eden' ? theme.accent : theme.text,
            fontSize: 'clamp(2.5rem, 8vw, 4rem)',
            margin: 0,
            marginBottom: 8,
          }}
          data-testid="give-page-title"
        >
          Give
        </h1>
        <p style={{ color: theme.muted, marginTop: 0, marginBottom: 36, fontSize: 16 }}>
          Every gift changes lives.
        </p>

        <Eyebrow theme={theme}>Amount</Eyebrow>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 16 }}>
          {config.preset_amounts.map((a) => (
            <PresetBtn
              key={a}
              theme={theme}
              selected={!customAmount && amount === a}
              onClick={() => { setAmount(a); setCustomAmount(''); }}
              testid={`give-preset-${a}`}
            >
              ${a}
            </PresetBtn>
          ))}
          <input
            type="number"
            inputMode="decimal"
            placeholder="Other"
            value={customAmount}
            onChange={(e) => setCustomAmount(e.target.value)}
            style={inputStyle(theme)}
            data-testid="give-custom-amount"
          />
        </div>

        <label
          onClick={() => setCoverFees((v) => !v)}
          style={{
            display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
            background: coverFees ? `rgba(45,212,191,0.08)` : theme.panel,
            border: `1px solid ${coverFees ? theme.accent : theme.border}`,
            borderRadius: theme.radius,
            cursor: 'pointer',
            marginBottom: 24,
          }}
          data-testid="give-cover-fees"
        >
          <span
            style={{
              width: 18, height: 18, borderRadius: theme.radius === 0 ? 0 : 3,
              border: `1.5px solid ${coverFees ? theme.accent : theme.muted}`,
              background: coverFees ? theme.accent : 'transparent',
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              color: '#000', fontSize: 12, fontWeight: 700,
              flexShrink: 0,
            }}
          >{coverFees ? '✓' : ''}</span>
          <span style={{ fontSize: 13, color: theme.text }}>
            Cover the {formatCurrency(feeAmount)} processing fee so 100% of my gift reaches the church
          </span>
        </label>

        <Eyebrow theme={theme}>Fund</Eyebrow>
        <select
          value={fund}
          onChange={(e) => setFund(e.target.value)}
          style={{ ...inputStyle(theme), marginBottom: 20 }}
          data-testid="give-fund-select"
        >
          {config.funds.map((f) => (<option key={f} value={f}>{f}</option>))}
        </select>

        <Eyebrow theme={theme}>Frequency</Eyebrow>
        <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
          {config.frequencies.map((freq) => (
            <button
              key={freq}
              onClick={() => setFrequency(freq)}
              style={{
                flex: 1,
                padding: '10px 8px',
                background: frequency === freq ? `rgba(45,212,191,0.08)` : 'transparent',
                color: frequency === freq ? theme.accent : theme.text,
                border: `1px solid ${frequency === freq ? theme.accent : theme.border}`,
                borderRadius: theme.radius,
                fontSize: 11,
                fontWeight: 600,
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                cursor: 'pointer',
                fontFamily: theme.bodyFont,
              }}
              data-testid={`give-freq-${freq}`}
            >
              {freq === 'one-time' ? 'One-Time' : freq}
            </button>
          ))}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
          <input
            placeholder="First name"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            style={inputStyle(theme)}
            data-testid="give-first-name"
            autoComplete="given-name"
          />
          <input
            placeholder="Last name"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            style={inputStyle(theme)}
            data-testid="give-last-name"
            autoComplete="family-name"
          />
        </div>
        <input
          type="email"
          placeholder="Email for receipt"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ ...inputStyle(theme), marginBottom: 20 }}
          data-testid="give-email"
          autoComplete="email"
        />

        <Eyebrow theme={theme}>Card</Eyebrow>
        <div
          ref={cardMountRef}
          style={{
            ...inputStyle(theme),
            padding: 14,
            minHeight: 46,
            marginBottom: 24,
          }}
          data-testid="give-card-element"
        />

        {error && (
          <div
            style={{ marginBottom: 16, padding: 12, border: `1px solid #ef4444`, color: '#ef4444', fontSize: 13, borderRadius: theme.radius }}
            data-testid="give-error"
          >
            {error}
          </div>
        )}

        <button
          onClick={handleGive}
          disabled={submitting || finalAmount < 1}
          data-testid="give-submit"
          style={{
            width: '100%',
            padding: '16px 20px',
            background: theme.primaryBtnBg,
            color: theme.primaryBtnText,
            border: 'none',
            borderRadius: theme.radius,
            fontFamily: theme.bodyFont,
            fontSize: 12,
            fontWeight: 600,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            cursor: submitting ? 'not-allowed' : 'pointer',
            opacity: submitting || finalAmount < 1 ? 0.6 : 1,
            transition: 'background 0.15s ease',
          }}
          onMouseEnter={(e) => { if (!submitting) e.currentTarget.style.background = theme.primaryBtnHover; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = theme.primaryBtnBg; }}
        >
          {submitting ? 'Processing…' : `Give ${formatCurrency(totalCharge)}`}
        </button>

        <p style={{ marginTop: 28, fontSize: 11, color: theme.muted, letterSpacing: '0.15em', textTransform: 'uppercase', textAlign: 'center' }}>
          Powered by Solomon Pay
        </p>
      </main>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* sub-components                                                      */
/* ------------------------------------------------------------------ */

function TopNav({ theme }) {
  return (
    <nav
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '18px 24px',
        borderBottom: `1px solid ${theme.border}`,
      }}
    >
      <div style={{ fontFamily: theme.headingFont, fontSize: 20, letterSpacing: '0.04em' }}>
        <span>{theme.logoText}</span>
        {theme.logoAccent && (
          <span style={{ fontStyle: 'italic', color: theme.accent, marginLeft: 2 }}>{theme.logoAccent}</span>
        )}
      </div>
      <div style={{ fontSize: 11, color: theme.muted, letterSpacing: '0.15em', textTransform: 'uppercase' }}>
        {theme.navLabel}
      </div>
    </nav>
  );
}

function Eyebrow({ theme, children }) {
  return (
    <div
      style={{
        fontFamily: theme.bodyFont,
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: '0.25em',
        textTransform: 'uppercase',
        color: theme.accent,
        marginBottom: 10,
      }}
    >
      {children}
    </div>
  );
}

function PresetBtn({ theme, selected, onClick, children, testid }) {
  return (
    <button
      onClick={onClick}
      data-testid={testid}
      style={{
        padding: '14px 8px',
        background: selected ? `rgba(45,212,191,0.08)` : 'transparent',
        color: selected ? theme.accent : theme.text,
        border: `1px solid ${selected ? theme.accent : theme.border}`,
        borderRadius: theme.radius,
        fontFamily: theme.bodyFont,
        fontSize: 15,
        fontWeight: 600,
        cursor: 'pointer',
        transition: 'all 0.15s ease',
      }}
    >
      {children}
    </button>
  );
}

function inputStyle(theme) {
  return {
    width: '100%',
    padding: '12px 14px',
    background: theme.inputBg,
    color: theme.text,
    border: `1px solid ${theme.border}`,
    borderRadius: theme.radius,
    fontFamily: theme.bodyFont,
    fontSize: 15,
    outline: 'none',
    boxSizing: 'border-box',
  };
}

function TestBanner({ theme }) {
  return (
    <div
      style={{
        background: '#fef3c7',
        color: '#92400e',
        padding: '8px 16px',
        textAlign: 'center',
        fontSize: 12,
        fontFamily: theme.bodyFont,
        letterSpacing: '0.05em',
      }}
      data-testid="give-test-banner"
    >
      TEST MODE — Use card 4242 4242 4242 4242, any future date, any CVC
    </div>
  );
}

function Receipt({ theme, donation }) {
  const row = {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '10px 0',
    borderBottom: `1px solid ${theme.border}`,
    fontSize: 14,
    color: theme.text,
  };
  const last = { ...row, borderBottom: 'none' };
  if (!donation) {
    return <p style={{ color: theme.muted }}>Your receipt will be emailed shortly.</p>;
  }
  return (
    <div>
      <div style={row}>
        <span style={{ color: theme.muted }}>Gift</span>
        <span>{formatCurrency(donation.amount)}</span>
      </div>
      {donation.fee_amount > 0 && (
        <div style={row}>
          <span style={{ color: theme.muted }}>Fee covered</span>
          <span>{formatCurrency(donation.fee_amount)}</span>
        </div>
      )}
      <div style={row}>
        <span style={{ color: theme.muted }}>Total charged</span>
        <span style={{ fontWeight: 600 }}>{formatCurrency(donation.total_charged)}</span>
      </div>
      <div style={row}>
        <span style={{ color: theme.muted }}>Fund</span>
        <span>{donation.fund_name}</span>
      </div>
      {donation.card_brand && (
        <div style={row}>
          <span style={{ color: theme.muted }}>Card</span>
          <span style={{ textTransform: 'capitalize' }}>{donation.card_brand} •••• {donation.card_last_four}</span>
        </div>
      )}
      <div style={last}>
        <span style={{ color: theme.muted }}>Transaction</span>
        <span style={{ fontFamily: 'monospace', fontSize: 12 }}>
          {donation.stripe_payment_intent_id?.replace(/^pi_/, '').slice(0, 18)}…
        </span>
      </div>
    </div>
  );
}
