import { useState, useEffect } from 'react';
import { X, CreditCard, DollarSign, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { API_URL } from '@/lib/utils';

const DONATION_AMOUNTS = [
  { id: 'tithe_25', amount: 25, label: '$25' },
  { id: 'tithe_50', amount: 50, label: '$50' },
  { id: 'tithe_100', amount: 100, label: '$100' },
  { id: 'tithe_250', amount: 250, label: '$250' },
  { id: 'tithe_500', amount: 500, label: '$500' },
  { id: 'tithe_1000', amount: 1000, label: '$1,000' },
];

export default function DonationCheckout({ onClose, preselectedFund }) {
  const [step, setStep] = useState('amount'); // amount, info, processing, success, error
  const [selectedAmount, setSelectedAmount] = useState(null);
  const [customAmount, setCustomAmount] = useState('');
  const [selectedFund, setSelectedFund] = useState(preselectedFund || 'general');
  const [donorName, setDonorName] = useState('');
  const [donorEmail, setDonorEmail] = useState('');
  const [isRecurring, setIsRecurring] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [funds, setFunds] = useState([]);

  useEffect(() => {
    // Fetch funds
    fetch(`${API_URL}/funds`)
      .then(res => res.json())
      .then(data => setFunds(data))
      .catch(err => console.error('Failed to fetch funds:', err));
    
    // Check if returning from Stripe
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    const status = urlParams.get('status');
    
    if (sessionId && status === 'success') {
      setStep('processing');
      pollPaymentStatus(sessionId);
    } else if (status === 'cancelled') {
      setStep('amount');
    }
  }, []);

  const pollPaymentStatus = async (sessionId, attempts = 0) => {
    const maxAttempts = 10;
    
    if (attempts >= maxAttempts) {
      setStep('success'); // Assume success after max attempts
      return;
    }

    try {
      const response = await fetch(`${API_URL}/payments/status/${sessionId}`);
      const data = await response.json();
      
      if (data.payment_status === 'paid') {
        setStep('success');
        // Clear URL params
        window.history.replaceState({}, '', window.location.pathname);
        return;
      } else if (data.status === 'expired') {
        setError('Payment session expired. Please try again.');
        setStep('error');
        return;
      }
      
      // Continue polling
      setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), 2000);
    } catch (err) {
      console.error('Error checking payment status:', err);
      setStep('error');
      setError('Error checking payment status.');
    }
  };

  const getFinalAmount = () => {
    if (selectedAmount) {
      return selectedAmount.amount;
    }
    return parseFloat(customAmount) || 0;
  };

  const handleProceedToCheckout = async () => {
    const amount = getFinalAmount();
    
    if (amount < 1) {
      setError('Please enter an amount of at least $1.00');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_URL}/payments/donate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          package_id: selectedAmount ? selectedAmount.id : 'custom',
          custom_amount: selectedAmount ? null : amount,
          fund_id: selectedFund,
          origin_url: window.location.origin,
          recurring: isRecurring,
          donor_name: donorName || null,
          donor_email: donorEmail || null,
        }),
      });
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to create checkout');
      }
      
      const data = await response.json();
      
      // Redirect to Stripe Checkout
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        throw new Error('No checkout URL received');
      }
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  // Processing state
  if (step === 'processing') {
    return (
      <div className="slide-panel-overlay" onClick={onClose}>
        <div className="slide-panel" onClick={e => e.stopPropagation()}>
          <div className="flex flex-col items-center justify-center h-full p-8">
            <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-4" />
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Processing Your Gift</h3>
            <p className="text-sm text-slate-500 text-center">Please wait while we confirm your donation...</p>
          </div>
        </div>
      </div>
    );
  }

  // Success state
  if (step === 'success') {
    return (
      <div className="slide-panel-overlay" onClick={onClose}>
        <div className="slide-panel" onClick={e => e.stopPropagation()}>
          <div className="flex flex-col items-center justify-center h-full p-8">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Thank You!</h3>
            <p className="text-sm text-slate-500 text-center mb-6">
              Your generous gift has been received. A confirmation email will be sent shortly.
            </p>
            <Button onClick={onClose} className="btn-primary">
              Close
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (step === 'error') {
    return (
      <div className="slide-panel-overlay" onClick={onClose}>
        <div className="slide-panel" onClick={e => e.stopPropagation()}>
          <div className="flex flex-col items-center justify-center h-full p-8">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
              <AlertCircle className="w-8 h-8 text-red-600" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Something Went Wrong</h3>
            <p className="text-sm text-slate-500 text-center mb-6">
              {error || 'We encountered an error processing your donation. Please try again.'}
            </p>
            <div className="flex gap-3">
              <Button variant="outline" onClick={onClose} className="btn-secondary">
                Cancel
              </Button>
              <Button onClick={() => { setStep('amount'); setError(null); }} className="btn-primary">
                Try Again
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="slide-panel-overlay" onClick={onClose}>
      <div className="slide-panel" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="slide-panel-header">
          <div>
            <h2 className="slide-panel-title">Make a Gift</h2>
            <p className="text-xs text-slate-500 mt-0.5">Secure payment via Stripe</p>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="slide-panel-content space-y-6">
          {/* Error message */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Fund Selection */}
          <div className="form-group">
            <label className="form-label">Designation</label>
            <select 
              value={selectedFund}
              onChange={(e) => setSelectedFund(e.target.value)}
              className="form-input"
            >
              <option value="general">General Fund</option>
              {funds.map(fund => (
                <option key={fund.id} value={fund.id}>{fund.name}</option>
              ))}
            </select>
          </div>

          {/* Amount Selection */}
          <div className="form-group">
            <label className="form-label">Gift Amount</label>
            <div className="grid grid-cols-3 gap-2 mb-3">
              {DONATION_AMOUNTS.map(amt => (
                <button
                  key={amt.id}
                  onClick={() => { setSelectedAmount(amt); setCustomAmount(''); }}
                  className={`p-3 border text-center font-mono font-medium transition-colors ${
                    selectedAmount?.id === amt.id
                      ? 'bg-blue-600 border-blue-600 text-white'
                      : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300'
                  }`}
                >
                  {amt.label}
                </button>
              ))}
            </div>
            
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="number"
                value={customAmount}
                onChange={(e) => { setCustomAmount(e.target.value); setSelectedAmount(null); }}
                placeholder="Custom amount"
                className="form-input pl-9 font-mono"
                min="1"
                step="0.01"
              />
            </div>
          </div>

          {/* Recurring Option */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="recurring"
              checked={isRecurring}
              onChange={(e) => setIsRecurring(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="recurring" className="text-sm text-slate-600">
              Make this a monthly recurring gift
            </label>
          </div>

          {/* Donor Info (Optional) */}
          <div className="space-y-3 pt-4 border-t border-slate-100">
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Optional Information</p>
            <div className="grid grid-cols-2 gap-3">
              <input
                type="text"
                value={donorName}
                onChange={(e) => setDonorName(e.target.value)}
                placeholder="Name"
                className="form-input"
              />
              <input
                type="email"
                value={donorEmail}
                onChange={(e) => setDonorEmail(e.target.value)}
                placeholder="Email"
                className="form-input"
              />
            </div>
          </div>

          {/* Summary */}
          {getFinalAmount() > 0 && (
            <div className="bg-slate-50 p-4 border border-slate-200">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">
                  {isRecurring ? 'Monthly Gift' : 'One-time Gift'}
                </span>
                <span className="text-xl font-mono font-semibold text-slate-900">
                  {formatCurrency(getFinalAmount())}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="slide-panel-footer">
          <Button variant="outline" onClick={onClose} className="btn-secondary">
            Cancel
          </Button>
          <Button 
            onClick={handleProceedToCheckout}
            disabled={loading || getFinalAmount() < 1}
            className="btn-primary"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <CreditCard className="w-4 h-4 mr-2" />
                Continue to Payment
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
