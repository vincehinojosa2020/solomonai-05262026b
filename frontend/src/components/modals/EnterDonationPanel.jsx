import { useState, useEffect } from 'react';
import { X, Search, CreditCard, Banknote, FileText, Building2, Bitcoin, TrendingUp, Home, Car } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { toast } from 'sonner';
import { API_URL, formatCurrency, getInitials, debounce } from '@/lib/utils';

const PAYMENT_METHODS = [
  { id: 'card', label: 'Card', icon: CreditCard },
  { id: 'check', label: 'Check', icon: FileText },
  { id: 'cash', label: 'Cash', icon: Banknote },
  { id: 'ach', label: 'ACH', icon: Building2 },
];

const ASSET_METHODS = [
  { id: 'crypto', label: 'Crypto', icon: Bitcoin },
  { id: 'stock', label: 'Stock', icon: TrendingUp },
  { id: 'real_estate', label: 'Real Estate', icon: Home },
  { id: 'vehicle', label: 'Vehicle', icon: Car },
];

export default function EnterDonationPanel({ onClose, onSuccess, funds, batches }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  const [formData, setFormData] = useState({
    person_id: null,
    person_name: '',
    fund_id: funds[0]?.id || '',
    amount: '',
    donation_date: new Date().toISOString().split('T')[0],
    payment_method: 'card',
    check_number: '',
    crypto_currency: '',
    crypto_amount: '',
    asset_type: '',
    asset_description: '',
    notes: '',
    batch_id: '',
  });

  const handleChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  // Search for donors
  useEffect(() => {
    if (searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }

    const search = async () => {
      setSearching(true);
      try {
        const response = await fetch(`${API_URL}/search?q=${encodeURIComponent(searchQuery)}&limit=5`);
        const data = await response.json();
        setSearchResults(data.filter(r => r.type === 'person'));
      } catch (error) {
        console.error('Search failed:', error);
      } finally {
        setSearching(false);
      }
    };

    const timer = setTimeout(search, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const selectDonor = (person) => {
    setFormData({
      ...formData,
      person_id: person.id,
      person_name: person.title,
    });
    setSearchQuery('');
    setSearchResults([]);
    setStep(2);
  };

  const handleAnonymous = () => {
    setFormData({
      ...formData,
      person_id: null,
      person_name: 'Anonymous',
    });
    setStep(2);
  };

  const handleSubmit = async () => {
    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        person_id: formData.person_id,
        fund_id: formData.fund_id,
        amount: parseFloat(formData.amount),
        donation_date: formData.donation_date,
        payment_method: formData.payment_method,
        check_number: formData.check_number || null,
        crypto_currency: formData.crypto_currency || null,
        crypto_amount: formData.crypto_amount ? parseFloat(formData.crypto_amount) : null,
        asset_type: formData.asset_type || null,
        asset_description: formData.asset_description || null,
        notes: formData.notes || null,
        batch_id: formData.batch_id || null,
      };

      const response = await fetch(`${API_URL}/donations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error('Failed to record donation');
      }

      toast.success('Donation recorded', {
        description: `${formatCurrency(payload.amount)} from ${formData.person_name}`,
      });
      onSuccess();
    } catch (error) {
      console.error('Failed to record donation:', error);
      toast.error('Failed to record donation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="slide-panel-overlay" onClick={onClose} data-testid="donation-panel-overlay">
      <div className="slide-panel" onClick={(e) => e.stopPropagation()} data-testid="donation-panel">
        <div className="slide-panel-header">
          <h2 className="slide-panel-title">Enter Donation</h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-slate-100 transition-colors"
            data-testid="close-panel-btn"
          >
            <X className="w-5 h-5 text-slate-400" />
          </button>
        </div>

        {/* Step Indicator */}
        <div className="px-6 py-4 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step >= 1 ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-500'
            }`}>1</div>
            <div className={`flex-1 h-0.5 ${step >= 2 ? 'bg-blue-600' : 'bg-slate-200'}`}></div>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step >= 2 ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-500'
            }`}>2</div>
            <div className={`flex-1 h-0.5 ${step >= 3 ? 'bg-blue-600' : 'bg-slate-200'}`}></div>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step >= 3 ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-500'
            }`}>3</div>
          </div>
          <div className="flex justify-between mt-2 text-xs text-slate-500">
            <span>Donor</span>
            <span>Amount</span>
            <span>Confirm</span>
          </div>
        </div>

        <div className="slide-panel-content">
          {/* Step 1: Select Donor */}
          {step === 1 && (
            <div className="space-y-4">
              <div>
                <Label className="form-label">Search for Donor</Label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    placeholder="Type name, email, or phone..."
                    className="pl-9"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    data-testid="donor-search-input"
                  />
                </div>
              </div>

              {/* Search Results */}
              {searching && (
                <div className="text-center py-4 text-slate-400 text-sm">Searching...</div>
              )}

              {searchResults.length > 0 && (
                <div className="border border-slate-200 rounded-lg overflow-hidden">
                  {searchResults.map((person) => (
                    <button
                      key={person.id}
                      className="w-full flex items-center gap-3 p-3 hover:bg-slate-50 text-left border-b border-slate-100 last:border-0"
                      onClick={() => selectDonor(person)}
                      data-testid={`donor-result-${person.id}`}
                    >
                      <Avatar className="w-10 h-10">
                        <AvatarImage src={person.photo_url} />
                        <AvatarFallback>{person.title?.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium text-slate-900">{person.title}</p>
                        <p className="text-sm text-slate-500">{person.subtitle}</p>
                      </div>
                    </button>
                  ))}
                </div>
              )}

              <button
                className="w-full p-4 border border-dashed border-slate-300 rounded-lg text-slate-500 hover:border-slate-400 hover:text-slate-700 transition-colors"
                onClick={handleAnonymous}
                data-testid="anonymous-btn"
              >
                Record as Anonymous / Walk-in
              </button>
            </div>
          )}

          {/* Step 2: Enter Amount */}
          {step === 2 && (
            <div className="space-y-5">
              {/* Selected Donor */}
              <div className="p-3 bg-slate-50 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Avatar className="w-10 h-10">
                    <AvatarFallback>{formData.person_name?.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="font-medium text-slate-900">{formData.person_name}</p>
                    <p className="text-xs text-slate-500">Donor</p>
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={() => setStep(1)}>Change</Button>
              </div>

              {/* Fund Selection */}
              <div className="form-group">
                <Label className="form-label">Fund</Label>
                <Select value={formData.fund_id} onValueChange={(v) => handleChange('fund_id', v)}>
                  <SelectTrigger data-testid="fund-select">
                    <SelectValue placeholder="Select fund" />
                  </SelectTrigger>
                  <SelectContent>
                    {funds.map((fund) => (
                      <SelectItem key={fund.id} value={fund.id}>{fund.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Amount */}
              <div className="form-group">
                <Label className="form-label">Amount</Label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-2xl text-slate-400">$</span>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    className="amount-input pl-10"
                    value={formData.amount}
                    onChange={(e) => handleChange('amount', e.target.value)}
                    data-testid="amount-input"
                  />
                </div>
              </div>

              {/* Date */}
              <div className="form-group">
                <Label className="form-label">Date</Label>
                <Input
                  type="date"
                  value={formData.donation_date}
                  onChange={(e) => handleChange('donation_date', e.target.value)}
                  data-testid="date-input"
                />
              </div>

              {/* Payment Method */}
              <div className="form-group">
                <Label className="form-label">Payment Method</Label>
                <div className="payment-methods-grid">
                  {PAYMENT_METHODS.map((method) => (
                    <button
                      key={method.id}
                      type="button"
                      className={`payment-method-btn ${formData.payment_method === method.id ? 'active' : ''}`}
                      onClick={() => handleChange('payment_method', method.id)}
                      data-testid={`payment-${method.id}`}
                    >
                      <method.icon className="icon" />
                      <span className="label">{method.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Check Number (if check selected) */}
              {formData.payment_method === 'check' && (
                <div className="form-group">
                  <Label className="form-label">Check Number</Label>
                  <Input
                    placeholder="Enter check number"
                    value={formData.check_number}
                    onChange={(e) => handleChange('check_number', e.target.value)}
                    data-testid="check-number-input"
                  />
                </div>
              )}

              {/* Asset Methods (Collapsible) */}
              <details className="border border-slate-200 rounded-lg">
                <summary className="px-4 py-3 cursor-pointer text-sm text-slate-600 hover:text-slate-900">
                  Non-cash gifts (Crypto, Stock, Real Estate, Vehicle)
                </summary>
                <div className="px-4 pb-4 pt-2 border-t border-slate-100">
                  <div className="payment-methods-grid">
                    {ASSET_METHODS.map((method) => (
                      <button
                        key={method.id}
                        type="button"
                        className={`payment-method-btn ${formData.payment_method === method.id ? 'active' : ''}`}
                        onClick={() => handleChange('payment_method', method.id)}
                        data-testid={`payment-${method.id}`}
                      >
                        <method.icon className="icon" />
                        <span className="label">{method.label}</span>
                      </button>
                    ))}
                  </div>

                  {formData.payment_method === 'crypto' && (
                    <div className="mt-4 space-y-3">
                      <div className="form-group">
                        <Label className="form-label">Cryptocurrency</Label>
                        <Select value={formData.crypto_currency} onValueChange={(v) => handleChange('crypto_currency', v)}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select currency" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="BTC">Bitcoin (BTC)</SelectItem>
                            <SelectItem value="ETH">Ethereum (ETH)</SelectItem>
                            <SelectItem value="USDC">USD Coin (USDC)</SelectItem>
                            <SelectItem value="SOL">Solana (SOL)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="form-group">
                        <Label className="form-label">Crypto Amount</Label>
                        <Input
                          type="number"
                          step="0.00000001"
                          placeholder="0.0"
                          value={formData.crypto_amount}
                          onChange={(e) => handleChange('crypto_amount', e.target.value)}
                        />
                      </div>
                    </div>
                  )}

                  {['stock', 'real_estate', 'vehicle'].includes(formData.payment_method) && (
                    <div className="mt-4 form-group">
                      <Label className="form-label">Asset Description</Label>
                      <Textarea
                        placeholder="Describe the asset..."
                        value={formData.asset_description}
                        onChange={(e) => handleChange('asset_description', e.target.value)}
                      />
                    </div>
                  )}
                </div>
              </details>

              {/* Batch */}
              {batches.length > 0 && (
                <div className="form-group">
                  <Label className="form-label">Add to Batch (Optional)</Label>
                  <Select value={formData.batch_id} onValueChange={(v) => handleChange('batch_id', v)}>
                    <SelectTrigger>
                      <SelectValue placeholder="No batch" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">No batch</SelectItem>
                      {batches.map((batch) => (
                        <SelectItem key={batch.id} value={batch.id}>{batch.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* Notes */}
              <div className="form-group">
                <Label className="form-label">Notes (Optional)</Label>
                <Textarea
                  placeholder="Add any notes..."
                  value={formData.notes}
                  onChange={(e) => handleChange('notes', e.target.value)}
                  data-testid="notes-input"
                />
              </div>
            </div>
          )}

          {/* Step 3: Confirm */}
          {step === 3 && (
            <div className="space-y-6">
              <div className="text-center py-6">
                <div className="success-check mx-auto mb-4">
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-1">Confirm Donation</h3>
                <p className="text-slate-500">Review the details below</p>
              </div>

              <div className="bg-slate-50 rounded-lg p-4 space-y-3">
                <div className="flex justify-between">
                  <span className="text-slate-500">Donor</span>
                  <span className="font-medium text-slate-900">{formData.person_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Fund</span>
                  <span className="font-medium text-slate-900">
                    {funds.find(f => f.id === formData.fund_id)?.name}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Amount</span>
                  <span className="font-bold text-2xl text-slate-900 font-data">
                    {formatCurrency(parseFloat(formData.amount) || 0)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Date</span>
                  <span className="font-medium text-slate-900">{formData.donation_date}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Method</span>
                  <span className="font-medium text-slate-900 capitalize">{formData.payment_method}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="slide-panel-footer">
          {step === 1 && (
            <Button variant="outline" onClick={onClose}>Cancel</Button>
          )}
          {step === 2 && (
            <>
              <Button variant="outline" onClick={() => setStep(1)}>Back</Button>
              <Button 
                className="btn-primary" 
                onClick={() => setStep(3)}
                disabled={!formData.amount || parseFloat(formData.amount) <= 0}
                data-testid="continue-btn"
              >
                Continue
              </Button>
            </>
          )}
          {step === 3 && (
            <>
              <Button variant="outline" onClick={() => setStep(2)}>Back</Button>
              <Button 
                className="btn-primary" 
                onClick={handleSubmit}
                disabled={loading}
                data-testid="save-donation-btn"
              >
                {loading ? 'Saving...' : 'Save Donation'}
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
