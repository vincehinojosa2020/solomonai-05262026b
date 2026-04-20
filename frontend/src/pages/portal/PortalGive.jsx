import { useState, useEffect, useCallback } from 'react';
import { useOutletContext, useSearchParams } from 'react-router-dom';
import { usePolling } from '@/hooks/usePolling';
import { CreditCard, DollarSign, Download, CheckCircle, ChevronDown, MapPin, Flame, Heart } from 'lucide-react';
import { API_URL, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';
import { safeRedirect } from '@/utils/sanitize';
import SolomonPayForm from '@/components/SolomonPayForm';
import RecurringGivingManager from '@/components/RecurringGivingManager';
import GivingGoalTracker from '@/components/GivingGoalTracker';

export default function PortalGive() {
  const { user, memberData, refreshData, tenant } = useOutletContext();
  const [searchParams, setSearchParams] = useSearchParams();
  const [amount, setAmount] = useState('');
  const [fund, setFund] = useState('general');
  const [frequency, setFrequency] = useState('one-time');
  const [funds, setFunds] = useState([]);
  const [givingHistory, setGivingHistory] = useState([]);
  const [savedCards, setSavedCards] = useState([]);
  const [selectedSavedCard, setSelectedSavedCard] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [showPayment, setShowPayment] = useState(false);
  const [campuses, setCampuses] = useState([]);
  const [selectedCampus, setSelectedCampus] = useState(user?.home_campus_id || tenant?.id || '');
  const [isMultiCampus, setIsMultiCampus] = useState(false);
  const [coverFees, setCoverFees] = useState(false);
  const [stripeConfig, setStripeConfig] = useState(null);
  const [stripeLoading, setStripeLoading] = useState(false);

  const quickAmounts = [25, 50, 100, 250];
  const giveAmount = parseFloat(amount) || 0;
  const processingFee = coverFees ? Math.round((giveAmount * 0.019 + 0.30) * 100) / 100 : 0;
  const totalCharge = Math.round((giveAmount + processingFee) * 100) / 100;

  useEffect(() => {
    fetchFunds();
    fetchGivingHistory();
    fetchSavedPaymentMethods();
    fetchCampuses();
    // Check Stripe configuration
    fetch(`${API_URL}/stripe/config`).then(r => r.ok ? r.json() : null).then(d => { if (d) setStripeConfig(d); }).catch(() => {});
  }, []);

  const fetchSavedPaymentMethods = async () => {
    try {
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/portal/payment-methods`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const cards = data.payment_methods || [];
        setSavedCards(cards);
        const defaultCard = cards.find(c => c.is_default);
        if (defaultCard) setSelectedSavedCard(defaultCard.id);
      }
    } catch (error) {
      console.error('Failed to fetch saved cards:', error);
    }
  };

  const fetchCampuses = async () => {
    try {
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/portal/campuses`, { headers: { 'Authorization': `Bearer ${token}` } });
      if (res.ok) {
        const data = await res.json();
        setCampuses(data.campuses || []);
        setIsMultiCampus(data.is_multi_campus || false);
      }
    } catch (error) {
      console.error('Failed to fetch campuses:', error);
    }
  };

  const fetchFunds = async () => {
    try {
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/portal/giving/funds`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setFunds(data.funds || []);
      }
    } catch (error) {
      console.error('Failed to fetch funds:', error);
    }
  };

  const fetchGivingHistory = async () => {
    try {
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/portal/giving/history?limit=50`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setGivingHistory(data.donations || []);
      }
    } catch (error) {
      console.error('Failed to fetch giving history:', error);
    }
  };

  // Process giving with saved card
  const handleGiveWithSavedCard = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    const card = savedCards.find(c => c.id === selectedSavedCard);
    if (!card) {
      toast.error('Please select a payment method');
      return;
    }
    setIsLoading(true);
    try {
      const token = sessionStorage.getItem('session_token');
      const fundObj = funds.find(f => f.id === fund);
      const res = await fetch(`${API_URL}/solomonpay/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          amount: totalCharge,
          payment_method_type: 'card',
          token: card.token,
          cover_fees: coverFees,
          context: 'donation',
          fund_id: fund,
          fund_name: fundObj?.name || 'General Fund',
          frequency,
          description: `${frequency === 'one-time' ? 'One-time' : frequency} gift to ${fundObj?.name || 'General Fund'}`,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Payment failed');
      }
      setShowSuccessMessage(true);
      toast.success(`Thank you! ${card.card_brand} ••••${card.card_last_four} charged ${formatCurrency(totalCharge)}`);
      setAmount('');
      setCoverFees(false);
      setTimeout(() => fetchGivingHistory(), 500);
    } catch (err) {
      toast.error(err.message || 'Payment failed. Please try again.');
    }
    setIsLoading(false);
  };

  const handleGive = () => {
    if (!amount || parseFloat(amount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    // If saved card selected, go directly via Solomon Pay
    if (selectedSavedCard) {
      handleGiveWithSavedCard();
      return;
    }
    setShowPayment(true);
  };

  // Stripe Checkout flow
  const handleStripeCheckout = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    setStripeLoading(true);
    try {
      const token = sessionStorage.getItem('session_token');
      const fundObj = funds.find(f => f.id === fund);
      const res = await fetch(`${API_URL}/stripe/checkout/giving`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          amount: parseFloat(amount),
          fund_name: fundObj?.name || 'General Fund',
          cover_fees: coverFees,
          origin_url: window.location.origin,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to create checkout');
      }
      const data = await res.json();
      if (data.url) {
        // Stripe checkout URL — validate before redirect
        if (data.url.startsWith('https://checkout.stripe.com/')) {
          window.location.href = data.url;
        } else {
          window.location.href = safeRedirect(data.url);
        }
      } else if (data.mode === 'simulated') {
        toast.info('Stripe is in demo mode. Using Solomon Pay.');
        setShowPayment(true);
      }
    } catch (err) {
      toast.error(err.message || 'Checkout failed');
    } finally {
      setStripeLoading(false);
    }
  };

  // Handle return from Stripe success
  useEffect(() => {
    const sessionId = searchParams.get('session_id');
    if (sessionId) {
      // Poll for payment status
      let attempts = 0;
      const poll = async () => {
        try {
          const res = await fetch(`${API_URL}/stripe/checkout/status/${sessionId}`);
          if (res.ok) {
            const data = await res.json();
            if (data.payment_status === 'paid') {
              setShowSuccessMessage(true);
              toast.success('Thank you! Your donation has been received.');
              setSearchParams({});
              setTimeout(() => fetchGivingHistory(), 500);
              return;
            }
            if (data.status === 'expired') {
              toast.error('Payment session expired. Please try again.');
              setSearchParams({});
              return;
            }
          }
        } catch {}
        attempts++;
        if (attempts < 5) setTimeout(poll, 2000);
      };
      poll();
    }
  }, [searchParams]);

  const handleSolomonPaySuccess = async (cardData) => {
    const fundObj = funds.find(f => f.id === fund);
    const token = sessionStorage.getItem('session_token');
    const response = await fetch(`${API_URL}/solomonpay/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({
        ...cardData,
        amount: totalCharge,
        cover_fees: coverFees,
        context: 'donation',
        fund_id: fund,
        fund_name: fundObj?.name || 'General Fund',
        frequency,
        description: `${frequency === 'one-time' ? 'One-time' : frequency} gift to ${fundObj?.name || 'General Fund'}`,
      }),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Payment failed');
    }
    setShowPayment(false);
    setShowSuccessMessage(true);
    toast.success(`Thank you for your generous gift of ${formatCurrency(totalCharge)}!`);
    setAmount('');
    setCoverFees(false);
    setTimeout(() => fetchGivingHistory(), 500);
    setTimeout(() => fetchSavedPaymentMethods(), 500);
  };

  // Calculate giving streak (consecutive weeks with donations)
  const givingStreak = (() => {
    if (!givingHistory || givingHistory.length === 0) return 0;
    const now = new Date();
    const weekMs = 7 * 24 * 60 * 60 * 1000;
    // Group donations by week number
    const weeks = new Set();
    givingHistory.forEach(d => {
      const date = new Date(d.donation_date);
      const weekStart = new Date(date);
      weekStart.setDate(weekStart.getDate() - weekStart.getDay());
      weeks.add(`${weekStart.getFullYear()}-${weekStart.getMonth()}-${weekStart.getDate()}`);
    });
    // Count consecutive weeks from current week backwards
    let streak = 0;
    let checkDate = new Date(now);
    for (let i = 0; i < 52; i++) {
      const weekStart = new Date(checkDate);
      weekStart.setDate(weekStart.getDate() - weekStart.getDay());
      const key = `${weekStart.getFullYear()}-${weekStart.getMonth()}-${weekStart.getDate()}`;
      if (weeks.has(key)) {
        streak++;
        checkDate = new Date(checkDate.getTime() - weekMs);
      } else if (i === 0) {
        // Allow current week to not count yet (grace period)
        checkDate = new Date(checkDate.getTime() - weekMs);
      } else {
        break;
      }
    }
    return streak;
  })();

  const ytdGiving = memberData?.giving?.ytd_total || 0;
  const lastGift = memberData?.giving?.last_gift;
  const recurring = memberData?.giving?.recurring;

  const TaxStatementDownloader = () => {
    const [showYears, setShowYears] = useState(false);
    const [downloading, setDownloading] = useState(null);
    const currentYear = new Date().getFullYear();
    const years = [currentYear, currentYear - 1, currentYear - 2, currentYear - 3];

    const downloadStatement = async (year) => {
      setDownloading(year);
      try {
        const res = await fetch(`${API_URL}/portal/giving/statement/${year}/pdf`);
        if (!res.ok) { toast.error('Failed to generate statement'); return; }
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `giving_statement_${year}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        toast.success(`${year} statement downloaded`);
        setShowYears(false);
      } catch { toast.error('Download failed'); }
      finally { setDownloading(null); }
    };

    return (
      <div className="relative" data-testid="tax-statement-section">
        <button onClick={() => setShowYears(!showYears)} className="portal-download-btn w-full" data-testid="download-statement-btn" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
          <Download className="w-4 h-4" /> Download Year-End Giving Summary <ChevronDown className={`w-3 h-3 transition-transform ${showYears ? 'rotate-180' : ''}`} />
        </button>
        {showYears && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg z-10 overflow-hidden" data-testid="year-selector">
            {years.map(y => (
              <button key={y} onClick={() => downloadStatement(y)} disabled={downloading === y} className="w-full px-4 py-2.5 text-sm text-left hover:bg-slate-50 transition-colors flex items-center justify-between" data-testid={`download-year-${y}`}>
                <span>{y} Statement</span>
                {downloading === y && <span className="text-xs text-slate-400">Generating...</span>}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="portal-give" data-testid="portal-give">
      <div className="portal-page-header">
        <h1 className="portal-page-title">Give to {tenant?.name || 'Your Church'}</h1>
        <p className="portal-page-subtitle">Your generosity changes lives. Every gift matters.</p>
      </div>

      {/* Success Message Banner */}
      {showSuccessMessage && (
        <div className="portal-success-banner" data-testid="donation-success">
          <CheckCircle className="w-6 h-6 text-green-500" />
          <div>
            <h3>Thank you for your generous gift!</h3>
            <p>Your donation has been received and will be reflected in your giving history.</p>
          </div>
          <button onClick={() => setShowSuccessMessage(false)} className="portal-close-btn">&times;</button>
        </div>
      )}

      <div className="portal-give-container">
        {/* Giving Form */}
        <div className="portal-give-form">
          {/* Amount */}
          <div className="portal-form-section">
            <label className="portal-form-label">AMOUNT</label>
            <div className="portal-amount-input-wrapper">
              <span className="portal-currency-symbol">$</span>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="portal-amount-input"
                data-testid="give-amount-input"
              />
            </div>
            <div className="portal-quick-amounts">
              {quickAmounts.map((qa) => (
                <button
                  key={qa}
                  onClick={() => setAmount(qa.toString())}
                  className={`portal-quick-amount ${amount === qa.toString() ? 'active' : ''}`}
                  data-testid={`quick-amount-${qa}`}
                >
                  ${qa}
                </button>
              ))}
              <button
                onClick={() => setAmount('')}
                className={`portal-quick-amount ${!quickAmounts.includes(parseInt(amount)) && amount ? 'active' : ''}`}
              >
                Other
              </button>
            </div>
          </div>

          {/* Campus (for multi-campus churches) */}
          {isMultiCampus && campuses.length > 1 && (
            <div className="portal-form-section">
              <label className="portal-form-label flex items-center gap-1"><MapPin className="w-3 h-3" /> CAMPUS</label>
              <select
                value={selectedCampus}
                onChange={(e) => setSelectedCampus(e.target.value)}
                className="portal-select"
                data-testid="give-campus-select"
              >
                {campuses.map((c) => (
                  <option key={c.id} value={c.id}>{c.label || c.name}</option>
                ))}
              </select>
            </div>
          )}

          {/* Fund */}
          <div className="portal-form-section">
            <label className="portal-form-label">FUND</label>
            <select
              value={fund}
              onChange={(e) => setFund(e.target.value)}
              className="portal-select"
              data-testid="give-fund-select"
            >
              {funds.map((f) => (
                <option key={f.id} value={f.id}>{f.name}</option>
              ))}
            </select>
          </div>

          {/* Frequency */}
          <div className="portal-form-section">
            <label className="portal-form-label">FREQUENCY</label>
            <select
              value={frequency}
              onChange={(e) => setFrequency(e.target.value)}
              className="portal-select"
              data-testid="give-frequency-select"
            >
              <option value="one-time">One time</option>
              <option value="weekly">Weekly</option>
              <option value="biweekly">Every 2 weeks</option>
              <option value="monthly">Monthly</option>
              <option value="annually">Annually</option>
            </select>
          </div>

          {/* Payment Method */}
          <div className="portal-form-section">
            <label className="portal-form-label">PAYMENT</label>
            
            {/* Saved Cards */}
            {savedCards.length > 0 && !showPayment && (
              <div className="portal-saved-cards" style={{ marginBottom: '12px' }}>
                {savedCards.map((card) => (
                  <button
                    key={card.id}
                    onClick={() => { setSelectedSavedCard(card.id === selectedSavedCard ? null : card.id); setShowPayment(false); }}
                    className={`portal-saved-card ${selectedSavedCard === card.id ? 'active' : ''}`}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '10px',
                      padding: '10px 14px',
                      border: selectedSavedCard === card.id ? '2px solid #0f172a' : '1px solid #e2e8f0',
                      borderRadius: '8px',
                      background: selectedSavedCard === card.id ? '#f8fafc' : 'white',
                      width: '100%', marginBottom: '8px', cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                    data-testid={`saved-card-${card.id}`}
                  >
                    <CreditCard className="w-4 h-4" style={{ color: '#0f172a' }} />
                    <span style={{ fontWeight: '500' }}>{card.card_brand} &bull;&bull;&bull;&bull; {card.card_last_four}</span>
                    <span style={{ fontSize: '12px', color: '#94a3b8', marginLeft: 'auto' }}>
                      {card.is_default && 'Default'}
                    </span>
                    {selectedSavedCard === card.id && (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    )}
                  </button>
                ))}
                <button
                  onClick={() => { setSelectedSavedCard(null); setShowPayment(true); }}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '8px',
                    padding: '8px 14px', border: '1px dashed #d1d5db', borderRadius: '8px',
                    background: 'transparent', width: '100%', cursor: 'pointer',
                    fontSize: '13px', color: '#6b7280'
                  }}
                  data-testid="use-new-card-btn"
                >
                  <CreditCard className="w-4 h-4" /> Enter a new card
                </button>
              </div>
            )}
            
            {showPayment && (
              <div style={{ marginTop: 8 }}>
                <SolomonPayForm
                  amount={totalCharge}
                  onSuccess={handleSolomonPaySuccess}
                  onCancel={() => setShowPayment(false)}
                  context="donation"
                />
              </div>
            )}
          </div>

          {/* Cover Processing Fees — Luntz Style */}
          {giveAmount > 0 && !showPayment && (
            <div
              style={{
                display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px',
                background: coverFees ? '#eff6ff' : '#f8fafc',
                border: `1px solid ${coverFees ? '#93c5fd' : '#e2e8f0'}`,
                borderRadius: 8, cursor: 'pointer', transition: 'all 0.2s', marginBottom: 12
              }}
              onClick={() => setCoverFees(!coverFees)}
              data-testid="give-cover-fees-toggle"
            >
              <div style={{
                width: 20, height: 20, borderRadius: 4, border: `2px solid ${coverFees ? '#2563eb' : '#d1d5db'}`,
                background: coverFees ? '#2563eb' : '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                transition: 'all 0.2s', flexShrink: 0
              }}>
                {coverFees && <span style={{ color: '#fff', fontSize: 12, fontWeight: 700 }}>&#10003;</span>}
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ fontSize: 13, fontWeight: 700, color: coverFees ? '#1e40af' : '#374151', margin: 0 }}>
                  I'd like to cover the processing fee ({formatCurrency(Math.round((giveAmount * 0.019 + 0.30) * 100) / 100)})
                </p>
                <p style={{ fontSize: 11, color: coverFees ? '#60a5fa' : '#9ca3af', margin: 0, lineHeight: 1.4 }}>
                  When you cover the fee, 100% of your gift reaches the church. Not one penny lost.
                </p>
              </div>
            </div>
          )}

          {/* Total with fee breakdown */}
          {giveAmount > 0 && coverFees && !showPayment && (
            <div style={{ padding: '10px 16px', background: '#f0f9ff', borderRadius: 8, marginBottom: 12, fontSize: 13 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#374151', marginBottom: 2 }}>
                <span>Your gift</span>
                <span>{formatCurrency(giveAmount)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#2563eb', marginBottom: 2, fontWeight: 600 }}>
                <span>Processing fee covered</span>
                <span>{formatCurrency(processingFee)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, color: '#0f172a', paddingTop: 6, borderTop: '1px solid #bfdbfe' }}>
                <span>Total charge</span>
                <span>{formatCurrency(totalCharge)}</span>
              </div>
            </div>
          )}

          {/* Submit Button */}
          {!showPayment && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <button
                onClick={handleGive}
                disabled={isLoading || !amount}
                className="portal-give-btn"
                data-testid="give-submit-btn"
                style={isLoading ? { opacity: 0.6, cursor: 'not-allowed' } : {}}
              >
                {isLoading ? 'Processing...' : `Give ${amount ? formatCurrency(totalCharge) : ''} with Solomon Pay`}
              </button>
              {stripeConfig?.stripe_live && (
                <button
                  onClick={handleStripeCheckout}
                  disabled={stripeLoading || !amount}
                  data-testid="stripe-checkout-btn"
                  style={{
                    width: '100%', padding: '14px 24px', borderRadius: 12,
                    background: '#635bff', color: '#fff', border: 'none',
                    fontSize: 16, fontWeight: 700, cursor: stripeLoading ? 'not-allowed' : 'pointer',
                    opacity: stripeLoading || !amount ? 0.6 : 1,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  }}
                >
                  {stripeLoading ? 'Redirecting...' : `Pay ${amount ? formatCurrency(totalCharge) : ''} with Stripe`}
                </button>
              )}
            </div>
          )}
        </div>

        {/* Giving Summary */}
        <div className="portal-give-summary">

          {/* Giving Streak — Frank Luntz Style */}
          {givingStreak > 0 && (
            <div style={{
              padding: '16px 18px', borderRadius: 12, marginBottom: 20,
              background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 50%, #fbbf24 100%)',
              border: '1px solid #f59e0b', position: 'relative', overflow: 'hidden'
            }} data-testid="giving-streak">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                <Flame style={{ width: 22, height: 22, color: '#dc2626' }} />
                <span style={{ fontSize: 28, fontWeight: 800, color: '#92400e', letterSpacing: '-0.02em' }}>
                  {givingStreak} Week{givingStreak !== 1 ? 's' : ''}
                </span>
              </div>
              <p style={{ fontSize: 14, fontWeight: 700, color: '#78350f', margin: 0, marginBottom: 4 }}>
                {givingStreak >= 12 ? "That's not a habit — that's a lifestyle." :
                 givingStreak >= 4 ? "You're building something beautiful." :
                 "Every streak starts with the first step."}
              </p>
              <p style={{ fontSize: 12, color: '#92400e', margin: 0, lineHeight: 1.4 }}>
                {givingStreak >= 12 ? `${givingStreak} consecutive weeks of faithfulness. Your consistency is transforming this community.` :
                 givingStreak >= 4 ? `${givingStreak} weeks of faithful giving and counting. Keep this streak alive.` :
                 `You've given ${givingStreak} week${givingStreak !== 1 ? 's' : ''} in a row. Consistency is the seed of transformation.`}
              </p>
            </div>
          )}

          <h3 className="portal-summary-title">Your giving this year</h3>
          
          <div className="portal-summary-stat">
            <span className="portal-summary-label">YTD Given</span>
            <span className="portal-summary-value">{formatCurrency(ytdGiving)}</span>
          </div>

          {lastGift && (
            <div className="portal-summary-stat">
              <span className="portal-summary-label">Last Gift</span>
              <span className="portal-summary-value-sm">
                {formatCurrency(lastGift.amount)} — {lastGift.fund_name || 'General Fund'} — {lastGift.donation_date}
              </span>
            </div>
          )}

          {recurring && (
            <div className="portal-summary-stat">
              <span className="portal-summary-label">Recurring</span>
              <span className="portal-summary-value-sm flex items-center gap-1">
                {formatCurrency(recurring.amount)}/{recurring.frequency}
                <CheckCircle className="w-4 h-4 text-green-500" />
                Active
              </span>
            </div>
          )}

          <TaxStatementDownloader />
        </div>
      </div>

      {/* Giving Goal Tracker */}
      <div className="mt-8">
        <GivingGoalTracker />
      </div>

      {/* Recurring Giving Management */}
      <div className="mt-8">
        <RecurringGivingManager funds={funds} />
      </div>

      {/* Giving History */}
      <div className="portal-section mt-8">
        <h3 className="portal-section-title">Giving History</h3>
        {givingHistory.length > 0 ? (
          <div className="portal-history-table">
            <div className="portal-history-header">
              <span>Date</span>
              <span>Fund</span>
              <span>Amount</span>
              <span>Method</span>
            </div>
            {givingHistory.slice(0, 10).map((donation, idx) => (
              <div key={donation.id || `donation-${idx}`} className="portal-history-row" data-testid={`donation-row-${idx}`}>
                <span>{donation.donation_date}</span>
                <span>{donation.fund_name}</span>
                <span className="font-semibold">{formatCurrency(donation.amount)}</span>
                <span className="capitalize">{donation.payment_method}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="portal-empty-state" data-testid="no-donations">
            <DollarSign className="w-12 h-12 text-slate-300" />
            <p className="text-slate-500 mt-4">No giving history yet</p>
            <p className="text-slate-400 text-sm">Your donations will appear here after your first gift.</p>
          </div>
        )}
      </div>
    </div>
  );
}
