import { useState, useEffect, useCallback } from 'react';
import { useOutletContext, useSearchParams } from 'react-router-dom';
import { usePolling } from '@/hooks/usePolling';
import { CreditCard, DollarSign, Download, CheckCircle, ChevronDown, MapPin } from 'lucide-react';
import { API_URL, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';
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

  const quickAmounts = [25, 50, 100, 250];

  useEffect(() => {
    fetchFunds();
    fetchGivingHistory();
    fetchSavedPaymentMethods();
    fetchCampuses();
  }, []);

  const fetchSavedPaymentMethods = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/payment-methods`);
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
    fetchSavedPaymentMethods();
    fetchCampuses();
  }, []);

  const fetchCampuses = async () => {
    try {
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/portal/campuses`, { headers: { 'Authorization': `Bearer ${token}` } });
      if (res.ok) {
        const d = await res.json();
        setCampuses(d.campuses || []);
        setIsMultiCampus(d.is_multi_campus || false);
        if (!selectedCampus && d.home_campus_id) setSelectedCampus(d.home_campus_id);
      }
    } catch (e) { console.error(e); }
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

  const handleGive = () => {
    if (!amount || parseFloat(amount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }
    setShowPayment(true);
  };

  const handleSolomonPaySuccess = async (cardData) => {
    const fundObj = funds.find(f => f.id === fund);
    const response = await fetch(`${API_URL}/solomonpay/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...cardData,
        amount: parseFloat(amount),
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
    toast.success(`Thank you for your generous gift of $${amount}!`);
    setAmount('');
    setTimeout(() => fetchGivingHistory(), 500);
    setTimeout(() => fetchSavedPaymentMethods(), 500);
  };

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

          {/* How You Give */}
          <div className="portal-form-section">
            <label className="portal-form-label">PAYMENT</label>
            
            {/* Saved Cards */}
            {savedCards.length > 0 && !showPayment && (
              <div className="portal-saved-cards" style={{ marginBottom: '12px' }}>
                <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px' }}>Saved Cards</p>
                {savedCards.map((card) => (
                  <button
                    key={card.id}
                    onClick={() => setSelectedSavedCard(card.id === selectedSavedCard ? null : card.id)}
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
                    <span style={{ fontWeight: '500' }}>{card.card_brand} •••• {card.card_last_four}</span>
                    <span style={{ fontSize: '12px', color: '#94a3b8', marginLeft: 'auto' }}>
                      Exp {card.card_exp_month}/{card.card_exp_year}
                    </span>
                    {card.is_default && (
                      <span style={{ fontSize: '10px', background: '#dcfce7', color: '#16a34a', padding: '2px 6px', borderRadius: '10px' }}>
                        Default
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
            
            {showPayment ? (
              <div style={{ marginTop: 8 }}>
                <SolomonPayForm
                  amount={parseFloat(amount)}
                  onSuccess={handleSolomonPaySuccess}
                  onCancel={() => setShowPayment(false)}
                  context="donation"
                />
              </div>
            ) : (
              <p style={{ fontSize: '13px', color: '#64748b' }}>
                Secure payment powered by SolomonPay
              </p>
            )}
          </div>

          {/* Submit Button */}
          {!showPayment && (
            <button
              onClick={handleGive}
              disabled={isLoading || !amount}
              className="portal-give-btn"
              data-testid="give-submit-btn"
            >
              {isLoading ? 'Processing...' : `Give ${amount ? `$${amount}` : ''} with SolomonPay`}
            </button>
          )}
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
