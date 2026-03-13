import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Check, X, Clock, AlertCircle, Phone, ChevronRight, ChevronLeft, Sparkles } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

const getAvatar = (seed) =>
  `https://api.dicebear.com/7.x/adventurer/svg?seed=${encodeURIComponent(seed)}&backgroundColor=transparent`;

const CHARACTERS = ['Explorer', 'Dreamer', 'Hero', 'Champion', 'Star', 'Adventurer', 'Captain', 'Buddy'];
const getCharacter = (name) => CHARACTERS[name.charCodeAt(0) % CHARACTERS.length];

const CARD_COLORS = [
  { bg: '#58CC02', border: '#46a302' },
  { bg: '#CE82FF', border: '#b35cff' },
  { bg: '#FF9600', border: '#e08500' },
  { bg: '#1CB0F6', border: '#0a9de0' },
  { bg: '#FF4B4B', border: '#e03a3a' },
  { bg: '#FFC800', border: '#e0b200' },
];
const getCardColor = (name) => CARD_COLORS[name.charCodeAt(0) % CARD_COLORS.length];

const formatAge = (birthdate) => {
  if (!birthdate) return 'Age not set';
  const today = new Date();
  const birth = new Date(birthdate);
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
  if (age <= 0) return 'Under 1 year';
  if (age === 1) return '1 year old';
  return `${age} years old`;
};

export default function PortalKidsCheckin() {
  const { user } = useOutletContext();
  const [children, setChildren] = useState([]);
  const [checkins, setCheckins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddChild, setShowAddChild] = useState(false);

  // Wizard
  const [wizardStep, setWizardStep] = useState(0);
  const [selectedChildren, setSelectedChildren] = useState([]);
  const [checkinResults, setCheckinResults] = useState([]);

  const [newChild, setNewChild] = useState({
    name: '', birthdate: '', allergies: '', special_needs: '',
    emergency_contact: '', emergency_phone: ''
  });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [childRes, checkinRes] = await Promise.all([
        fetch(`${API_URL}/portal/kids`, { credentials: 'include' }),
        fetch(`${API_URL}/portal/kids/checkins/active`, { credentials: 'include' })
      ]);
      if (childRes.ok) setChildren((await childRes.json()).children || []);
      if (checkinRes.ok) setCheckins((await checkinRes.json()).checkins || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const addChild = async () => {
    if (!newChild.name || !newChild.birthdate) { toast.error('Name and birthdate required'); return; }
    try {
      const res = await fetch(`${API_URL}/portal/kids`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        credentials: 'include', body: JSON.stringify(newChild)
      });
      if (res.ok) {
        toast.success(`${newChild.name} added!`);
        setShowAddChild(false);
        setNewChild({ name: '', birthdate: '', allergies: '', special_needs: '', emergency_contact: '', emergency_phone: '' });
        fetchData();
      } else toast.error('Failed to add child');
    } catch { toast.error('Error adding child'); }
  };

  const isCheckedIn = (childId) => checkins.some(c => c.child_id === childId && c.status === 'checked_in');
  const getCheckinInfo = (childId) => checkins.find(c => c.child_id === childId && c.status === 'checked_in');

  const toggleSelect = (child) => {
    setSelectedChildren(prev =>
      prev.find(c => c.id === child.id) ? prev.filter(c => c.id !== child.id) : [...prev, child]
    );
  };

  const handleBulkCheckin = async () => {
    const results = [];
    for (const child of selectedChildren) {
      try {
        const res = await fetch(`${API_URL}/portal/kids/${child.id}/checkin`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          credentials: 'include', body: JSON.stringify({ classroom: 'Sunday School' })
        });
        if (res.ok) {
          const data = await res.json();
          results.push({ child, pickup_code: data.pickup_code, success: true });
        } else results.push({ child, success: false });
      } catch { results.push({ child, success: false }); }
    }
    setCheckinResults(results);
    setWizardStep(3);
    fetchData();
  };

  const startWizard = () => { setSelectedChildren([]); setCheckinResults([]); setWizardStep(1); };
  const closeWizard = () => { setWizardStep(0); setSelectedChildren([]); setCheckinResults([]); };

  const uncheckedChildren = children.filter(c => !isCheckedIn(c.id));

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]" data-testid="kids-checkin-loading" style={{ fontFamily: "'Nunito', sans-serif" }}>
        <div className="flex gap-1.5 mb-4">
          {['#58CC02', '#FF9600', '#1CB0F6'].map((c, i) => (
            <span key={i} className="w-3.5 h-3.5 rounded-full animate-bounce" style={{ backgroundColor: c, animationDelay: `${i * 0.15}s` }} />
          ))}
        </div>
        <p className="text-gray-500 font-bold text-lg">Getting ready for fun...</p>
      </div>
    );
  }

  return (
    <div data-testid="kids-checkin-page" style={{ fontFamily: "'Nunito', 'Inter', sans-serif", minHeight: '80vh', background: 'linear-gradient(180deg, #eef7ff 0%, #fff8ee 100%)' }}>

      {/* Header */}
      <div style={{ background: '#58CC02', padding: '1.5rem 1.5rem 1.25rem', borderRadius: '0 0 28px 28px' }}>
        <div className="max-w-[900px] mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-white font-black text-2xl md:text-3xl tracking-tight" style={{ margin: 0, color: '#fff' }}>Kids Zone</h1>
            <p className="text-white/85 text-sm font-semibold mt-0.5">Sunday School Adventures</p>
          </div>
          <button
            data-testid="add-child-btn"
            onClick={() => setShowAddChild(true)}
            className="inline-flex items-center gap-1.5 bg-white text-gray-900 font-extrabold text-sm px-4 py-2.5 rounded-xl cursor-pointer"
            style={{ border: '3px solid rgba(0,0,0,0.08)', boxShadow: '0 3px 0 rgba(0,0,0,0.1)', fontFamily: "'Nunito', sans-serif" }}
          >
            <Plus className="w-5 h-5" /> Add Child
          </button>
        </div>
      </div>

      {/* Check-in CTA */}
      {uncheckedChildren.length > 0 && (
        <motion.button
          data-testid="start-checkin-wizard"
          onClick={startWizard}
          initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
          className="flex items-center gap-3 bg-white w-[calc(100%-2rem)] max-w-[900px] mx-auto mt-5 px-5 py-4 text-left cursor-pointer"
          style={{ border: '3px solid #58CC02', borderRadius: '18px', boxShadow: '0 4px 0 #46a302', fontFamily: "'Nunito', sans-serif" }}
        >
          <Sparkles className="w-6 h-6 text-green-500 shrink-0" />
          <div className="flex-1">
            <strong className="block text-gray-900 text-base font-extrabold">Ready for Sunday School?</strong>
            <span className="text-gray-500 text-sm font-semibold">Tap here to check in your kids</span>
          </div>
          <ChevronRight className="w-5 h-5 text-green-500" />
        </motion.button>
      )}

      {/* Children Grid */}
      <div className="grid gap-4 max-w-[900px] mx-auto mt-5 px-4" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))' }}>
        {children.length === 0 ? (
          <motion.div className="col-span-full text-center py-12 px-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ fontFamily: "'Nunito', sans-serif" }}>
            <img src={getAvatar('welcome-friend')} alt="" className="w-24 h-24 mx-auto mb-4" />
            <h3 className="text-xl font-extrabold text-gray-900 mb-2" style={{ color: '#1a1a2e' }}>No Children Yet</h3>
            <p className="text-gray-500 font-semibold mb-5">Add your children to get started with check-in</p>
            <button
              data-testid="add-first-child-btn"
              onClick={() => setShowAddChild(true)}
              className="inline-flex items-center gap-1.5 bg-white text-gray-900 font-extrabold text-sm px-5 py-2.5 rounded-xl cursor-pointer"
              style={{ border: '3px solid rgba(0,0,0,0.08)', boxShadow: '0 3px 0 rgba(0,0,0,0.1)', fontFamily: "'Nunito', sans-serif" }}
            >
              <Plus className="w-5 h-5" /> Add Your First Child
            </button>
          </motion.div>
        ) : (
          children.map((child, i) => {
            const checked = isCheckedIn(child.id);
            const info = getCheckinInfo(child.id);
            const color = getCardColor(child.name);
            return (
              <motion.div
                key={child.id}
                data-testid={`child-card-${child.id}`}
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
                className="bg-white rounded-[20px] p-5 relative overflow-hidden transition-all hover:-translate-y-0.5"
                style={{
                  border: `3px solid ${checked ? color.bg : '#e5e7eb'}`,
                  boxShadow: '0 2px 0 rgba(0,0,0,0.05)',
                  background: checked ? `linear-gradient(to bottom, ${color.bg}08, #fff)` : '#fff',
                }}
              >
                <div className="w-[72px] h-[72px] mx-auto mb-3 rounded-full overflow-hidden p-1" style={{ background: color.bg }}>
                  <img src={getAvatar(child.name)} alt={child.name} className="w-full h-full rounded-full bg-white" />
                </div>
                <div className="text-center">
                  <h3 className="font-extrabold text-lg mb-0.5" style={{ color: '#1a1a2e' }}>{child.name}</h3>
                  <span className="block text-xs font-semibold text-gray-400">{formatAge(child.birthdate)}</span>
                  <span className="inline-block text-xs font-bold text-white px-2.5 py-0.5 rounded-full mt-1.5" style={{ background: color.bg }}>{getCharacter(child.name)}</span>
                  {child.allergies && (
                    <div className="flex items-center gap-1 justify-center text-xs font-bold text-red-500 mt-1.5">
                      <AlertCircle className="w-3 h-3" /> {child.allergies}
                    </div>
                  )}
                </div>
                {checked ? (
                  <div className="mt-3 text-center">
                    <div className="inline-flex items-center gap-1 text-white text-xs font-extrabold px-3.5 py-1 rounded-full" style={{ background: '#58CC02' }}>
                      <Check className="w-4 h-4" /> Checked In
                    </div>
                    <div className="mt-2 rounded-xl p-2" style={{ background: '#1a1a2e' }}>
                      <span className="block text-[10px] uppercase tracking-wider font-semibold text-gray-400">Pickup Code</span>
                      <span className="block text-2xl font-black tracking-[4px]" data-testid={`pickup-code-${child.id}`} style={{ color: '#FFC800' }}>{info?.pickup_code}</span>
                    </div>
                    <div className="flex items-center gap-1 justify-center text-xs text-gray-400 font-semibold mt-1.5">
                      <Clock className="w-3 h-3" />
                      {new Date(info?.checked_in_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                ) : (
                  <button
                    data-testid={`checkin-btn-${child.id}`}
                    onClick={startWizard}
                    className="block w-full mt-3 text-white font-extrabold text-sm py-2.5 rounded-xl cursor-pointer border-none"
                    style={{ background: color.bg, boxShadow: `0 3px 0 ${color.border}`, fontFamily: "'Nunito', sans-serif" }}
                  >
                    Check In
                  </button>
                )}
              </motion.div>
            );
          })
        )}
      </div>

      {/* Summary */}
      {checkins.filter(c => c.status === 'checked_in').length > 0 && (
        <motion.div className="max-w-[900px] mx-auto mt-5 px-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="flex items-center gap-4 rounded-[18px] px-5 py-4 text-white" style={{ background: '#1a1a2e' }}>
            <div className="w-12 h-12 rounded-xl flex items-center justify-center text-xl font-black shrink-0" style={{ background: '#58CC02' }}>
              {checkins.filter(c => c.status === 'checked_in').length}
            </div>
            <div>
              <strong className="block text-sm font-extrabold">
                {checkins.filter(c => c.status === 'checked_in').length === 1 ? 'child' : 'children'} in Sunday School
              </strong>
              <p className="text-gray-400 text-xs font-semibold mt-0.5">
                <Phone className="w-3 h-3 inline" /> We'll notify you if they need you
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* ===== 3-STEP WIZARD ===== */}
      <AnimatePresence>
        {wizardStep > 0 && (
          <motion.div
            className="fixed inset-0 z-[9998] flex items-end justify-center"
            style={{ background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          >
            <motion.div
              className="w-full max-w-[480px] bg-white rounded-t-[28px] p-6 max-h-[85vh] overflow-y-auto relative"
              style={{ fontFamily: "'Nunito', sans-serif" }}
              initial={{ y: '100%' }} animate={{ y: 0 }} exit={{ y: '100%' }}
              transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            >
              {/* Progress */}
              <div className="flex gap-2 justify-center mb-5">
                {[1, 2, 3].map(s => (
                  <div key={s} className="w-8 h-1.5 rounded-full transition-colors" style={{ background: wizardStep >= s ? '#58CC02' : '#e5e7eb' }} />
                ))}
              </div>

              <button data-testid="wizard-close" onClick={closeWizard} className="absolute top-4 right-4 bg-gray-100 border-none rounded-full w-9 h-9 flex items-center justify-center cursor-pointer text-gray-500">
                <X className="w-5 h-5" />
              </button>

              {/* Step 1 */}
              {wizardStep === 1 && (
                <div data-testid="wizard-step-1">
                  <h2 className="text-center font-black text-xl mb-1" style={{ color: '#1a1a2e' }}>Who's checking in today?</h2>
                  <p className="text-center text-sm text-gray-400 font-semibold mb-5">Tap to select</p>
                  <div className="grid gap-3" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))' }}>
                    {uncheckedChildren.map(child => {
                      const sel = selectedChildren.find(c => c.id === child.id);
                      const color = getCardColor(child.name);
                      return (
                        <motion.button
                          key={child.id} data-testid={`wizard-select-${child.id}`}
                          onClick={() => toggleSelect(child)} whileTap={{ scale: 0.95 }}
                          className="flex flex-col items-center gap-1.5 p-3 rounded-2xl cursor-pointer relative"
                          style={{
                            border: `3px solid ${sel ? '#58CC02' : '#e5e7eb'}`,
                            background: sel ? '#f0fce8' : '#fff',
                            fontFamily: "'Nunito', sans-serif"
                          }}
                        >
                          <img src={getAvatar(child.name)} alt={child.name} className="w-14 h-14 rounded-full" />
                          <span className="text-xs font-extrabold" style={{ color: '#1a1a2e' }}>{child.name}</span>
                          {sel && (
                            <div className="absolute top-1.5 right-1.5 w-5 h-5 rounded-full flex items-center justify-center text-white" style={{ background: '#58CC02' }}>
                              <Check className="w-3 h-3" />
                            </div>
                          )}
                        </motion.button>
                      );
                    })}
                  </div>
                  {uncheckedChildren.length === 0 && <p className="text-center text-gray-400 font-semibold py-4">All your kids are already checked in!</p>}
                  <button
                    data-testid="wizard-next-1"
                    disabled={selectedChildren.length === 0}
                    onClick={() => setWizardStep(2)}
                    className="flex items-center justify-center gap-1.5 w-full mt-5 text-white font-extrabold text-base py-3 rounded-xl border-none cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                    style={{ background: '#58CC02', boxShadow: '0 4px 0 #46a302', fontFamily: "'Nunito', sans-serif" }}
                  >
                    Next <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              )}

              {/* Step 2 */}
              {wizardStep === 2 && (
                <div data-testid="wizard-step-2">
                  <h2 className="text-center font-black text-xl mb-1" style={{ color: '#1a1a2e' }}>Confirm Check-in</h2>
                  <p className="text-center text-sm text-gray-400 font-semibold mb-5">
                    {selectedChildren.length} {selectedChildren.length === 1 ? 'child' : 'children'} for Sunday School
                  </p>
                  <div className="flex flex-col gap-3 mb-5">
                    {selectedChildren.map(child => (
                      <div key={child.id} className="flex items-center gap-3 bg-gray-50 rounded-xl px-4 py-3">
                        <img src={getAvatar(child.name)} alt={child.name} className="w-12 h-12 rounded-full shrink-0" />
                        <div>
                          <strong className="block text-sm font-extrabold" style={{ color: '#1a1a2e' }}>{child.name}</strong>
                          <span className="block text-xs text-gray-400 font-semibold">{formatAge(child.birthdate)}</span>
                          {child.allergies && <span className="block text-xs text-red-500 font-semibold">Allergy: {child.allergies}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-3">
                    <button data-testid="wizard-back-2" onClick={() => setWizardStep(1)} className="flex items-center gap-1 bg-gray-100 text-gray-500 font-extrabold text-sm px-5 py-3 rounded-xl border-none cursor-pointer" style={{ fontFamily: "'Nunito', sans-serif" }}>
                      <ChevronLeft className="w-5 h-5" /> Back
                    </button>
                    <button data-testid="wizard-confirm" onClick={handleBulkCheckin} className="flex-1 flex items-center justify-center gap-1.5 text-white font-extrabold text-base py-3 rounded-xl border-none cursor-pointer" style={{ background: '#FF9600', boxShadow: '0 4px 0 #e08500', fontFamily: "'Nunito', sans-serif" }}>
                      Check In Now
                    </button>
                  </div>
                </div>
              )}

              {/* Step 3: Success */}
              {wizardStep === 3 && (
                <div className="text-center" data-testid="wizard-step-3">
                  <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3 text-white" style={{ background: 'linear-gradient(135deg, #FFC800, #FF9600)' }}>
                    <Sparkles className="w-8 h-8" />
                  </div>
                  <h2 className="font-black text-xl mb-1" style={{ color: '#1a1a2e' }}>All Set!</h2>
                  <p className="text-sm text-gray-400 font-semibold mb-5">Show these codes at pickup</p>
                  <div className="grid gap-3 mb-5" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))' }}>
                    {checkinResults.filter(r => r.success).map(r => (
                      <div key={r.child.id} className="bg-gray-50 rounded-2xl p-4 text-center">
                        <img src={getAvatar(r.child.name)} alt={r.child.name} className="w-12 h-12 rounded-full mx-auto mb-1" />
                        <strong className="block text-sm font-extrabold mb-2" data-testid={`result-name-${r.child.id}`} style={{ color: '#1a1a2e' }}>{r.child.name}</strong>
                        <div className="mx-auto mb-2" data-testid={`result-qr-${r.child.id}`}>
                          <QRCodeSVG value={`SOLOMON_PICKUP_${r.child.id}_${r.pickup_code}_${new Date().toISOString().split('T')[0]}`} size={90} level="M" bgColor="#ffffff" fgColor="#1a1a2e" />
                        </div>
                        <span className="block text-[10px] uppercase text-gray-400 font-semibold tracking-wide">Pickup Code</span>
                        <strong className="block text-xl tracking-[3px]" data-testid={`result-code-${r.child.id}`} style={{ color: '#FF9600' }}>{r.pickup_code}</strong>
                      </div>
                    ))}
                  </div>
                  <button data-testid="wizard-done" onClick={closeWizard} className="w-full text-white font-extrabold text-base py-3 rounded-xl border-none cursor-pointer" style={{ background: '#58CC02', boxShadow: '0 4px 0 #46a302', fontFamily: "'Nunito', sans-serif" }}>
                    Done
                  </button>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ===== ADD CHILD MODAL ===== */}
      <AnimatePresence>
        {showAddChild && (
          <motion.div
            className="fixed inset-0 z-[9998] flex items-center justify-center p-4"
            style={{ background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setShowAddChild(false)}
          >
            <motion.div
              className="w-full max-w-[440px] bg-white rounded-3xl p-6 relative max-h-[90vh] overflow-y-auto"
              style={{ fontFamily: "'Nunito', sans-serif" }}
              initial={{ y: 40, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 40, opacity: 0 }}
              onClick={e => e.stopPropagation()}
            >
              <button data-testid="close-add-child" onClick={() => setShowAddChild(false)} className="absolute top-4 right-4 bg-gray-100 border-none rounded-full w-9 h-9 flex items-center justify-center cursor-pointer text-gray-500">
                <X className="w-5 h-5" />
              </button>
              <div className="text-center mb-5">
                <img src={getAvatar('new-friend')} alt="" className="w-[72px] h-[72px] mx-auto mb-2" />
                <h2 className="font-black text-xl" style={{ color: '#1a1a2e' }}>Add a Child</h2>
                <p className="text-sm text-gray-400 font-semibold">Register for Sunday School — any age welcome!</p>
              </div>
              <div className="flex flex-col gap-3">
                <div>
                  <label className="block text-xs font-extrabold text-gray-700 mb-1">Child's Name *</label>
                  <input data-testid="child-name-input" value={newChild.name} onChange={e => setNewChild({...newChild, name: e.target.value})} placeholder="e.g., Sophie" className="w-full px-3 py-2.5 rounded-xl text-sm font-semibold outline-none" style={{ border: '2px solid #e5e7eb', fontFamily: "'Nunito', sans-serif", color: '#1a1a2e' }} />
                </div>
                <div>
                  <label className="block text-xs font-extrabold text-gray-700 mb-1">Date of Birth *</label>
                  <input data-testid="child-birthdate-input" type="date" value={newChild.birthdate} onChange={e => setNewChild({...newChild, birthdate: e.target.value})} className="w-full px-3 py-2.5 rounded-xl text-sm font-semibold outline-none" style={{ border: '2px solid #e5e7eb', fontFamily: "'Nunito', sans-serif", color: '#1a1a2e' }} />
                </div>
                <div>
                  <label className="block text-xs font-extrabold text-gray-700 mb-1">Allergies</label>
                  <input data-testid="child-allergies-input" value={newChild.allergies} onChange={e => setNewChild({...newChild, allergies: e.target.value})} placeholder="Peanuts, Dairy..." className="w-full px-3 py-2.5 rounded-xl text-sm font-semibold outline-none" style={{ border: '2px solid #e5e7eb', fontFamily: "'Nunito', sans-serif", color: '#1a1a2e' }} />
                </div>
                <div>
                  <label className="block text-xs font-extrabold text-gray-700 mb-1">Special Needs / Notes</label>
                  <textarea value={newChild.special_needs} onChange={e => setNewChild({...newChild, special_needs: e.target.value})} placeholder="Anything we should know?" rows={2} className="w-full px-3 py-2.5 rounded-xl text-sm font-semibold outline-none resize-y" style={{ border: '2px solid #e5e7eb', fontFamily: "'Nunito', sans-serif", color: '#1a1a2e' }} />
                </div>
                <div className="text-xs font-extrabold text-gray-400 uppercase tracking-wide pt-2 mt-1 border-t border-gray-100">Emergency Contact</div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-extrabold text-gray-700 mb-1">Name</label>
                    <input value={newChild.emergency_contact} onChange={e => setNewChild({...newChild, emergency_contact: e.target.value})} placeholder="Contact name" className="w-full px-3 py-2.5 rounded-xl text-sm font-semibold outline-none" style={{ border: '2px solid #e5e7eb', fontFamily: "'Nunito', sans-serif", color: '#1a1a2e' }} />
                  </div>
                  <div>
                    <label className="block text-xs font-extrabold text-gray-700 mb-1">Phone</label>
                    <input type="tel" value={newChild.emergency_phone} onChange={e => setNewChild({...newChild, emergency_phone: e.target.value})} placeholder="(555) 123-4567" className="w-full px-3 py-2.5 rounded-xl text-sm font-semibold outline-none" style={{ border: '2px solid #e5e7eb', fontFamily: "'Nunito', sans-serif", color: '#1a1a2e' }} />
                  </div>
                </div>
                <button data-testid="save-child-btn" onClick={addChild} className="w-full mt-2 inline-flex items-center justify-center gap-1.5 text-white font-extrabold text-sm py-3 rounded-xl border-none cursor-pointer" style={{ background: '#58CC02', boxShadow: '0 4px 0 #46a302', fontFamily: "'Nunito', sans-serif" }}>
                  Add Child
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
