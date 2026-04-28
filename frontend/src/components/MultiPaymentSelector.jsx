import { useState, useEffect } from 'react';
import { CreditCard, Banknote } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import StripePaymentRequestButton from '@/components/payments/StripePaymentRequestButton';

/**
 * MultiPaymentSelector — Supports:
 *   - Solomon Pay (card on file)
 *   - Guest card (tokenized via SolomonPayForm)
 *   - Apple Pay (Payment Request API, shows only if supported)
 *   - Google Pay (Payment Request API)
 *   - Cash (admin marks as paid)
 *
 * Props:
 *   amount: number
 *   onSelect: callback(paymentMethod: { type, token?, card_last_four? })
 *   showCash: boolean (show cash option — for admin use)
 */
export default function MultiPaymentSelector({ amount = 0, onSelect, showCash = false, label = 'Payment' }) {
  const [savedCards, setSavedCards] = useState([]);
  const [supportsWallet, setSupportsWallet] = useState(false);
  const [selected, setSelected] = useState('solomon_pay');

  useEffect(() => {
    fetchSavedCards();
    // Show wallet button if the browser exposes Apple Pay OR the Payment Request API
    const hasApplePay =
      typeof window.ApplePaySession !== 'undefined' &&
      typeof window.ApplePaySession.canMakePayments === 'function';
    const hasPaymentRequest = typeof window.PaymentRequest !== 'undefined';
    setSupportsWallet(hasApplePay || hasPaymentRequest);
  }, []);

  const fetchSavedCards = async () => {
    try {
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/portal/payment-methods`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const d = await res.json();
        setSavedCards(d.payment_methods || []);
        if (d.payment_methods?.length > 0) setSelected('card_on_file');
      }
    } catch (e) { console.error(e); }
  };

  const handleSelect = (type) => {
    setSelected(type);
    if (type !== 'guest_card' && type !== 'wallet') {
      const card = savedCards.find(c => c.is_default) || savedCards[0];
      onSelect?.({ type, token: card?.token, card_last_four: card?.card_last_four, card_brand: card?.card_brand });
    }
  };

  const handleWalletSuccess = (payload) => {
    setSelected('wallet');
    onSelect?.(payload);
    toast.success(payload.is_mock ? 'Payment confirmed (demo)' : 'Payment confirmed');
  };

  // NOTE: Raw-card entry was REMOVED 2026-04-28 (PCI scope reduction —
  // BLOCKER #4 from production audit). Card capture flows through Stripe
  // Elements on the giving pages; this component now only offers
  // Apple/Google Pay (Stripe Payment Request Button), card-on-file, and cash.

  return (
    <div className="space-y-2" data-testid="multi-payment-selector">
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Payment Method</p>

      {/* Card on file */}
      {savedCards.length > 0 && (
        <button
          onClick={() => handleSelect('card_on_file')}
          className={`w-full flex items-center gap-3 p-3 border rounded-xl transition-all ${selected === 'card_on_file' ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-slate-300'}`}
          data-testid="pay-card-on-file"
        >
          <CreditCard className="w-5 h-5 text-blue-600" />
          <div className="text-left">
            <p className="text-sm font-medium text-slate-800">
              {savedCards.find(c => c.is_default)?.card_brand || savedCards[0].card_brand} ••••{savedCards.find(c => c.is_default)?.card_last_four || savedCards[0].card_last_four}
            </p>
            <p className="text-xs text-slate-500">Card on file</p>
          </div>
          {selected === 'card_on_file' && <span className="ml-auto text-blue-600 text-lg">✓</span>}
        </button>
      )}

      {/* Guest card entry was removed for PCI scope reduction (2026-04-28).
          Donors who don't have a card on file are routed to the Stripe
          Elements giving page or use Apple/Google Pay below. */}

      {/* Apple Pay / Google Pay (Stripe Payment Request Button — auto-detects wallet) */}
      {supportsWallet && amount >= 1 && (
        <div className="pt-1" data-testid="wallet-pay-slot">
          <StripePaymentRequestButton
            amount={amount}
            label={label}
            onSuccess={handleWalletSuccess}
          />
        </div>
      )}

      {/* Cash */}
      {showCash && (
        <button
          onClick={() => { setSelected('cash'); onSelect?.({ type: 'cash' }); }}
          className={`w-full flex items-center gap-3 p-3 border rounded-xl transition-all ${selected === 'cash' ? 'border-green-500 bg-green-50' : 'border-slate-200 hover:border-slate-300'}`}
          data-testid="pay-cash"
        >
          <Banknote className="w-5 h-5 text-green-600" />
          <div className="text-left">
            <p className="text-sm font-medium text-slate-800">Cash</p>
            <p className="text-xs text-slate-500">Mark as paid manually</p>
          </div>
          {selected === 'cash' && <span className="ml-auto text-green-600 text-lg">✓</span>}
        </button>
      )}
    </div>
  );
}
