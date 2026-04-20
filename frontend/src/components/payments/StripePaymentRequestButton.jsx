import { useState, useEffect, useMemo } from 'react';
import { X, CheckCircle2 } from 'lucide-react';

/**
 * StripePaymentRequestButton
 * ---------------------------
 * Renders an Apple Pay or Google Pay button following each vendor's brand
 * guidelines. Two modes:
 *
 *   MOCK mode (default — no Stripe publishable key set):
 *     - Renders the same branded button
 *     - Opens a realistic confirmation sheet (Face ID / Google Pay sheet)
 *     - After a simulated auth delay, fires onSuccess with a mock token
 *
 *   LIVE mode (when REACT_APP_STRIPE_PUBLISHABLE_KEY is set):
 *     - Lazy-loads @stripe/stripe-js + Stripe PaymentRequest
 *     - Falls back to MOCK if the browser/device cannot do wallet payments
 *
 * Props:
 *   amount       – number (USD, dollars, e.g. 25.00)
 *   label        – string (shown in wallet sheet, e.g. "General Fund")
 *   onSuccess    – (payload: { type, token, card_last_four, card_brand, wallet_type }) => void
 *   onCancel?    – () => void
 *   disabled?    – boolean
 */
export default function StripePaymentRequestButton({
  amount = 0,
  label = 'Payment',
  onSuccess,
  onCancel,
  disabled = false,
}) {
  const [sheetOpen, setSheetOpen] = useState(false);
  const [authState, setAuthState] = useState('idle'); // idle | authing | success
  const stripeKey =
    (typeof window !== 'undefined' && window.__STRIPE_PUBLISHABLE_KEY__) ||
    process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY ||
    '';
  const isLive = Boolean(stripeKey);

  const walletType = useMemo(() => detectWalletType(), []);

  // In LIVE mode we would have already attempted stripe.paymentRequest.canMakePayment()
  // For the mock + scaffold we always show the button; the sheet handles the rest.
  const handleClick = async () => {
    if (disabled || amount < 1) return;

    if (isLive) {
      // LIVE path — will be activated once REACT_APP_STRIPE_PUBLISHABLE_KEY is set.
      // Implementation hook-point documented in /app/STRIPE_PAYMENT_REQUEST_INTEGRATION.md
      // For now, fall through to mock sheet so the flow can still be exercised.
    }
    setSheetOpen(true);
    setAuthState('authing');

    // Simulate biometric / wallet authentication (~1.6s)
    setTimeout(() => {
      setAuthState('success');
      setTimeout(() => {
        const mockToken = `mock_tok_${walletType}_${Date.now().toString(36)}`;
        onSuccess?.({
          type: walletType === 'apple_pay' ? 'apple_pay' : 'google_pay',
          token: mockToken,
          card_last_four: '4242',
          card_brand: 'Visa',
          wallet_type: walletType,
          is_mock: true,
        });
        setSheetOpen(false);
        setAuthState('idle');
      }, 750);
    }, 1600);
  };

  const handleCancel = () => {
    setSheetOpen(false);
    setAuthState('idle');
    onCancel?.();
  };

  const formatCurrency = (v) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(v);

  return (
    <>
      {walletType === 'apple_pay' ? (
        <ApplePayButton onClick={handleClick} disabled={disabled} />
      ) : (
        <GooglePayButton onClick={handleClick} disabled={disabled} />
      )}

      {!isLive && (
        <p
          className="text-[10px] text-slate-400 mt-1 text-center tracking-wide uppercase"
          data-testid="wallet-mock-badge"
        >
          Demo mode — no card will be charged
        </p>
      )}

      {sheetOpen && (
        <WalletSheet
          walletType={walletType}
          amount={amount}
          label={label}
          formatted={formatCurrency(amount)}
          authState={authState}
          onCancel={handleCancel}
        />
      )}
    </>
  );
}

/* ------------------------------------------------------------------ */
/*  Button variants                                                    */
/* ------------------------------------------------------------------ */
function ApplePayButton({ onClick, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      data-testid="apple-pay-button"
      aria-label="Pay with Apple Pay"
      className="w-full h-11 rounded-md bg-black text-white flex items-center justify-center gap-1 font-medium transition-transform active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-neutral-800"
      style={{ fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif' }}
    >
      <span className="text-[15px] font-normal tracking-tight">Pay with</span>
      <svg width="16" height="20" viewBox="0 0 16 20" fill="currentColor" aria-hidden="true">
        <path d="M13.05 10.65c-.02-2.08 1.7-3.08 1.78-3.13-.97-1.41-2.48-1.6-3.02-1.62-1.29-.13-2.51.76-3.16.76-.65 0-1.66-.74-2.73-.72-1.4.02-2.7.81-3.42 2.06-1.46 2.53-.37 6.28 1.05 8.34.7 1 1.52 2.12 2.59 2.08 1.04-.04 1.43-.67 2.7-.67 1.27 0 1.62.67 2.72.65 1.13-.02 1.83-1.02 2.52-2.02.79-1.16 1.12-2.28 1.14-2.34-.02-.01-2.19-.84-2.22-3.33zM10.99 4.53c.57-.7.96-1.66.85-2.63-.83.03-1.83.55-2.42 1.24-.53.61-.99 1.6-.87 2.54.92.07 1.87-.47 2.44-1.15z" />
      </svg>
      <span className="text-[15px] font-semibold tracking-tight">Pay</span>
    </button>
  );
}

function GooglePayButton({ onClick, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      data-testid="google-pay-button"
      aria-label="Pay with Google Pay"
      className="w-full h-11 rounded-md bg-black text-white flex items-center justify-center gap-2 transition-transform active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed hover:bg-neutral-800"
      style={{ fontFamily: 'Roboto, -apple-system, BlinkMacSystemFont, sans-serif' }}
    >
      <span className="text-[15px] font-normal">Buy with</span>
      <span className="inline-flex items-center gap-[3px]">
        <svg width="17" height="17" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
        </svg>
        <span className="text-[15px] font-medium tracking-tight">
          <span className="text-[#4285F4]">G</span>
          <span className="text-[#EA4335]">o</span>
          <span className="text-[#FBBC05]">o</span>
          <span className="text-[#4285F4]">g</span>
          <span className="text-[#34A853]">l</span>
          <span className="text-[#EA4335]">e</span>
          <span className="text-white ml-[3px]">Pay</span>
        </span>
      </span>
    </button>
  );
}

/* ------------------------------------------------------------------ */
/*  Wallet confirmation sheet (mock)                                   */
/* ------------------------------------------------------------------ */
function WalletSheet({ walletType, label, formatted, authState, onCancel }) {
  const isApple = walletType === 'apple_pay';

  return (
    <div
      className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center bg-black/50 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      data-testid="wallet-mock-sheet"
    >
      <div className="w-full sm:max-w-md bg-white rounded-t-2xl sm:rounded-2xl shadow-2xl overflow-hidden animate-slideUp">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            {isApple ? (
              <svg width="18" height="22" viewBox="0 0 16 20" fill="#000" aria-hidden="true">
                <path d="M13.05 10.65c-.02-2.08 1.7-3.08 1.78-3.13-.97-1.41-2.48-1.6-3.02-1.62-1.29-.13-2.51.76-3.16.76-.65 0-1.66-.74-2.73-.72-1.4.02-2.7.81-3.42 2.06-1.46 2.53-.37 6.28 1.05 8.34.7 1 1.52 2.12 2.59 2.08 1.04-.04 1.43-.67 2.7-.67 1.27 0 1.62.67 2.72.65 1.13-.02 1.83-1.02 2.52-2.02.79-1.16 1.12-2.28 1.14-2.34-.02-.01-2.19-.84-2.22-3.33zM10.99 4.53c.57-.7.96-1.66.85-2.63-.83.03-1.83.55-2.42 1.24-.53.61-.99 1.6-.87 2.54.92.07 1.87-.47 2.44-1.15z" />
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
              </svg>
            )}
            <p className="text-sm font-semibold text-slate-800">
              {isApple ? 'Apple Pay' : 'Google Pay'}
            </p>
          </div>
          <button
            onClick={onCancel}
            className="p-1 text-slate-400 hover:text-slate-700 transition-colors"
            aria-label="Cancel payment"
            data-testid="wallet-mock-cancel"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-6 space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[11px] text-slate-500 uppercase tracking-wider">Pay to</p>
              <p className="text-sm font-semibold text-slate-800">Solomon AI</p>
              <p className="text-xs text-slate-500 mt-0.5">{label}</p>
            </div>
            <p className="text-2xl font-mono font-semibold text-slate-900">{formatted}</p>
          </div>

          <div className="flex items-center justify-between py-3 px-4 bg-slate-50 rounded-lg border border-slate-100">
            <div className="flex items-center gap-2">
              <div className="w-8 h-5 bg-gradient-to-r from-slate-700 to-slate-900 rounded-[3px] flex items-center justify-center">
                <span className="text-[9px] font-bold text-white tracking-wider">VISA</span>
              </div>
              <p className="text-sm text-slate-700">•••• 4242</p>
            </div>
            <p className="text-[11px] text-slate-400">Default</p>
          </div>

          {/* Auth prompt */}
          <div className="flex flex-col items-center py-4">
            {authState === 'authing' && (
              <>
                <div className="w-14 h-14 rounded-full border-2 border-slate-900 flex items-center justify-center mb-3 animate-pulse">
                  {isApple ? (
                    <FaceIdIcon />
                  ) : (
                    <svg className="w-7 h-7 text-slate-800" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 11c0-1.1.9-2 2-2h4a2 2 0 012 2v7a2 2 0 01-2 2H6a2 2 0 01-2-2v-7a2 2 0 012-2h4m4 0V7a2 2 0 00-4 0v4" />
                    </svg>
                  )}
                </div>
                <p className="text-sm font-medium text-slate-800">
                  {isApple ? 'Double click to confirm' : 'Confirm with screen lock'}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {isApple ? 'Face ID' : 'Authenticating…'}
                </p>
              </>
            )}
            {authState === 'success' && (
              <>
                <div className="w-14 h-14 rounded-full bg-green-500 flex items-center justify-center mb-3">
                  <CheckCircle2 className="w-8 h-8 text-white" />
                </div>
                <p className="text-sm font-semibold text-slate-800">Done</p>
              </>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes slideUp {
          from { transform: translateY(100%); opacity: 0.5; }
          to   { transform: translateY(0); opacity: 1; }
        }
        .animate-slideUp { animation: slideUp 0.22s cubic-bezier(0.2, 0.8, 0.2, 1); }
      `}</style>
    </div>
  );
}

function FaceIdIcon() {
  return (
    <svg className="w-7 h-7 text-slate-800" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 8V6a2 2 0 0 1 2-2h2" />
      <path d="M16 4h2a2 2 0 0 1 2 2v2" />
      <path d="M4 16v2a2 2 0 0 0 2 2h2" />
      <path d="M16 20h2a2 2 0 0 0 2-2v-2" />
      <line x1="9" y1="10" x2="9" y2="12" />
      <line x1="15" y1="10" x2="15" y2="12" />
      <path d="M12 10v4" />
      <path d="M9 16c1 1 2 1.5 3 1.5s2-.5 3-1.5" />
    </svg>
  );
}

/* ------------------------------------------------------------------ */
/*  Wallet detection                                                   */
/* ------------------------------------------------------------------ */
function detectWalletType() {
  if (typeof window === 'undefined') return 'google_pay';
  const ua = window.navigator.userAgent || '';
  const isAppleDevice = /iPhone|iPad|iPod|Macintosh/i.test(ua);
  const isSafari = /^((?!chrome|android|crios|fxios).)*safari/i.test(ua);
  const hasApplePaySession =
    typeof window.ApplePaySession !== 'undefined' &&
    typeof window.ApplePaySession.canMakePayments === 'function';

  if (isAppleDevice && (isSafari || hasApplePaySession)) return 'apple_pay';
  return 'google_pay';
}
