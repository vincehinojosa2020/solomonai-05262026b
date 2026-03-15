import { useState, useEffect } from 'react';
import { useOutletContext, useSearchParams } from 'react-router-dom';
import { CreditCard, Building2, DollarSign, Download, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { API_URL, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';

export default function PortalGive() {
  const { user, memberData, refreshData } = useOutletContext();
  const [searchParams, setSearchParams] = useSearchParams();
  const [amount, setAmount] = useState('');
  const [fund, setFund] = useState('general');
  const [frequency, setFrequency] = useState('one-time');
  const [paymentMethod, setPaymentMethod] = useState('card');
  const [funds, setFunds] = useState([]);
  const [givingHistory, setGivingHistory] = useState([]);
  const [savedCards, setSavedCards] = useState([]);
  const [selectedSavedCard, setSelectedSavedCard] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);

  const quickAmounts = [25, 50, 100, 250];

  useEffect(() => {
    fetchFunds();
    fetchGivingHistory();
    fetchSavedPaymentMethods();
    
    // Handle Stripe redirect
    const status = searchParams.get('status');
    const sessionId = searchParams.get('session_id');
    
    if (status === 'success' && sessionId) {
      // Confirm payment and create donation record
      confirmPayment(sessionId);
    } else if (status === 'cancelled') {
      toast.error('Donation was cancelled');
      // Clear URL params
      setSearchParams({});
    }
  }, []);

  const fetchSavedPaymentMethods = async () => {
    try {
      const res = await fetch(`${API_URL}/payments/methods`);
      if (res.ok) {
        const data = await res.json();
        setSavedCards(data.payment_methods || []);
      }
    } catch (error) {
      console.error('Failed to fetch saved cards:', error);
    }
  };

  useEffect(() => {
    fetchFunds();
    fetchGivingHistory();
    
    // Handle Stripe redirect
    const status = searchParams.get('status');
    const sessionId = searchParams.get('session_id');
    
    if (status === 'success' && sessionId) {
      // Confirm payment and create donation record
      confirmPayment(sessionId);
    } else if (status === 'cancelled') {
      toast.error('Donation was cancelled');
      // Clear URL params
      setSearchParams({});
    }
  }, []);

  const confirmPayment = async (sessionId) => {
    try {
      const res = await fetch(`${API_URL}/payments/status/${sessionId}`, {
        
      });
      
      if (res.ok) {
        const data = await res.json();
        if (data.payment_status === 'paid') {
          setShowSuccessMessage(true);
          toast.success('Thank you for your generous donation!');
          // Refresh giving history
          setTimeout(() => {
            fetchGivingHistory();
          }, 1000);
        }
      }
    } catch (error) {
      console.error('Failed to confirm payment:', error);
    } finally {
      // Clear URL params
      setSearchParams({});
    }
  };

  const fetchFunds = async () => {
    try {
      const res = await fetch(`${API_URL}/funds`);
      if (res.ok) {
        const data = await res.json();
        setFunds(data);
        if (data.length > 0) setFund(data[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch funds:', error);
    }
  };

  const fetchGivingHistory = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/giving/history`);
      if (res.ok) {
        const data = await res.json();
        setGivingHistory(data.donations || []);
      }
    } catch (error) {
      console.error('Failed to fetch giving history:', error);
    }
  };

  const handleGive = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    setIsLoading(true);
    try {
      // Use existing Stripe checkout flow
      const response = await fetch(`${API_URL}/payments/donate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({
          package_id: 'custom',
          custom_amount: parseFloat(amount),
          fund_id: fund,
          origin_url: window.location.href,
          recurring: frequency !== 'one-time',
          donor_name: user?.name
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create checkout session');
      }

      const data = await response.json();
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch (error) {
      toast.error('Unable to process donation. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const ytdGiving = memberData?.giving?.ytd_total || 0;
  const lastGift = memberData?.giving?.last_gift;
  const recurring = memberData?.giving?.recurring;

  return (
    <div className="portal-give" data-testid="portal-give">
      <div className="portal-page-header">
        <h1 className="portal-page-title">Give to Abundant Church</h1>
        <p className="portal-page-subtitle">Securely give online using your preferred method</p>
      </div>

      {/* Success Message Banner */}
      {showSuccessMessage && (
        <div className="portal-success-banner" data-testid="donation-success">
          <CheckCircle className="w-6 h-6 text-green-500" />
          <div>
            <h3>Thank you for your generous gift!</h3>
            <p>Your donation has been received and will be reflected in your giving history.</p>
          </div>
          <button onClick={() => setShowSuccessMessage(false)} className="portal-close-btn">×</button>
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
            <label className="portal-form-label">PAYMENT METHOD</label>
            
            {/* Saved Cards */}
            {savedCards.length > 0 && (
              <div className="portal-saved-cards" style={{ marginBottom: '12px' }}>
                <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px' }}>Saved Cards</p>
                {savedCards.map((card) => (
                  <button
                    key={card.id}
                    onClick={() => {
                      setSelectedSavedCard(card.id);
                      setPaymentMethod('saved');
                    }}
                    className={`portal-saved-card ${selectedSavedCard === card.id ? 'active' : ''}`}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '10px 14px',
                      border: selectedSavedCard === card.id ? '2px solid #3b82f6' : '1px solid #e2e8f0',
                      borderRadius: '8px',
                      background: selectedSavedCard === card.id ? '#eff6ff' : 'white',
                      width: '100%',
                      marginBottom: '8px',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                    data-testid={`saved-card-${card.id}`}
                  >
                    <CreditCard className="w-4 h-4" style={{ color: '#3b82f6' }} />
                    <span style={{ fontWeight: '500' }}>{card.card_brand} •••• {card.card_last_four}</span>
                    <span style={{ fontSize: '12px', color: '#94a3b8', marginLeft: 'auto' }}>
                      Exp {card.card_exp_month}/{card.card_exp_year}
                    </span>
                    {card.is_default && (
                      <span style={{ 
                        fontSize: '10px', 
                        background: '#dcfce7', 
                        color: '#16a34a', 
                        padding: '2px 6px', 
                        borderRadius: '10px' 
                      }}>
                        Default
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
            
            <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px' }}>
              {savedCards.length > 0 ? 'Or use a new payment method' : 'Choose payment method'}
            </p>
            <div className="portal-payment-methods">
              <button
                onClick={() => {
                  setPaymentMethod('card');
                  setSelectedSavedCard(null);
                }}
                className={`portal-payment-method ${paymentMethod === 'card' && !selectedSavedCard ? 'active' : ''}`}
                data-testid="payment-method-card"
              >
                <CreditCard className="w-4 h-4" />
                Card / ACH
              </button>
              <button
                onClick={() => {
                  setPaymentMethod('paypal');
                  setSelectedSavedCard(null);
                }}
                className={`portal-payment-method ${paymentMethod === 'paypal' ? 'active' : ''}`}
              >
                <span className="text-blue-600 font-bold text-sm">P</span>
                PayPal
              </button>
              <button
                onClick={() => {
                  setPaymentMethod('venmo');
                  setSelectedSavedCard(null);
                }}
                className={`portal-payment-method ${paymentMethod === 'venmo' ? 'active' : ''}`}
              >
                <span className="text-blue-500 font-bold text-sm">V</span>
                Venmo
              </button>
              <button
                onClick={() => {
                  setPaymentMethod('zelle');
                  setSelectedSavedCard(null);
                }}
                className={`portal-payment-method ${paymentMethod === 'zelle' ? 'active' : ''}`}
              >
                <span className="text-purple-600 font-bold text-sm">Z</span>
                Zelle
              </button>
            </div>
          </div>

          {/* Submit Button */}
          <button
            onClick={handleGive}
            disabled={isLoading || !amount}
            className="portal-give-btn"
            data-testid="give-submit-btn"
          >
            {isLoading ? 'Processing...' : `Give ${amount ? `$${amount}` : ''} →`}
          </button>
        </div>

        {/* Giving Summary */}
        <div className="portal-give-summary">
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

          <button className="portal-download-btn" data-testid="download-statement-btn">
            <Download className="w-4 h-4" />
            Download Tax Statement
          </button>
        </div>
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
              <div key={idx} className="portal-history-row" data-testid={`donation-row-${idx}`}>
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
