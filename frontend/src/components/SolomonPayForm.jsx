import { useState, useCallback } from 'react';
import { CreditCard, Lock, Shield, Loader2 } from 'lucide-react';

const detectCardBrand = (number) => {
  const n = number.replace(/\s/g, '');
  if (/^4/.test(n)) return 'Visa';
  if (/^5[1-5]/.test(n) || /^2[2-7]/.test(n)) return 'Mastercard';
  if (/^3[47]/.test(n)) return 'Amex';
  if (/^6(?:011|5)/.test(n)) return 'Discover';
  return '';
};

const formatCardNumber = (value) => {
  const digits = value.replace(/\D/g, '').slice(0, 16);
  return digits.replace(/(.{4})/g, '$1 ').trim();
};

const formatExpiry = (value) => {
  const digits = value.replace(/\D/g, '').slice(0, 4);
  if (digits.length >= 3) return digits.slice(0, 2) + '/' + digits.slice(2);
  return digits;
};

export default function SolomonPayForm({ amount, onSuccess, onCancel, context = 'donation', isProcessing = false }) {
  const [cardNumber, setCardNumber] = useState('');
  const [expiry, setExpiry] = useState('');
  const [cvv, setCvv] = useState('');
  const [cardholderName, setCardholderName] = useState('');
  const [billingZip, setBillingZip] = useState('');
  const [saveCard, setSaveCard] = useState(false);
  const [coverFees, setCoverFees] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const brand = detectCardBrand(cardNumber);
  const isAmex = brand === 'Amex';
  const processingFee = coverFees ? Math.round((amount * 0.025 + 0.30) * 100) / 100 : 0;
  const totalAmount = Math.round((amount + processingFee) * 100) / 100;

  const isValid = cardNumber.replace(/\s/g, '').length >= 15
    && expiry.length === 5
    && cvv.length >= 3
    && cardholderName.trim().length >= 2
    && billingZip.length === 5;

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    if (!isValid || loading) return;

    setLoading(true);
    setError('');

    const payload = {
      card_last_four: cardNumber.replace(/\s/g, '').slice(-4),
      card_brand: brand || 'Unknown',
      card_exp_month: expiry.split('/')[0],
      card_exp_year: expiry.split('/')[1],
      cardholder_name: cardholderName.trim(),
      billing_zip: billingZip,
      save_card: saveCard,
      amount: totalAmount,
      cover_fees: coverFees,
      context: context,
    };

    try {
      if (onSuccess) await onSuccess(payload);
    } catch (err) {
      setError(err.message || 'Payment could not be processed. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [cardNumber, expiry, cvv, cardholderName, billingZip, saveCard, coverFees, totalAmount, amount, brand, context, isValid, loading, onSuccess]);

  const inputStyle = {
    width: '100%', padding: '12px 14px', fontSize: 15, border: '1px solid #d1d5db',
    borderRadius: 8, outline: 'none', transition: 'border-color 0.15s',
    fontFamily: "'SF Mono', 'Fira Code', 'Consolas', monospace", background: '#fff', color: '#0f172a',
  };

  const labelStyle = { display: 'block', fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 6, letterSpacing: '0.02em' };

  return (
    <div data-testid="solomonpay-form" style={{ maxWidth: 420, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, paddingBottom: 16, borderBottom: '1px solid #e5e7eb' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 36, height: 36, borderRadius: 8, background: 'linear-gradient(135deg, #0f172a, #1e3a5f)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <CreditCard style={{ width: 18, height: 18, color: '#60a5fa' }} />
          </div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: '#0f172a', letterSpacing: '-0.01em' }}>SolomonPay</div>
            <div style={{ fontSize: 11, color: '#6b7280', fontWeight: 500 }}>Secure payment</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5, color: '#059669', fontSize: 12, fontWeight: 500 }}>
          <Lock style={{ width: 13, height: 13 }} />
          <span>Encrypted</span>
        </div>
      </div>

      {error && (
        <div data-testid="solomonpay-error" style={{ padding: '10px 14px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, color: '#dc2626', fontSize: 13, marginBottom: 16 }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Card Number */}
        <div style={{ marginBottom: 16 }}>
          <label style={labelStyle}>Card number</label>
          <div style={{ position: 'relative' }}>
            <input
              data-testid="solomonpay-card-number"
              type="text"
              inputMode="numeric"
              placeholder="1234 5678 9012 3456"
              value={cardNumber}
              onChange={(e) => setCardNumber(formatCardNumber(e.target.value))}
              maxLength={19}
              style={inputStyle}
              autoComplete="cc-number"
            />
            {brand && (
              <span style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', fontSize: 12, fontWeight: 600, color: '#6b7280', background: '#f3f4f6', padding: '2px 8px', borderRadius: 4 }}>
                {brand}
              </span>
            )}
          </div>
        </div>

        {/* Expiry + CVV row */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
          <div>
            <label style={labelStyle}>Expiration</label>
            <input
              data-testid="solomonpay-expiry"
              type="text"
              inputMode="numeric"
              placeholder="MM/YY"
              value={expiry}
              onChange={(e) => setExpiry(formatExpiry(e.target.value))}
              maxLength={5}
              style={inputStyle}
              autoComplete="cc-exp"
            />
          </div>
          <div>
            <label style={labelStyle}>CVV</label>
            <input
              data-testid="solomonpay-cvv"
              type="text"
              inputMode="numeric"
              placeholder={isAmex ? '1234' : '123'}
              value={cvv}
              onChange={(e) => setCvv(e.target.value.replace(/\D/g, '').slice(0, isAmex ? 4 : 3))}
              maxLength={isAmex ? 4 : 3}
              style={inputStyle}
              autoComplete="cc-csc"
            />
          </div>
        </div>

        {/* Cardholder Name */}
        <div style={{ marginBottom: 16 }}>
          <label style={labelStyle}>Cardholder name</label>
          <input
            data-testid="solomonpay-name"
            type="text"
            placeholder="Full name on card"
            value={cardholderName}
            onChange={(e) => setCardholderName(e.target.value)}
            style={{ ...inputStyle, fontFamily: "'Inter', -apple-system, sans-serif" }}
            autoComplete="cc-name"
          />
        </div>

        {/* Billing ZIP */}
        <div style={{ marginBottom: 20 }}>
          <label style={labelStyle}>Billing ZIP code</label>
          <input
            data-testid="solomonpay-zip"
            type="text"
            inputMode="numeric"
            placeholder="12345"
            value={billingZip}
            onChange={(e) => setBillingZip(e.target.value.replace(/\D/g, '').slice(0, 5))}
            maxLength={5}
            style={{ ...inputStyle, maxWidth: 140 }}
            autoComplete="postal-code"
          />
        </div>

        {/* Save card checkbox */}
        <label style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10, cursor: 'pointer' }}>
          <input
            data-testid="solomonpay-save-card"
            type="checkbox"
            checked={saveCard}
            onChange={(e) => setSaveCard(e.target.checked)}
            style={{ width: 16, height: 16, accentColor: '#0f172a' }}
          />
          <span style={{ fontSize: 13, color: '#374151' }}>Save this card for future use</span>
        </label>

        {/* Cover processing fees */}
        {context === 'donation' && (
          <label style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20, cursor: 'pointer' }} data-testid="cover-fees-toggle">
            <input
              type="checkbox"
              checked={coverFees}
              onChange={(e) => setCoverFees(e.target.checked)}
              style={{ width: 16, height: 16, accentColor: '#0f172a' }}
            />
            <span style={{ fontSize: 13, color: '#374151' }}>
              Cover processing fees {coverFees && <span style={{ color: '#16a34a', fontWeight: 600 }}>(+${processingFee.toFixed(2)})</span>}
            </span>
          </label>
        )}

        {/* Beta notice */}
        <div data-testid="solomonpay-beta-notice" style={{ padding: '10px 14px', background: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: 8, marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
            <Shield style={{ width: 14, height: 14, color: '#0284c7', flexShrink: 0, marginTop: 1 }} />
            <p style={{ fontSize: 12, color: '#0369a1', lineHeight: 1.5, margin: 0 }}>
              SolomonPay is in beta. Your card information is securely stored and will be charged once payment processing goes live.
            </p>
          </div>
        </div>

        {/* Submit */}
        <button
          data-testid="solomonpay-submit"
          type="submit"
          disabled={!isValid || loading || isProcessing}
          style={{
            width: '100%', padding: '14px 24px', fontSize: 15, fontWeight: 600,
            color: '#fff', background: (!isValid || loading) ? '#94a3b8' : '#0f172a',
            border: 'none', borderRadius: 10, cursor: (!isValid || loading) ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            transition: 'background 0.15s',
          }}
        >
          {(loading || isProcessing) ? (
            <>
              <Loader2 style={{ width: 18, height: 18, animation: 'spin 1s linear infinite' }} />
              Processing...
            </>
          ) : (
            <>
              <Lock style={{ width: 15, height: 15 }} />
              {amount ? `Pay $${parseFloat(amount).toFixed(2)} with SolomonPay` : 'Pay with SolomonPay'}
            </>
          )}
        </button>

        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            data-testid="solomonpay-cancel"
            style={{
              width: '100%', padding: '10px 24px', fontSize: 14, fontWeight: 500,
              color: '#6b7280', background: 'transparent', border: 'none',
              cursor: 'pointer', marginTop: 8,
            }}
          >
            Cancel
          </button>
        )}
      </form>

      {/* Footer */}
      <div style={{ textAlign: 'center', marginTop: 20, paddingTop: 16, borderTop: '1px solid #e5e7eb' }}>
        <span style={{ fontSize: 11, color: '#94a3b8', fontWeight: 500, letterSpacing: '0.02em' }}>
          Powered by SolomonPay
        </span>
      </div>
    </div>
  );
}
