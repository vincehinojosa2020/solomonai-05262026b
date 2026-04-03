import { useState, useEffect } from 'react';
import { MapPin, ChevronRight, Check } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

/**
 * CampusSelectorModal — Shows on first login for multi-campus churches.
 * "Which campus do you call home?"
 * 
 * Props:
 *   user: current user object
 *   onSelect: callback(campus) after selection
 *   onSkip: callback to dismiss without selecting
 */
export default function CampusSelectorModal({ user, onSelect, onSkip }) {
  const [campuses, setCampuses] = useState([]);
  const [parentName, setParentName] = useState('');
  const [selected, setSelected] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchCampuses();
  }, []);

  const fetchCampuses = async () => {
    try {
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/portal/campuses`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCampuses(data.campuses || []);
        setParentName(data.parent_name || '');
        setSelected(data.home_campus_id || '');
        // If not multi-campus or already selected, skip
        if (!data.is_multi_campus || user?.campus_selected) {
          onSkip?.();
        }
      }
    } catch (e) {
      console.error(e);
      onSkip?.();
    }
  };

  const handleConfirm = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/portal/campus/select`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ campus_id: selected }),
      });
      if (res.ok) {
        const d = await res.json();
        toast.success(`Welcome to ${d.campus_name}!`);
        onSelect?.(campuses.find(c => c.id === selected));
      }
    } catch (e) {
      toast.error('Failed to set campus');
    } finally {
      setSaving(false);
    }
  };

  if (campuses.length <= 1) return null;

  return (
    <div className="fixed inset-0 z-[200] bg-black/60 flex items-end sm:items-center justify-center p-4" data-testid="campus-selector-modal">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
        <div className="px-6 pt-6 pb-4 border-b border-slate-100">
          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
            <MapPin className="w-6 h-6 text-blue-600" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Which campus do you call home?</h2>
          <p className="text-sm text-slate-500 mt-1">
            You can change this anytime from your profile.
          </p>
        </div>

        <div className="p-4 space-y-2">
          {campuses.map(campus => (
            <button
              key={campus.id}
              onClick={() => setSelected(campus.id)}
              className={`w-full flex items-center justify-between p-4 border-2 rounded-xl transition-all ${
                selected === campus.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-slate-200 hover:border-slate-300 bg-white'
              }`}
              data-testid={`campus-option-${campus.id}`}
            >
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-sm ${selected === campus.id ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600'}`}>
                  {campus.label.charAt(0)}
                </div>
                <div className="text-left">
                  <p className="font-semibold text-slate-900">{parentName} {campus.label}</p>
                  {campus.address && <p className="text-xs text-slate-500">{campus.address}</p>}
                </div>
              </div>
              {selected === campus.id && <Check className="w-5 h-5 text-blue-600 flex-shrink-0" />}
            </button>
          ))}
        </div>

        <div className="p-4 border-t border-slate-100 flex gap-3">
          <button
            onClick={onSkip}
            className="flex-1 py-3 border border-slate-200 rounded-xl text-sm text-slate-600 hover:bg-slate-50"
          >
            Ask me later
          </button>
          <button
            onClick={handleConfirm}
            disabled={!selected || saving}
            className="flex-1 py-3 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-1.5"
            data-testid="campus-confirm-btn"
          >
            {saving ? 'Saving...' : <>This is my campus <ChevronRight className="w-4 h-4" /></>}
          </button>
        </div>
      </div>
    </div>
  );
}
