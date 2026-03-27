import { useState, useEffect } from 'react';
import { X, DollarSign, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { API_URL } from '@/lib/utils';
import SolomonPayForm from '@/components/SolomonPayForm';

const DONATION_AMOUNTS = [
  { id: 'tithe_25', amount: 25, label: '$25' },
  { id: 'tithe_50', amount: 50, label: '$50' },
  { id: 'tithe_100', amount: 100, label: '$100' },
  { id: 'tithe_250', amount: 250, label: '$250' },
  { id: 'tithe_500', amount: 500, label: '$500' },
  { id: 'tithe_1000', amount: 1000, label: '$1,000' },
];

export default function DonationCheckout({ onClose, preselectedFund }) {
  const [step, setStep] = useState('amount');
  const [selectedAmount, setSelectedAmount] = useState(null);
  const [customAmount, setCustomAmount] = useState('');
  const [selectedFund, setSelectedFund] = useState(preselectedFund || 'general');
  const [isRecurring, setIsRecurring] = useState(false);
  const [error, setError] = useState(null);
  const [funds, setFunds] = useState([]);
  const [transactionId, setTransactionId] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/funds`)
      .then(res => res.json())
      .then(data => setFunds(data))
      .catch(() => {});
  }, []);

  const getFinalAmount = () => {
    if (selectedAmount) return selectedAmount.amount;
    return parseFloat(customAmount) || 0;
  };

  const handleProceedToPayment = () => {
    const amount = getFinalAmount();
    if (amount < 1) {
      setError('Please enter an amount of at least $1.00');
      return;
    }
    setError(null);
    setStep('payment');
  };

  const handleSolomonPaySuccess = async (cardData) => {
    const amount = getFinalAmount();
    const fundObj = funds.find(f => f.id === selectedFund);
    const response = await fetch(`${API_URL}/solomonpay/process`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...cardData,
        amount,
        context: 'donation',
        fund_id: selectedFund,
        fund_name: fundObj?.name || 'General Fund',
        frequency: isRecurring ? 'monthly' : 'one-time',
        description: `${isRecurring ? 'Monthly' : 'One-time'} gift to ${fundObj?.name || 'General Fund'}`,
      }),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Payment failed');
    }
    const data = await response.json();
    setTransactionId(data.transaction_id);
    setStep('success');
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(value);
  };

  if (step === 'success') {
    return (
      <div className="slide-panel-overlay" onClick={onClose}>
        <div className="slide-panel" onClick={e => e.stopPropagation()}>
          <div className="flex flex-col items-center justify-center h-full p-8">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Thank You for Your Generosity!</h3>
            <p className="text-sm text-slate-500 text-center mb-2">
              Your {formatCurrency(getFinalAmount())} gift has been recorded.
            </p>
            <p className="text-xs text-slate-400 text-center mb-6">
              Transaction will be processed when SolomonPay goes live.
            </p>
            {transactionId && (
              <p className="text-xs text-slate-400 font-mono mb-4">Ref: {transactionId}</p>
            )}
            <Button onClick={onClose} className="btn-primary" data-testid="donation-success-close">
              Close
            </Button>
          </div>
        </div>
      </div>
    );
  }

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
              {error || 'We encountered an error. Please try again.'}
            </p>
            <div className="flex gap-3">
              <Button variant="outline" onClick={onClose} className="btn-secondary">Cancel</Button>
              <Button onClick={() => { setStep('amount'); setError(null); }} className="btn-primary">Try Again</Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (step === 'payment') {
    return (
      <div className="slide-panel-overlay" onClick={onClose}>
        <div className="slide-panel" onClick={e => e.stopPropagation()}>
          <div className="slide-panel-header">
            <div>
              <h2 className="slide-panel-title">Complete Your Gift</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                {isRecurring ? 'Monthly' : 'One-time'} gift of {formatCurrency(getFinalAmount())}
              </p>
            </div>
            <button onClick={() => setStep('amount')} className="p-1.5 text-slate-400 hover:text-slate-600">
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="slide-panel-content" style={{ paddingTop: 24 }}>
            <SolomonPayForm
              amount={getFinalAmount()}
              onSuccess={handleSolomonPaySuccess}
              onCancel={() => setStep('amount')}
              context="donation"
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="slide-panel-overlay" onClick={onClose}>
      <div className="slide-panel" onClick={e => e.stopPropagation()}>
        <div className="slide-panel-header">
          <div>
            <h2 className="slide-panel-title">Make a Gift</h2>
            <p className="text-xs text-slate-500 mt-0.5">Secure payment via SolomonPay</p>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-600" data-testid="donation-close">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="slide-panel-content space-y-6">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm">{error}</div>
          )}
          <div className="form-group">
            <label className="form-label">Designation</label>
            <select value={selectedFund} onChange={(e) => setSelectedFund(e.target.value)} className="form-input" data-testid="donation-fund-select">
              <option value="general">General Fund</option>
              {funds.map(fund => (
                <option key={fund.id} value={fund.id}>{fund.name}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Gift Amount</label>
            <div className="grid grid-cols-3 gap-2 mb-3">
              {DONATION_AMOUNTS.map(amt => (
                <button
                  key={amt.id}
                  onClick={() => { setSelectedAmount(amt); setCustomAmount(''); }}
                  data-testid={`donation-amount-${amt.amount}`}
                  className={`p-3 border text-center font-mono font-medium transition-colors ${
                    selectedAmount?.id === amt.id
                      ? 'bg-slate-900 border-slate-900 text-white'
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
                data-testid="donation-custom-amount"
              />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="recurring"
              checked={isRecurring}
              onChange={(e) => setIsRecurring(e.target.checked)}
              className="w-4 h-4 text-slate-900 border-slate-300 rounded focus:ring-slate-500"
              data-testid="donation-recurring"
            />
            <label htmlFor="recurring" className="text-sm text-slate-600">
              Make this a monthly recurring gift
            </label>
          </div>
          {getFinalAmount() > 0 && (
            <div className="bg-slate-50 p-4 border border-slate-200">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">{isRecurring ? 'Monthly Gift' : 'One-time Gift'}</span>
                <span className="text-xl font-mono font-semibold text-slate-900">{formatCurrency(getFinalAmount())}</span>
              </div>
            </div>
          )}
        </div>
        <div className="slide-panel-footer">
          <Button variant="outline" onClick={onClose} className="btn-secondary">Cancel</Button>
          <Button onClick={handleProceedToPayment} disabled={getFinalAmount() < 1} className="btn-primary" data-testid="donation-continue-btn">
            Continue to SolomonPay
          </Button>
        </div>
      </div>
    </div>
  );
}
