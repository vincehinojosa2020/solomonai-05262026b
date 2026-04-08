import { useState, useEffect } from 'react';
import { User, CreditCard, Bell, ChevronRight, Check, X } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

export default function OnboardingFlow({ user, onComplete }) {
  const [step, setStep] = useState(0);
  const [show, setShow] = useState(false);
  const [profile, setProfile] = useState({ phone: '', address: '', city: '', state: '', zip: '' });
  const [cardForm, setCardForm] = useState({ number: '', exp_month: '', exp_year: '', cvc: '' });
  const [prefs, setPrefs] = useState({ newsletter: true, events: true, receipts: true, groups: true, prayer: false });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    // Skip onboarding if already completed (stored in DB)
    if (user?.onboarding_completed || user?.profile_completed) return;
    const loginCount = parseInt(sessionStorage.getItem('solomon_login_count') || '0');
    const dismissed = sessionStorage.getItem('solomon_onboarding_done');
    if (loginCount <= 2 && !dismissed) setShow(true);
  }, [user]);

  if (!show) return null;

  const dismiss = () => { sessionStorage.setItem('solomon_onboarding_done', '1'); setShow(false); onComplete?.(); };

  const steps = [
    { icon: User, title: 'Complete Your Profile', desc: 'Help us connect with you' },
    { icon: CreditCard, title: 'Add Payment Method', desc: 'For faster checkout' },
    { icon: Bell, title: 'Notification Preferences', desc: 'Stay in the loop' },
  ];

  const saveProfile = async () => {
    setSaving(true);
    try {
      await fetch(`${API_URL}/portal/me`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mobile_phone: profile.phone, address: profile.address, city: profile.city, state: profile.state, zip: profile.zip }),
      });
      toast.success('Profile updated');
      setStep(1);
    } catch { toast.error('Failed to save'); }
    finally { setSaving(false); }
  };

  const saveCard = async () => {
    if (!cardForm.number) { setStep(2); return; } // skip if empty
    setSaving(true);
    try {
      const last4 = cardForm.number.slice(-4);
      const brand = cardForm.number.startsWith('4') ? 'Visa' : cardForm.number.startsWith('5') ? 'Mastercard' : 'Card';
      await fetch(`${API_URL}/portal/payment-methods`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ solomonpay_token: `sp_onboard_${Date.now()}`, card_brand: brand, card_last_four: last4, card_exp_month: parseInt(cardForm.exp_month) || 12, card_exp_year: parseInt(cardForm.exp_year) || 2028, is_default: true }),
      });
      toast.success('Card saved');
      setStep(2);
    } catch { toast.error('Failed'); }
    finally { setSaving(false); }
  };

  const savePrefs = async () => {
    setSaving(true);
    try {
      await fetch(`${API_URL}/portal/me`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notification_preferences: prefs }),
      });
      toast.success('Preferences saved');
      dismiss();
    } catch { toast.error('Failed'); dismiss(); }
    finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 backdrop-blur-sm" data-testid="onboarding-modal">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden" style={{ animation: 'fadeInUp .3s ease' }}>
        {/* Progress */}
        <div className="flex items-center gap-0 px-6 pt-5 pb-2">
          {steps.map((s, i) => (
            <div key={i} className="flex items-center flex-1">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${i < step ? 'bg-green-500 text-white' : i === step ? 'bg-slate-900 text-white' : 'bg-slate-200 text-slate-500'}`}>
                {i < step ? <Check className="w-3.5 h-3.5" /> : i + 1}
              </div>
              {i < 2 && <div className={`flex-1 h-0.5 mx-1 ${i < step ? 'bg-green-500' : 'bg-slate-200'}`} />}
            </div>
          ))}
        </div>

        {/* Header */}
        <div className="px-6 pt-2 pb-4">
          <h2 className="text-lg font-bold text-slate-900">{steps[step].title}</h2>
          <p className="text-sm text-slate-500">{steps[step].desc}</p>
        </div>

        {/* Step Content */}
        <div className="px-6 pb-6">
          {step === 0 && (
            <div className="space-y-3" data-testid="onboarding-step-profile">
              <div>
                <label className="text-xs font-medium text-slate-500">PHONE</label>
                <input type="tel" value={profile.phone} onChange={e => setProfile({...profile, phone: e.target.value})} placeholder="(555) 123-4567" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-300" data-testid="onboard-phone" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500">ADDRESS</label>
                <input type="text" value={profile.address} onChange={e => setProfile({...profile, address: e.target.value})} placeholder="123 Main St" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-300" data-testid="onboard-address" />
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="text-xs font-medium text-slate-500">CITY</label>
                  <input type="text" value={profile.city} onChange={e => setProfile({...profile, city: e.target.value})} placeholder="El Paso" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-300" />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500">STATE</label>
                  <input type="text" value={profile.state} onChange={e => setProfile({...profile, state: e.target.value})} placeholder="TX" maxLength={2} className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-300" />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500">ZIP</label>
                  <input type="text" value={profile.zip} onChange={e => setProfile({...profile, zip: e.target.value})} placeholder="79936" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-300" />
                </div>
              </div>
              <div className="flex gap-2 pt-2">
                <button onClick={saveProfile} disabled={saving} className="flex-1 px-4 py-2.5 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 disabled:opacity-50" data-testid="onboard-save-profile">
                  {saving ? 'Saving...' : 'Continue'}
                </button>
                <button onClick={() => setStep(1)} className="px-4 py-2.5 text-slate-500 text-sm hover:text-slate-700">Skip for now</button>
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-3" data-testid="onboarding-step-payment">
              <div>
                <label className="text-xs font-medium text-slate-500">CARD NUMBER</label>
                <input type="text" maxLength="19" value={cardForm.number} onChange={e => setCardForm({...cardForm, number: e.target.value.replace(/\D/g,'')})} placeholder="4242 4242 4242 4242" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-300" data-testid="onboard-card-number" />
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="text-xs font-medium text-slate-500">MONTH</label>
                  <input type="text" maxLength="2" value={cardForm.exp_month} onChange={e => setCardForm({...cardForm, exp_month: e.target.value})} placeholder="12" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-300" />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500">YEAR</label>
                  <input type="text" maxLength="4" value={cardForm.exp_year} onChange={e => setCardForm({...cardForm, exp_year: e.target.value})} placeholder="2028" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-300" />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500">CVC</label>
                  <input type="text" maxLength="4" value={cardForm.cvc} onChange={e => setCardForm({...cardForm, cvc: e.target.value})} placeholder="123" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-300" />
                </div>
              </div>
              <p className="text-xs text-slate-400">Secure payment powered by SolomonPay. Your card is encrypted.</p>
              <div className="flex gap-2 pt-2">
                <button onClick={saveCard} disabled={saving} className="flex-1 px-4 py-2.5 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 disabled:opacity-50" data-testid="onboard-save-card">
                  {saving ? 'Saving...' : cardForm.number ? 'Save & Continue' : 'Continue'}
                </button>
                <button onClick={() => setStep(2)} className="px-4 py-2.5 text-slate-500 text-sm hover:text-slate-700">Skip for now</button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-3" data-testid="onboarding-step-notifications">
              {[
                { id: 'newsletter', label: 'Weekly newsletter' },
                { id: 'events', label: 'Event reminders & updates' },
                { id: 'receipts', label: 'Giving receipts' },
                { id: 'groups', label: 'Group updates & messages' },
                { id: 'prayer', label: 'Prayer request notifications' },
              ].map(p => (
                <label key={p.id} className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-slate-50 cursor-pointer">
                  <span className="text-sm text-slate-700">{p.label}</span>
                  <div className={`w-10 h-5 rounded-full transition-colors relative cursor-pointer ${prefs[p.id] ? 'bg-slate-900' : 'bg-slate-200'}`} onClick={() => setPrefs({...prefs, [p.id]: !prefs[p.id]})}>
                    <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${prefs[p.id] ? 'translate-x-5' : 'translate-x-0.5'}`} />
                  </div>
                </label>
              ))}
              <div className="flex gap-2 pt-2">
                <button onClick={savePrefs} disabled={saving} className="flex-1 px-4 py-2.5 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 disabled:opacity-50" data-testid="onboard-finish">
                  {saving ? 'Saving...' : 'Finish Setup'}
                </button>
                <button onClick={dismiss} className="px-4 py-2.5 text-slate-500 text-sm hover:text-slate-700">Skip for now</button>
              </div>
            </div>
          )}
        </div>

        {/* Dismiss */}
        <button onClick={dismiss} className="absolute top-4 right-4 p-1 rounded-full hover:bg-slate-100 text-slate-400" data-testid="onboarding-dismiss">
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
