import { useState } from 'react';
import { X, Building2, Clock, Palette, UserPlus, Check, ChevronRight, ChevronLeft, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

const STEPS = [
  { id: 1, title: 'Church Info', icon: Building2 },
  { id: 2, title: 'Services', icon: Clock },
  { id: 3, title: 'Branding', icon: Palette },
  { id: 4, title: 'Admin Account', icon: UserPlus },
  { id: 5, title: 'Review', icon: Check },
];

const PRESET_COLORS = ['#2563eb', '#059669', '#7c3aed', '#dc2626', '#ea580c', '#0891b2', '#4f46e5', '#be185d'];

export default function ChurchOnboardingWizard({ isOpen, onClose, onSuccess }) {
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    name: '', city: '', state: '', denomination: '', website: '', estimated_members: '',
    service_times: [{ day: 'Sunday', time: '09:00', name: 'Sunday Morning' }],
    primary_color: '#2563eb', subdomain: '',
    admin_name: '', admin_email: '', admin_password: '', admin_phone: '',
    plan: 'starter',
  });

  const update = (field, value) => setForm(prev => ({ ...prev, [field]: value }));

  const addServiceTime = () => {
    setForm(prev => ({ ...prev, service_times: [...prev.service_times, { day: 'Sunday', time: '11:00', name: '' }] }));
  };

  const updateServiceTime = (idx, field, value) => {
    setForm(prev => {
      const times = [...prev.service_times];
      times[idx] = { ...times[idx], [field]: value };
      return { ...prev, service_times: times };
    });
  };

  const removeServiceTime = (idx) => {
    setForm(prev => ({ ...prev, service_times: prev.service_times.filter((_, i) => i !== idx) }));
  };

  const autoSubdomain = (name) => name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '').slice(0, 30);

  const canNext = () => {
    if (step === 1) return form.name.trim().length > 0;
    if (step === 4) return form.admin_email.trim().length > 0 && form.admin_password.length >= 6;
    return true;
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const token = localStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/platform/churches/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
        body: JSON.stringify({
          ...form,
          estimated_members: parseInt(form.estimated_members) || 0,
          subdomain: form.subdomain || autoSubdomain(form.name),
        }),
      });

      if (res.ok) {
        const data = await res.json();
        toast.success(`${data.church_name} created successfully!`);
        onSuccess?.(data);
        onClose();
        setStep(1);
        setForm({ name: '', city: '', state: '', denomination: '', website: '', estimated_members: '', service_times: [{ day: 'Sunday', time: '09:00', name: 'Sunday Morning' }], primary_color: '#2563eb', subdomain: '', admin_name: '', admin_email: '', admin_password: '', admin_phone: '', plan: 'starter' });
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to create church');
      }
    } catch (error) {
      toast.error('Network error');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" data-testid="onboarding-wizard">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <div>
            <h2 className="text-lg font-bold text-slate-900" data-testid="wizard-title">Add New Church</h2>
            <p className="text-sm text-slate-500">Step {step} of 5 — {STEPS[step - 1].title}</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-lg" data-testid="wizard-close">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Progress */}
        <div className="flex items-center gap-1 px-6 pt-4">
          {STEPS.map((s) => (
            <div key={s.id} className={`flex-1 h-1.5 rounded-full transition-colors ${s.id <= step ? 'bg-blue-600' : 'bg-slate-200'}`} />
          ))}
        </div>

        {/* Body */}
        <div className="p-6 space-y-5">
          {/* Step 1: Church Info */}
          {step === 1 && (
            <>
              <div>
                <Label>Church Name *</Label>
                <Input value={form.name} onChange={(e) => { update('name', e.target.value); if (!form.subdomain) update('subdomain', autoSubdomain(e.target.value)); }} placeholder="e.g. Grace Community Church" data-testid="wizard-church-name" className="mt-1" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>City</Label>
                  <Input value={form.city} onChange={(e) => update('city', e.target.value)} placeholder="Charlotte" className="mt-1" data-testid="wizard-city" />
                </div>
                <div>
                  <Label>State</Label>
                  <Input value={form.state} onChange={(e) => update('state', e.target.value)} placeholder="NC" className="mt-1" data-testid="wizard-state" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Denomination</Label>
                  <Input value={form.denomination} onChange={(e) => update('denomination', e.target.value)} placeholder="Non-denominational" className="mt-1" />
                </div>
                <div>
                  <Label>Estimated Members</Label>
                  <Input type="number" value={form.estimated_members} onChange={(e) => update('estimated_members', e.target.value)} placeholder="200" className="mt-1" />
                </div>
              </div>
              <div>
                <Label>Website</Label>
                <Input value={form.website} onChange={(e) => update('website', e.target.value)} placeholder="https://gracechurch.com" className="mt-1" />
              </div>
            </>
          )}

          {/* Step 2: Service Times */}
          {step === 2 && (
            <>
              <p className="text-sm text-slate-500">Define when services happen. You can change these later.</p>
              {form.service_times.map((st, idx) => (
                <div key={idx} className="flex items-end gap-3 p-3 bg-slate-50 rounded-lg">
                  <div className="flex-1">
                    <Label className="text-xs">Day</Label>
                    <select value={st.day} onChange={(e) => updateServiceTime(idx, 'day', e.target.value)} className="w-full h-9 rounded-md border border-slate-300 px-3 text-sm mt-1">
                      {['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].map(d => <option key={d} value={d}>{d}</option>)}
                    </select>
                  </div>
                  <div className="w-28">
                    <Label className="text-xs">Time</Label>
                    <Input type="time" value={st.time} onChange={(e) => updateServiceTime(idx, 'time', e.target.value)} className="mt-1" />
                  </div>
                  <div className="flex-1">
                    <Label className="text-xs">Name</Label>
                    <Input value={st.name} onChange={(e) => updateServiceTime(idx, 'name', e.target.value)} placeholder="Sunday Morning" className="mt-1" />
                  </div>
                  {form.service_times.length > 1 && (
                    <button onClick={() => removeServiceTime(idx)} className="p-2 text-red-500 hover:bg-red-50 rounded-lg"><X className="w-4 h-4" /></button>
                  )}
                </div>
              ))}
              <Button variant="outline" size="sm" onClick={addServiceTime}>+ Add Service Time</Button>
            </>
          )}

          {/* Step 3: Branding */}
          {step === 3 && (
            <>
              <div>
                <Label>Primary Color</Label>
                <div className="flex items-center gap-3 mt-2">
                  {PRESET_COLORS.map(c => (
                    <button key={c} onClick={() => update('primary_color', c)} className={`w-9 h-9 rounded-full border-2 transition-all ${form.primary_color === c ? 'border-slate-900 scale-110' : 'border-transparent'}`} style={{ backgroundColor: c }} data-testid={`color-${c}`} />
                  ))}
                  <Input type="color" value={form.primary_color} onChange={(e) => update('primary_color', e.target.value)} className="w-9 h-9 p-0 border-0 cursor-pointer" />
                </div>
              </div>
              <div>
                <Label>Subdomain</Label>
                <div className="flex items-center gap-0 mt-1">
                  <Input value={form.subdomain || autoSubdomain(form.name)} onChange={(e) => update('subdomain', e.target.value)} className="rounded-r-none" data-testid="wizard-subdomain" />
                  <span className="inline-flex items-center h-9 px-3 bg-slate-100 border border-l-0 border-slate-300 rounded-r-md text-sm text-slate-500">.solomon.ai</span>
                </div>
              </div>
              <div>
                <Label>Plan</Label>
                <div className="grid grid-cols-3 gap-3 mt-2">
                  {['starter', 'growth', 'enterprise'].map(p => (
                    <button key={p} onClick={() => update('plan', p)} className={`p-4 rounded-xl border-2 text-center transition-all ${form.plan === p ? 'border-blue-600 bg-blue-50' : 'border-slate-200 hover:border-slate-300'}`} data-testid={`plan-${p}`}>
                      <span className="text-sm font-semibold capitalize block">{p}</span>
                      <span className="text-xs text-slate-500">{p === 'starter' ? '$49/mo' : p === 'growth' ? '$149/mo' : '$299/mo'}</span>
                    </button>
                  ))}
                </div>
              </div>
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50">
                <p className="text-sm font-medium text-slate-700 mb-2">Preview</p>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center text-white text-sm font-bold" style={{ backgroundColor: form.primary_color }}>
                    {form.name?.charAt(0)?.toUpperCase() || 'C'}
                  </div>
                  <div>
                    <p className="font-semibold text-sm" style={{ color: form.primary_color }}>{form.name || 'Church Name'}</p>
                    <p className="text-xs text-slate-500">{form.subdomain || autoSubdomain(form.name)}.solomon.ai</p>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Step 4: Admin Account */}
          {step === 4 && (
            <>
              <p className="text-sm text-slate-500">Create the primary admin account for this church.</p>
              <div>
                <Label>Full Name</Label>
                <Input value={form.admin_name} onChange={(e) => update('admin_name', e.target.value)} placeholder="Pastor John Smith" className="mt-1" data-testid="wizard-admin-name" />
              </div>
              <div>
                <Label>Email *</Label>
                <Input type="email" value={form.admin_email} onChange={(e) => update('admin_email', e.target.value)} placeholder="pastor@church.com" className="mt-1" data-testid="wizard-admin-email" />
              </div>
              <div>
                <Label>Password * (min 6 characters)</Label>
                <Input type="password" value={form.admin_password} onChange={(e) => update('admin_password', e.target.value)} placeholder="Secure password" className="mt-1" data-testid="wizard-admin-password" />
              </div>
              <div>
                <Label>Phone</Label>
                <Input type="tel" value={form.admin_phone} onChange={(e) => update('admin_phone', e.target.value)} placeholder="(555) 123-4567" className="mt-1" />
              </div>
            </>
          )}

          {/* Step 5: Review */}
          {step === 5 && (
            <>
              <p className="text-sm text-slate-500 mb-4">Please review the details before creating this church.</p>
              <div className="space-y-4">
                <div className="p-4 bg-slate-50 rounded-xl space-y-2">
                  <p className="font-semibold text-slate-700 text-xs uppercase tracking-wide">Church Info</p>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <span className="text-slate-500">Name:</span><span className="font-medium">{form.name}</span>
                    <span className="text-slate-500">Location:</span><span className="font-medium">{form.city}{form.state ? `, ${form.state}` : ''}</span>
                    <span className="text-slate-500">Subdomain:</span><span className="font-medium font-mono">{form.subdomain || autoSubdomain(form.name)}.solomon.ai</span>
                    <span className="text-slate-500">Plan:</span><span className="font-medium capitalize">{form.plan}</span>
                  </div>
                </div>
                <div className="p-4 bg-slate-50 rounded-xl space-y-2">
                  <p className="font-semibold text-slate-700 text-xs uppercase tracking-wide">Service Times</p>
                  {form.service_times.map((st, i) => (
                    <p key={i} className="text-sm"><span className="font-medium">{st.name || st.day}</span> — {st.day} at {st.time}</p>
                  ))}
                </div>
                <div className="p-4 bg-slate-50 rounded-xl space-y-2">
                  <p className="font-semibold text-slate-700 text-xs uppercase tracking-wide">Admin Account</p>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <span className="text-slate-500">Name:</span><span className="font-medium">{form.admin_name}</span>
                    <span className="text-slate-500">Email:</span><span className="font-medium">{form.admin_email}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-xl">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center text-white text-sm font-bold" style={{ backgroundColor: form.primary_color }}>
                    {form.name?.charAt(0)?.toUpperCase() || 'C'}
                  </div>
                  <div>
                    <p className="font-semibold text-sm" style={{ color: form.primary_color }}>{form.name}</p>
                    <p className="text-xs text-slate-500">Ready to launch</p>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-slate-200">
          {step > 1 ? (
            <Button variant="outline" onClick={() => setStep(step - 1)} data-testid="wizard-back">
              <ChevronLeft className="w-4 h-4 mr-1" /> Back
            </Button>
          ) : <div />}
          {step < 5 ? (
            <Button onClick={() => setStep(step + 1)} disabled={!canNext()} data-testid="wizard-next">
              Next <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          ) : (
            <Button onClick={handleSubmit} disabled={submitting} className="bg-green-600 hover:bg-green-700" data-testid="wizard-create">
              {submitting ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Creating...</> : <><Check className="w-4 h-4 mr-2" /> Create Church</>}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
