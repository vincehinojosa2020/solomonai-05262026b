import { useState } from 'react';
import { Search, Keyboard, X } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import { getAvatarStyle, formatAge, CLASSROOMS } from './constants';

export function ManualCheckinModal({ allKids, onClose, onSuccess }) {
  const [search, setSearch] = useState('');
  const [classroom, setClassroom] = useState('Sunday School');

  const filtered = allKids.filter(k =>
    search && (k.name?.toLowerCase().includes(search.toLowerCase()) || k.parent_name?.toLowerCase().includes(search.toLowerCase()))
  );

  const handleCheckin = async (kid) => {
    try {
      const res = await fetch(`${API_URL}/admin/kids/checkin`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ child_id: kid.id, classroom }),
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(`${kid.name} checked in! Code: ${data.security_code}`);
        onSuccess?.();
        onClose();
      } else { const err = await res.json(); toast.error(err.detail || 'Check-in failed'); }
    } catch { toast.error('Check-in failed'); }
  };

  return (
    <div className="kca-modal-overlay" data-testid="manual-checkin-modal">
      <div className="kca-modal">
        <div className="kca-modal-header">
          <h2><Keyboard className="w-5 h-5" /> Manual Check-In</h2>
          <button onClick={onClose} className="kca-modal-close"><X className="w-5 h-5" /></button>
        </div>
        <div style={{ padding: '20px' }}>
          <div className="kca-search-bar" style={{ marginBottom: '12px' }}>
            <Search className="kca-search-icon" />
            <input type="text" placeholder="Search child or parent name..." value={search} onChange={e => setSearch(e.target.value)} className="kca-search-input" autoFocus data-testid="manual-search" />
          </div>
          <div style={{ marginBottom: '12px' }}>
            <label className="text-xs font-medium text-slate-500">CLASSROOM</label>
            <select value={classroom} onChange={e => setClassroom(e.target.value)} className="kca-input" style={{ marginTop: '4px' }}>
              {CLASSROOMS.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          {search && (
            <div className="kca-search-results" style={{ maxHeight: '300px', overflowY: 'auto' }}>
              {filtered.length === 0 ? (
                <p className="text-slate-400 text-sm py-4 text-center">No children found matching "{search}"</p>
              ) : filtered.map(kid => {
                const avatar = getAvatarStyle(kid.name);
                return (
                  <div key={kid.id} className="kca-search-result" onClick={() => handleCheckin(kid)} data-testid={`manual-kid-${kid.id}`} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '10px', borderRadius: '8px', cursor: 'pointer', marginBottom: '4px', border: '1px solid #e2e8f0' }}>
                    <div className="kca-avatar-sm" style={{ background: avatar.bg, width: '36px', height: '36px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px' }}>{avatar.emoji}</div>
                    <div><p className="text-sm font-medium">{kid.name}</p><p className="text-xs text-slate-400">{formatAge(kid.birthdate)} | Parent: {kid.parent_name}</p></div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
