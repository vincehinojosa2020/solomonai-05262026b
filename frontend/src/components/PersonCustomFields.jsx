import { useState, useEffect } from 'react';
import { Save, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

export default function PersonCustomFields({ personId }) {
  const [definitions, setDefinitions] = useState([]);
  const [values, setValues] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (personId) fetchData();
  }, [personId]);

  const fetchData = async () => {
    try {
      const token = sessionStorage.getItem('session_token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const [defsRes, valsRes] = await Promise.all([
        fetch(`${API_URL}/admin/custom-field-definitions`, { headers }),
        fetch(`${API_URL}/admin/people/${personId}/custom-fields`, { headers }),
      ]);
      if (defsRes.ok) {
        const d = await defsRes.json();
        setDefinitions((d.fields || []).filter(f => f.is_active));
      }
      if (valsRes.ok) {
        const v = await valsRes.json();
        setValues(v.custom_fields || {});
      }
    } catch (err) {
      console.error('Failed to load custom fields:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (key, val) => {
    setValues(prev => ({ ...prev, [key]: val }));
    setDirty(true);
  };

  const handleMultiSelect = (key, option) => {
    const current = values[key] || [];
    const updated = current.includes(option)
      ? current.filter(o => o !== option)
      : [...current, option];
    handleChange(key, updated);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/admin/people/${personId}/custom-fields`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ custom_fields: values }),
      });
      if (res.ok) {
        toast.success('Custom fields saved');
        setDirty(false);
      } else {
        toast.error('Failed to save');
      }
    } catch {
      toast.error('Failed to save');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return null;
  if (definitions.length === 0) return null;

  const renderField = (def) => {
    const key = def.field_key;
    const val = values[key] ?? '';

    switch (def.field_type) {
      case 'text':
        return (
          <input
            value={val}
            onChange={(e) => handleChange(key, e.target.value)}
            className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
            placeholder={`Enter ${def.name.toLowerCase()}`}
            data-testid={`cf-input-${key}`}
          />
        );
      case 'textarea':
        return (
          <textarea
            value={val}
            onChange={(e) => handleChange(key, e.target.value)}
            rows={2}
            className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm resize-none"
            placeholder={`Enter ${def.name.toLowerCase()}`}
            data-testid={`cf-input-${key}`}
          />
        );
      case 'number':
        return (
          <input
            type="number"
            value={val}
            onChange={(e) => handleChange(key, e.target.value)}
            className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
            data-testid={`cf-input-${key}`}
          />
        );
      case 'date':
        return (
          <input
            type="date"
            value={val}
            onChange={(e) => handleChange(key, e.target.value)}
            className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
            data-testid={`cf-input-${key}`}
          />
        );
      case 'boolean':
        return (
          <label className="flex items-center gap-2 cursor-pointer" data-testid={`cf-input-${key}`}>
            <input
              type="checkbox"
              checked={!!val}
              onChange={(e) => handleChange(key, e.target.checked)}
              className="w-4 h-4 rounded border-slate-300"
            />
            <span className="text-sm text-slate-600">Yes</span>
          </label>
        );
      case 'select':
        return (
          <select
            value={val}
            onChange={(e) => handleChange(key, e.target.value)}
            className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
            data-testid={`cf-input-${key}`}
          >
            <option value="">— Select —</option>
            {(def.options || []).map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        );
      case 'multiselect':
        return (
          <div className="flex flex-wrap gap-1.5" data-testid={`cf-input-${key}`}>
            {(def.options || []).map(opt => {
              const selected = (values[key] || []).includes(opt);
              return (
                <button
                  key={opt}
                  type="button"
                  onClick={() => handleMultiSelect(key, opt)}
                  className={`px-2.5 py-1 rounded-full text-xs border transition-all ${
                    selected
                      ? 'bg-blue-50 border-blue-300 text-blue-700 font-medium'
                      : 'border-slate-200 text-slate-500 hover:border-slate-300'
                  }`}
                >
                  {opt}
                </button>
              );
            })}
          </div>
        );
      default:
        return <input value={val} onChange={(e) => handleChange(key, e.target.value)} className="w-full px-3 py-2 border rounded-lg text-sm" />;
    }
  };

  return (
    <div className="bento-card" data-testid="person-custom-fields">
      <div className="card-header mb-4">
        <h3 className="card-title">Custom Fields</h3>
        {dirty && (
          <Button
            size="sm"
            className="bg-slate-900 text-white hover:bg-slate-800 h-7 text-xs"
            onClick={handleSave}
            disabled={saving}
            data-testid="save-custom-fields-btn"
          >
            {saving ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Save className="w-3 h-3 mr-1" />}
            Save
          </Button>
        )}
      </div>
      <div className="space-y-3">
        {definitions.map((def) => (
          <div key={def.id}>
            <label className="block text-xs font-medium text-slate-500 mb-1">
              {def.name}
              {def.required && <span className="text-red-500 ml-0.5">*</span>}
            </label>
            {renderField(def)}
          </div>
        ))}
      </div>
    </div>
  );
}
