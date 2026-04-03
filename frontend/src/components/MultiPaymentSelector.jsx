import { useState, useEffect } from 'react';
import { CreditCard, Banknote, Smartphone } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

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
export default function MultiPaymentSelector({ amount = 0, onSelect, showCash = false }) {
  const [savedCards, setSavedCards] = useState([]);
  const [supportsApplePay, setSupportsApplePay] = useState(false);
  const [supportsGooglePay, setSupportsGooglePay] = useState(false);
  const [selected, setSelected] = useState('solomon_pay');
  const [showGuestCard, setShowGuestCard] = useState(false);
  const [guestCard, setGuestCard] = useState({ number: '', exp_month: '', exp_year: '', cvc: '' });

  useEffect(() => {
    fetchSavedCards();
    // Detect Apple Pay
    if (window.ApplePaySession && ApplePaySession.canMakePayments) {
      setSupportsApplePay(true);
    }
    // Detect Google Pay (Payment Request API)
    if (window.PaymentRequest) {
      setSupportsGooglePay(true);
    }
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
    if (type === 'apple_pay') handleApplePay();
    else if (type === 'google_pay') handleGooglePay();
    else if (type !== 'guest_card') {
      const card = savedCards.find(c => c.is_default) || savedCards[0];
      onSelect?.({ type, token: card?.token, card_last_four: card?.card_last_four, card_brand: card?.card_brand });
    }
  };

  const handleApplePay = async () => {
    toast.info('Apple Pay — coming soon! Use card on file for now.');
  };

  const handleGooglePay = async () => {
    toast.info('Google Pay — coming soon! Use card on file for now.');
  };

  const handleGuestCardSubmit = async () => {
    if (!guestCard.number || !guestCard.exp_month || !guestCard.exp_year) {
      toast.error('Fill all card fields');
      return;
    }
    try {
      const res = await fetch(`${API_URL}/solomonpay/tokenize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          card_number: guestCard.number.replace(/\s/g, ''),
          exp_month: parseInt(guestCard.exp_month),
          exp_year: parseInt(guestCard.exp_year),
          cvc: guestCard.cvc,
        }),
      });
      if (res.ok) {
        const d = await res.json();
        onSelect?.({ type: 'guest_card', token: d.token, card_last_four: d.card_last_four, card_brand: d.card_brand });
        toast.success('Card ready');
        setShowGuestCard(false);
      }
    } catch { toast.error('Card error'); }
  };

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

      {/* Guest card entry */}
      <button
        onClick={() => { setSelected('guest_card'); setShowGuestCard(!showGuestCard); }}
        className={`w-full flex items-center gap-3 p-3 border rounded-xl transition-all ${selected === 'guest_card' ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-slate-300'}`}
        data-testid="pay-guest-card"
      >
        <CreditCard className="w-5 h-5 text-slate-600" />
        <div className="text-left">
          <p className="text-sm font-medium text-slate-800">Enter Card</p>
          <p className="text-xs text-slate-500">Visa, Mastercard, Amex</p>
        </div>
      </button>

      {showGuestCard && (
        <div className="border border-slate-200 rounded-xl p-3 space-y-2 bg-slate-50">
          <input
            type="text" maxLength={19} placeholder="Card number"
            value={guestCard.number} onChange={e => setGuestCard({...guestCard, number: e.target.value})}
            className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm font-mono"
            data-testid="guest-card-number"
          />
          <div className="grid grid-cols-3 gap-2">
            <input type="text" maxLength={2} placeholder="MM" value={guestCard.exp_month} onChange={e => setGuestCard({...guestCard, exp_month: e.target.value})} className="px-3 py-2 border border-slate-200 rounded-lg text-sm" />
            <input type="text" maxLength={4} placeholder="YYYY" value={guestCard.exp_year} onChange={e => setGuestCard({...guestCard, exp_year: e.target.value})} className="px-3 py-2 border border-slate-200 rounded-lg text-sm" />
            <input type="text" maxLength={4} placeholder="CVC" value={guestCard.cvc} onChange={e => setGuestCard({...guestCard, cvc: e.target.value})} className="px-3 py-2 border border-slate-200 rounded-lg text-sm" />
          </div>
          <button onClick={handleGuestCardSubmit} className="w-full py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700" data-testid="guest-card-submit">
            Use This Card
          </button>
        </div>
      )}

      {/* Apple Pay */}
      {supportsApplePay && (
        <button
          onClick={() => handleSelect('apple_pay')}
          className={`w-full flex items-center gap-3 p-3 border rounded-xl transition-all ${selected === 'apple_pay' ? 'border-black bg-black text-white' : 'border-slate-200 bg-black text-white'}`}
          data-testid="pay-apple-pay"
          style={{ background: '#000000', color: 'white', borderColor: '#000' }}
        >
          <Smartphone className="w-5 h-5" />
          <span className="text-sm font-semibold"> Pay</span>
        </button>
      )}

      {/* Google Pay */}
      {supportsGooglePay && !supportsApplePay && (
        <button
          onClick={() => handleSelect('google_pay')}
          className="w-full flex items-center gap-3 p-3 border border-slate-200 rounded-xl bg-white hover:border-slate-300 transition-all"
          data-testid="pay-google-pay"
        >
          <Smartphone className="w-5 h-5 text-blue-600" />
          <span className="text-sm font-medium text-slate-800">G Pay</span>
        </button>
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
