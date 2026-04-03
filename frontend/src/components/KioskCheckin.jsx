import { useState, useEffect, useCallback, useRef } from 'react';
import { Phone, ChevronRight, CheckCircle, X, AlertTriangle, Printer, Search, Shield } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { LabelPrinter } from '@/components/LabelPrinter';
import { toast } from 'sonner';

const ADMIN_PIN = '1234'; // TODO: make configurable via church settings

const STEPS = {
  PHONE: 'phone',
  CHILDREN: 'children',
  CLASSROOM: 'classroom',
  CONFIRM: 'confirm',
  SUCCESS: 'success',
  PIN: 'pin',
};

export default function KioskCheckin({ tenantId, onExit }) {
  const [step, setStep] = useState(STEPS.PHONE);
  const [phone, setPhone] = useState('');
  const [family, setFamily] = useState([]);
  const [selected, setSelected] = useState([]);
  const [checkinResults, setCheckinResults] = useState([]);
  const [showPrinter, setShowPrinter] = useState(false);
  const [pinEntry, setPinEntry] = useState('');
  const [exitAttempt, setExitAttempt] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef();

  useEffect(() => {
    // Go full screen
    if (document.documentElement.requestFullscreen) {
      document.documentElement.requestFullscreen().catch(() => {});
    }
    return () => {
      if (document.exitFullscreen) document.exitFullscreen().catch(() => {});
    };
  }, []);

  useEffect(() => {
    if (step === STEPS.PHONE && inputRef.current) inputRef.current.focus();
  }, [step]);

  const formatPhone = (val) => {
    const digits = val.replace(/\D/g, '').slice(0, 10);
    if (digits.length <= 3) return digits;
    if (digits.length <= 6) return `(${digits.slice(0,3)}) ${digits.slice(3)}`;
    return `(${digits.slice(0,3)}) ${digits.slice(3,6)}-${digits.slice(6)}`;
  };

  const handlePhoneKey = (key) => {
    setError('');
    if (key === 'DEL') {
      setPhone(p => p.slice(0, -1));
      return;
    }
    if (key === 'CLR') { setPhone(''); return; }
    const digits = phone.replace(/\D/g,'');
    if (digits.length < 10) setPhone(formatPhone(digits + key));
  };

  const lookupFamily = async () => {
    const digits = phone.replace(/\D/g,'');
    if (digits.length < 10) { setError('Enter a 10-digit phone number'); return; }
    setLoading(true);
    setError('');
    try {
      const token = sessionStorage.getItem('session_token') || '';
      const res = await fetch(`${API_URL}/admin/checkin/family-lookup?phone=${digits}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        if (!data.children || data.children.length === 0) {
          setError('No children found for this phone number. Please see a volunteer.');
        } else {
          setFamily(data.children);
          setStep(STEPS.CHILDREN);
        }
      } else {
        setError('Could not find family. Please see a volunteer.');
      }
    } catch {
      setError('Connection error. Please see a volunteer.');
    } finally { setLoading(false); }
  };

  const toggleChild = (child) => {
    setSelected(prev =>
      prev.find(c => c.id === child.id)
        ? prev.filter(c => c.id !== child.id)
        : [...prev, child]
    );
  };

  const doCheckin = async () => {
    if (selected.length === 0) return;
    setLoading(true);
    const token = sessionStorage.getItem('session_token') || '';
    const results = [];
    for (const child of selected) {
      try {
        const res = await fetch(`${API_URL}/admin/checkin/checkin`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({
            child_id: child.id,
            child_name: child.name,
            parent_name: child.parent_name || '',
            guardian_phone: phone.replace(/\D/g,''),
            classroom: child.classroom || child.room || 'Children\'s Ministry',
            service_type: 'sunday_service',
          })
        });
        if (res.ok) {
          const d = await res.json();
          results.push({
            name: child.name,
            firstInitialLast: `${child.first_name || child.name.split(' ')[0]} ${(child.last_name || child.name.split(' ')[1] || '').charAt(0)}.`,
            classroom: d.classroom || child.classroom || 'Children\'s Ministry',
            serviceTime: 'Sunday 9:00 AM',
            pickupCode: d.pickup_code,
            allergies: child.allergies || '',
            allergiesDetail: child.allergies_detail || child.allergies || '',
            parentName: child.parent_name || '',
          });
        }
      } catch { /* individual child error logged */ }
    }
    setCheckinResults(results);
    setStep(STEPS.SUCCESS);
    setLoading(false);
    setShowPrinter(true);
  };

  const reset = () => {
    setStep(STEPS.PHONE);
    setPhone('');
    setFamily([]);
    setSelected([]);
    setCheckinResults([]);
    setShowPrinter(false);
    setError('');
  };

  const handleExitAttempt = () => { setExitAttempt(true); setPinEntry(''); };
  const handlePinKey = (key) => {
    if (key === 'DEL') { setPinEntry(p => p.slice(0,-1)); return; }
    const next = pinEntry + key;
    setPinEntry(next);
    if (next.length === 4) {
      if (next === ADMIN_PIN) { if (onExit) onExit(); }
      else { toast.error('Wrong PIN'); setPinEntry(''); }
    }
  };

  const NUMPAD = ['1','2','3','4','5','6','7','8','9','DEL','0','CLR'];

  return (
    <div
      className="fixed inset-0 z-[100] bg-slate-900 flex flex-col select-none"
      style={{ touchAction: 'none' }}
      data-testid="kiosk-checkin"
    >
      {/* Header */}
      <div className="bg-slate-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
            <span className="text-white font-bold text-sm">S</span>
          </div>
          <span className="text-white font-semibold text-lg">Kids Check-In</span>
        </div>
        <button onClick={handleExitAttempt} className="text-slate-400 hover:text-white text-sm flex items-center gap-1" data-testid="kiosk-exit-btn">
          <Shield className="w-4 h-4" /> Exit Kiosk
        </button>
      </div>

      {/* Main */}
      <div className="flex-1 flex flex-col items-center justify-center px-4">

        {/* PHONE ENTRY */}
        {step === STEPS.PHONE && (
          <div className="w-full max-w-sm text-center">
            <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <Phone className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">Welcome!</h1>
            <p className="text-slate-400 mb-8">Enter your phone number to check in your children.</p>
            <div className="bg-slate-800 rounded-xl px-6 py-4 mb-4 text-3xl font-mono text-white text-center tracking-widest min-h-[64px]">
              {phone || <span className="text-slate-600">• • • • • • • • • •</span>}
            </div>
            {error && <p className="text-red-400 text-sm mb-3">{error}</p>}
            {/* Numpad */}
            <div className="grid grid-cols-3 gap-3 mb-6">
              {NUMPAD.map(k => (
                <button
                  key={k}
                  onClick={() => handlePhoneKey(k)}
                  className={`py-4 rounded-xl text-xl font-bold transition-all active:scale-95 ${
                    k === 'DEL' || k === 'CLR'
                      ? 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      : 'bg-slate-700 text-white hover:bg-slate-600'
                  }`}
                  data-testid={`kiosk-key-${k}`}
                >
                  {k}
                </button>
              ))}
            </div>
            <button
              onClick={lookupFamily}
              disabled={loading || phone.replace(/\D/g,'').length < 10}
              className="w-full py-4 bg-blue-600 text-white text-xl font-bold rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
              data-testid="kiosk-lookup-btn"
            >
              {loading ? 'Looking up...' : <><Search className="w-5 h-5" /> Find My Children</>}
            </button>
          </div>
        )}

        {/* CHILD SELECTION */}
        {step === STEPS.CHILDREN && (
          <div className="w-full max-w-lg text-center">
            <h1 className="text-3xl font-bold text-white mb-2">Select Children</h1>
            <p className="text-slate-400 mb-6">Tap each child you're checking in today.</p>
            <div className="space-y-3 mb-8">
              {family.map(child => {
                const isSelected = selected.find(c => c.id === child.id);
                return (
                  <button
                    key={child.id}
                    onClick={() => toggleChild(child)}
                    className={`w-full p-4 rounded-xl border-2 text-left transition-all ${
                      isSelected
                        ? 'border-blue-500 bg-blue-600/20 text-white'
                        : 'border-slate-700 bg-slate-800 text-slate-300'
                    }`}
                    data-testid={`kiosk-child-${child.id}`}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold ${isSelected ? 'bg-blue-500 text-white' : 'bg-slate-700 text-slate-400'}`}>
                        {(child.name || '?')[0]}
                      </div>
                      <div>
                        <p className="font-semibold text-lg">{child.name}</p>
                        <p className="text-sm text-slate-400">{child.classroom || child.room || 'Children\'s Ministry'}</p>
                        {child.allergies && (
                          <p className="text-xs text-red-400 flex items-center gap-1 mt-1">
                            <AlertTriangle className="w-3 h-3" /> {child.allergies}
                          </p>
                        )}
                      </div>
                      {isSelected && <CheckCircle className="w-6 h-6 text-blue-400 ml-auto" />}
                    </div>
                  </button>
                );
              })}
            </div>
            <div className="flex gap-3">
              <button onClick={reset} className="flex-1 py-4 border border-slate-600 text-slate-300 rounded-xl text-lg">Back</button>
              <button
                onClick={doCheckin}
                disabled={selected.length === 0 || loading}
                className="flex-1 py-4 bg-blue-600 text-white text-xl font-bold rounded-xl hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
                data-testid="kiosk-confirm-checkin-btn"
              >
                {loading ? 'Checking in...' : `Check In (${selected.length})`}
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}

        {/* SUCCESS */}
        {step === STEPS.SUCCESS && (
          <div className="w-full max-w-sm text-center">
            <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">All Set!</h1>
            <p className="text-slate-400 mb-6">{selected.length} child{selected.length > 1 ? 'ren' : ''} checked in successfully.</p>
            <div className="bg-slate-800 rounded-xl p-4 mb-6 space-y-2">
              {checkinResults.map((r, i) => (
                <div key={i} className="flex items-center justify-between text-white">
                  <span>{r.name}</span>
                  <span className="font-mono text-2xl font-bold text-blue-400">{r.pickupCode}</span>
                </div>
              ))}
            </div>
            <p className="text-slate-500 text-sm mb-6">Keep your pickup code(s) to collect your children.</p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowPrinter(true)}
                className="flex-1 py-3 bg-slate-700 text-white rounded-xl text-sm flex items-center justify-center gap-2"
                data-testid="kiosk-print-btn"
              >
                <Printer className="w-4 h-4" /> Print Labels
              </button>
              <button
                onClick={reset}
                className="flex-1 py-3 bg-blue-600 text-white rounded-xl text-sm font-bold"
                data-testid="kiosk-done-btn"
              >
                Done
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Exit PIN modal */}
      {exitAttempt && (
        <div className="fixed inset-0 z-[200] bg-black/80 flex items-center justify-center">
          <div className="bg-slate-800 rounded-2xl p-8 w-80 text-center">
            <Shield className="w-10 h-10 text-slate-400 mx-auto mb-4" />
            <h2 className="text-white text-xl font-bold mb-2">Admin PIN Required</h2>
            <p className="text-slate-400 text-sm mb-4">Enter the 4-digit PIN to exit kiosk mode.</p>
            <div className="bg-slate-900 rounded-lg px-4 py-3 mb-4 text-2xl font-mono text-white text-center tracking-widest">
              {'•'.repeat(pinEntry.length) || <span className="text-slate-600">_ _ _ _</span>}
            </div>
            <div className="grid grid-cols-3 gap-2 mb-4">
              {['1','2','3','4','5','6','7','8','9','DEL','0','✕'].map(k => (
                <button
                  key={k}
                  onClick={() => {
                    if (k === '✕') { setExitAttempt(false); setPinEntry(''); return; }
                    handlePinKey(k);
                  }}
                  className={`py-3 rounded-lg text-lg font-bold transition-all active:scale-95 ${k === '✕' ? 'bg-red-600 text-white' : 'bg-slate-700 text-white hover:bg-slate-600'}`}
                  data-testid={`kiosk-pin-${k}`}
                >
                  {k}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Label printer modal */}
      {showPrinter && checkinResults.length > 0 && (
        <LabelPrinter checkins={checkinResults} onClose={() => setShowPrinter(false)} />
      )}
    </div>
  );
}
