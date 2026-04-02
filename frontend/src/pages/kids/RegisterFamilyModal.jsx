import { useState } from 'react';
import { Plus, X, User } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import { CLASSROOMS } from './constants';

export function RegisterFamilyModal({ onClose, onSuccess }) {
  const [form, setForm] = useState({
    parentName: '', parentEmail: '', parentPhone: '',
    childName: '', childBirthdate: '', childAllergies: '', childNotes: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.parentName || !form.childName) { toast.error('Parent and child names required'); return; }
    setSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/admin/kids/register-family`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parent_name: form.parentName, parent_email: form.parentEmail, parent_phone: form.parentPhone,
          child_name: form.childName, child_birthdate: form.childBirthdate,
          allergies: form.childAllergies, notes: form.childNotes,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message || 'Family registered!');
        onSuccess?.();
        onClose();
      } else { const err = await res.json(); toast.error(err.detail || 'Registration failed'); }
    } catch { toast.error('Registration failed'); }
    finally { setSubmitting(false); }
  };

  return (
    <div className="kca-modal-overlay" data-testid="register-family-modal">
      <div className="kca-modal">
        <div className="kca-modal-header">
          <h2><Plus className="w-5 h-5" /> Register New Family</h2>
          <button onClick={onClose} className="kca-modal-close"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="kca-form">
          <div className="kca-form-section">
            <h3><User className="w-4 h-4" /> Parent Information</h3>
            <input type="text" placeholder="Parent Name *" value={form.parentName} onChange={e => setForm({...form, parentName: e.target.value})} className="kca-input" data-testid="parent-name-input" />
            <div className="kca-form-row">
              <input type="email" placeholder="Email" value={form.parentEmail} onChange={e => setForm({...form, parentEmail: e.target.value})} className="kca-input" />
              <input type="tel" placeholder="Phone" value={form.parentPhone} onChange={e => setForm({...form, parentPhone: e.target.value})} className="kca-input" />
            </div>
          </div>
          <div className="kca-form-section">
            <h3>Child Information</h3>
            <input type="text" placeholder="Child Name *" value={form.childName} onChange={e => setForm({...form, childName: e.target.value})} className="kca-input" data-testid="child-name-input" />
            <div className="kca-form-row">
              <input type="date" value={form.childBirthdate} onChange={e => setForm({...form, childBirthdate: e.target.value})} className="kca-input" />
              <input type="text" placeholder="Allergies" value={form.childAllergies} onChange={e => setForm({...form, childAllergies: e.target.value})} className="kca-input" />
            </div>
            <input type="text" placeholder="Special notes" value={form.childNotes} onChange={e => setForm({...form, childNotes: e.target.value})} className="kca-input" />
          </div>
          <div className="kca-form-actions">
            <button type="button" onClick={onClose} className="kca-btn-secondary">Cancel</button>
            <button type="submit" disabled={submitting} className="kca-btn-primary" data-testid="register-family-submit">{submitting ? 'Registering...' : 'Register Family'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
