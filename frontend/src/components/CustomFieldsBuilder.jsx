import { useState, useEffect } from 'react';
import { Plus, GripVertical, Pencil, Trash2, X, Loader2, ToggleLeft, ToggleRight, Settings2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

const FIELD_TYPES = [
  { value: 'text', label: 'Text' },
  { value: 'textarea', label: 'Long Text' },
  { value: 'number', label: 'Number' },
  { value: 'date', label: 'Date' },
  { value: 'boolean', label: 'Yes / No' },
  { value: 'select', label: 'Dropdown' },
  { value: 'multiselect', label: 'Multi-Select' },
];

const CATEGORIES = [
  { value: 'personal', label: 'Personal' },
  { value: 'church', label: 'Church' },
  { value: 'medical', label: 'Medical' },
  { value: 'other', label: 'Other' },
];

const TYPE_COLORS = {
  text: 'bg-blue-50 text-blue-700',
  textarea: 'bg-blue-50 text-blue-600',
  number: 'bg-emerald-50 text-emerald-700',
  date: 'bg-amber-50 text-amber-700',
  boolean: 'bg-violet-50 text-violet-700',
  select: 'bg-rose-50 text-rose-700',
  multiselect: 'bg-rose-50 text-rose-600',
};

function FieldEditor({ field, onSave, onClose }) {
  const isEdit = !!field;
  const [name, setName] = useState(field?.name || '');
  const [fieldType, setFieldType] = useState(field?.field_type || 'text');
  const [category, setCategory] = useState(field?.category || 'other');
  const [required, setRequired] = useState(field?.required || false);
  const [options, setOptions] = useState(field?.options?.join('\n') || '');
  const [saving, setSaving] = useState(false);

  const showOptions = fieldType === 'select' || fieldType === 'multiselect';

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) { toast.error('Field name is required'); return; }
    if (showOptions && !options.trim()) { toast.error('Add at least one option'); return; }
    setSaving(true);
    try {
      await onSave({
        name: name.trim(),
        field_type: fieldType,
        category,
        required,
        options: showOptions ? options.split('\n').map(o => o.trim()).filter(Boolean) : [],
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" data-testid="field-editor-modal">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4">
        <div className="px-6 py-4 border-b flex items-center justify-between">
          <h3 className="font-semibold text-slate-900">{isEdit ? 'Edit Field' : 'Add Custom Field'}</h3>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded"><X className="w-4 h-4" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1 uppercase tracking-wide">Field Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g. Shirt Size, Allergies, Spiritual Gifts"
              data-testid="field-name-input"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1 uppercase tracking-wide">Type</label>
              <select
                value={fieldType}
                onChange={(e) => setFieldType(e.target.value)}
                className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm"
                data-testid="field-type-select"
              >
                {FIELD_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1 uppercase tracking-wide">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm"
                data-testid="field-category-select"
              >
                {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
          </div>
          {showOptions && (
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1 uppercase tracking-wide">Options (one per line)</label>
              <textarea
                value={options}
                onChange={(e) => setOptions(e.target.value)}
                rows={4}
                className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm font-mono"
                placeholder="Small\nMedium\nLarge\nX-Large"
                data-testid="field-options-input"
              />
            </div>
          )}
          <label className="flex items-center gap-2 cursor-pointer" data-testid="field-required-toggle">
            <input type="checkbox" checked={required} onChange={(e) => setRequired(e.target.checked)} className="sr-only" />
            {required ? <ToggleRight className="w-5 h-5 text-blue-600" /> : <ToggleLeft className="w-5 h-5 text-slate-400" />}
            <span className="text-sm text-slate-700">Required field</span>
          </label>
          <div className="flex gap-2 pt-2">
            <Button type="button" variant="outline" className="flex-1" onClick={onClose}>Cancel</Button>
            <Button type="submit" className="flex-1 bg-slate-900 text-white hover:bg-slate-800" disabled={saving} data-testid="save-field-btn">
              {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : null}
              {isEdit ? 'Save Changes' : 'Add Field'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function CustomFieldsBuilder() {
  const [fields, setFields] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEditor, setShowEditor] = useState(false);
  const [editingField, setEditingField] = useState(null);

  useEffect(() => { fetchFields(); }, []);

  const fetchFields = async () => {
    try {
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/admin/custom-field-definitions`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setFields(data.fields || []);
      }
    } catch (err) {
      console.error('Failed to fetch fields:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (data) => {
    const token = sessionStorage.getItem('session_token');
    const res = await fetch(`${API_URL}/admin/custom-field-definitions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json();
      toast.error(err.detail || 'Failed to create');
      return;
    }
    toast.success('Custom field created!');
    setShowEditor(false);
    fetchFields();
  };

  const handleUpdate = async (data) => {
    const token = sessionStorage.getItem('session_token');
    const res = await fetch(`${API_URL}/admin/custom-field-definitions/${editingField.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json();
      toast.error(err.detail || 'Failed to update');
      return;
    }
    toast.success('Field updated!');
    setShowEditor(false);
    setEditingField(null);
    fetchFields();
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this custom field? This will not remove existing data.')) return;
    const token = sessionStorage.getItem('session_token');
    const res = await fetch(`${API_URL}/admin/custom-field-definitions/${id}`, {
      method: 'DELETE',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (res.ok) {
      toast.success('Field deleted');
      fetchFields();
    } else {
      toast.error('Failed to delete');
    }
  };

  const handleToggleActive = async (field) => {
    const token = sessionStorage.getItem('session_token');
    await fetch(`${API_URL}/admin/custom-field-definitions/${field.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ is_active: !field.is_active }),
    });
    fetchFields();
  };

  const groupedByCategory = fields.reduce((acc, f) => {
    const cat = f.category || 'other';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(f);
    return acc;
  }, {});

  return (
    <div data-testid="custom-fields-builder">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
            <Settings2 className="w-5 h-5" /> Custom Fields
          </h2>
          <p className="text-xs text-slate-500 mt-1">Define custom data fields for people records</p>
        </div>
        <Button
          className="bg-slate-900 text-white hover:bg-slate-800"
          onClick={() => { setEditingField(null); setShowEditor(true); }}
          data-testid="add-custom-field-btn"
        >
          <Plus className="w-4 h-4 mr-1" /> Add Field
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
        </div>
      ) : fields.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl" data-testid="no-custom-fields">
          <Settings2 className="w-10 h-10 text-slate-200 mx-auto mb-3" />
          <p className="text-slate-500 text-sm">No custom fields defined yet</p>
          <p className="text-slate-400 text-xs mt-1">Add fields like "Shirt Size", "Allergies", or "Spiritual Gifts"</p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedByCategory).map(([cat, catFields]) => (
            <div key={cat}>
              <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">
                {CATEGORIES.find(c => c.value === cat)?.label || cat}
              </h3>
              <div className="space-y-2">
                {catFields.map((f) => (
                  <div
                    key={f.id}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg border transition-all ${f.is_active ? 'bg-white border-slate-200' : 'bg-slate-50 border-slate-100 opacity-60'}`}
                    data-testid={`custom-field-${f.id}`}
                  >
                    <GripVertical className="w-4 h-4 text-slate-300 cursor-grab flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm text-slate-800">{f.name}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${TYPE_COLORS[f.field_type] || 'bg-slate-100 text-slate-600'}`}>
                          {FIELD_TYPES.find(t => t.value === f.field_type)?.label || f.field_type}
                        </span>
                        {f.required && <span className="text-[10px] text-red-500 font-medium">Required</span>}
                      </div>
                      {f.options?.length > 0 && (
                        <p className="text-[11px] text-slate-400 mt-0.5 truncate">
                          Options: {f.options.join(', ')}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <button
                        onClick={() => handleToggleActive(f)}
                        className="p-1.5 hover:bg-slate-100 rounded"
                        title={f.is_active ? 'Disable' : 'Enable'}
                        data-testid={`toggle-field-${f.id}`}
                      >
                        {f.is_active
                          ? <ToggleRight className="w-4 h-4 text-emerald-500" />
                          : <ToggleLeft className="w-4 h-4 text-slate-400" />
                        }
                      </button>
                      <button
                        onClick={() => { setEditingField(f); setShowEditor(true); }}
                        className="p-1.5 hover:bg-slate-100 rounded"
                        data-testid={`edit-field-${f.id}`}
                      >
                        <Pencil className="w-3.5 h-3.5 text-slate-400" />
                      </button>
                      <button
                        onClick={() => handleDelete(f.id)}
                        className="p-1.5 hover:bg-red-50 rounded"
                        data-testid={`delete-field-${f.id}`}
                      >
                        <Trash2 className="w-3.5 h-3.5 text-red-400" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {showEditor && (
        <FieldEditor
          field={editingField}
          onSave={editingField ? handleUpdate : handleCreate}
          onClose={() => { setShowEditor(false); setEditingField(null); }}
        />
      )}
    </div>
  );
}
