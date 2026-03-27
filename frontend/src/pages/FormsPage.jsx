import { useState, useEffect } from 'react';
import {
  FileText, Plus, Trash2, Edit, Eye, Copy, ExternalLink,
  Loader2, GripVertical, ToggleLeft, ToggleRight, ChevronDown
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '@/components/ui/dialog';

const FIELD_TYPES = [
  { value: 'text', label: 'Text' },
  { value: 'email', label: 'Email' },
  { value: 'tel', label: 'Phone' },
  { value: 'number', label: 'Number' },
  { value: 'textarea', label: 'Long Text' },
  { value: 'select', label: 'Dropdown' },
  { value: 'checkbox', label: 'Checkbox' },
  { value: 'date', label: 'Date' },
  { value: 'url', label: 'Website' },
];

export default function FormsPage() {
  const [forms, setForms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showBuilder, setShowBuilder] = useState(false);
  const [editing, setEditing] = useState(null);
  const [showSubmissions, setShowSubmissions] = useState(null);
  const [submissions, setSubmissions] = useState([]);
  const [formData, setFormData] = useState({
    name: '', description: '', is_public: true, auto_create_profile: false,
    fields: [
      { id: 'f1', type: 'text', label: 'First Name', required: true, options: [] },
      { id: 'f2', type: 'text', label: 'Last Name', required: true, options: [] },
      { id: 'f3', type: 'email', label: 'Email', required: true, options: [] },
    ]
  });

  const fetchForms = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/forms`);
      if (res.ok) { const d = await res.json(); setForms(d.forms || []); }
    } catch {} finally { setLoading(false); }
  };

  useEffect(() => { fetchForms(); }, []);

  const saveForm = async () => {
    if (!formData.name) { toast.error('Form name is required'); return; }
    const url = editing ? `${API_URL}/admin/forms/${editing}` : `${API_URL}/admin/forms`;
    try {
      const res = await fetch(url, {
        method: editing ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        toast.success(editing ? 'Form updated' : 'Form created');
        setShowBuilder(false);
        setEditing(null);
        resetForm();
        fetchForms();
      }
    } catch { toast.error('Failed to save'); }
  };

  const deleteForm = async (id) => {
    if (!confirm('Delete this form?')) return;
    try {
      await fetch(`${API_URL}/admin/forms/${id}`, { method: 'DELETE' });
      toast.success('Form deleted');
      fetchForms();
    } catch { toast.error('Failed to delete'); }
  };

  const loadSubmissions = async (formId) => {
    try {
      const res = await fetch(`${API_URL}/admin/forms/${formId}/submissions`);
      if (res.ok) {
        const d = await res.json();
        setSubmissions(d.submissions || []);
        setShowSubmissions(formId);
      }
    } catch {}
  };

  const resetForm = () => {
    setFormData({
      name: '', description: '', is_public: true, auto_create_profile: false,
      fields: [
        { id: 'f1', type: 'text', label: 'First Name', required: true, options: [] },
        { id: 'f2', type: 'text', label: 'Last Name', required: true, options: [] },
        { id: 'f3', type: 'email', label: 'Email', required: true, options: [] },
      ]
    });
  };

  const openEdit = (form) => {
    setFormData({
      name: form.name, description: form.description || '',
      is_public: form.is_public, auto_create_profile: form.auto_create_profile || false,
      fields: form.fields || []
    });
    setEditing(form.id);
    setShowBuilder(true);
  };

  const addField = () => {
    setFormData({
      ...formData,
      fields: [...formData.fields, { id: `f${Date.now()}`, type: 'text', label: '', required: false, options: [] }]
    });
  };

  const removeField = (idx) => {
    setFormData({ ...formData, fields: formData.fields.filter((_, i) => i !== idx) });
  };

  const updateField = (idx, key, value) => {
    const fields = [...formData.fields];
    fields[idx] = { ...fields[idx], [key]: value };
    setFormData({ ...formData, fields });
  };

  const copyFormUrl = (formId) => {
    const url = `${window.location.origin}/forms/${formId}`;
    navigator.clipboard.writeText(url);
    toast.success('Public form URL copied to clipboard');
  };

  return (
    <div className="page-container" data-testid="forms-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>Forms</h1>
          <p style={{ fontSize: 14, color: '#64748b', marginTop: 4 }}>
            Create custom forms to collect information from visitors and members
          </p>
        </div>
        <Button onClick={() => { resetForm(); setEditing(null); setShowBuilder(true); }} data-testid="new-form-btn">
          <Plus className="w-4 h-4 mr-2" /> New Form
        </Button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}><Loader2 className="w-6 h-6 animate-spin" style={{ margin: '0 auto', color: '#64748b' }} /></div>
      ) : forms.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>
          <FileText className="w-10 h-10" style={{ margin: '0 auto 12px' }} />
          <p style={{ fontSize: 15, fontWeight: 600 }}>No forms yet</p>
          <p style={{ fontSize: 13, marginTop: 4 }}>Create your first form to start collecting data</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 16 }}>
          {forms.map(form => (
            <div key={form.id} data-testid={`form-${form.id}`}
              style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 14, padding: '20px 24px' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
                <div>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: '#0f172a', marginBottom: 4 }}>{form.name}</h3>
                  {form.description && <p style={{ fontSize: 13, color: '#64748b' }}>{form.description}</p>}
                </div>
                <span style={{
                  fontSize: 11, fontWeight: 600, padding: '2px 10px', borderRadius: 100,
                  background: form.is_active ? '#dcfce7' : '#fee2e2',
                  color: form.is_active ? '#166534' : '#991b1b'
                }}>
                  {form.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 12, fontSize: 12, color: '#94a3b8', marginBottom: 12 }}>
                <span>{(form.fields || []).length} fields</span>
                <span>{form.submission_count || 0} submissions</span>
                {form.auto_create_profile && <span style={{ color: '#3b82f6' }}>Auto-creates profiles</span>}
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                <Button size="sm" variant="outline" onClick={() => copyFormUrl(form.id)} title="Copy public URL">
                  <Copy className="w-3.5 h-3.5" />
                </Button>
                <Button size="sm" variant="outline" onClick={() => loadSubmissions(form.id)} title="View submissions">
                  <Eye className="w-3.5 h-3.5" />
                </Button>
                <Button size="sm" variant="outline" onClick={() => openEdit(form)} title="Edit form">
                  <Edit className="w-3.5 h-3.5" />
                </Button>
                <Button size="sm" variant="outline" onClick={() => deleteForm(form.id)} title="Delete" className="text-red-500 hover:text-red-700">
                  <Trash2 className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Form Builder Dialog */}
      <Dialog open={showBuilder} onOpenChange={setShowBuilder}>
        <DialogContent className="sm:max-w-[600px]" style={{ maxHeight: '85vh', overflowY: 'auto' }}>
          <DialogHeader>
            <DialogTitle>{editing ? 'Edit Form' : 'New Form'}</DialogTitle>
            <DialogDescription>Design your form fields and settings</DialogDescription>
          </DialogHeader>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 8 }}>
            <div>
              <label className="form-label">Form Name *</label>
              <input className="form-input" value={formData.name} data-testid="form-name-input"
                onChange={e => setFormData({ ...formData, name: e.target.value })} placeholder="Visitor Connect Card" />
            </div>
            <div>
              <label className="form-label">Description</label>
              <textarea className="form-input" rows={2} value={formData.description}
                onChange={e => setFormData({ ...formData, description: e.target.value })} placeholder="What is this form for?" />
            </div>

            <div style={{ display: 'flex', gap: 16 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <input type="checkbox" checked={formData.is_public}
                  onChange={e => setFormData({ ...formData, is_public: e.target.checked })}
                  style={{ width: 16, height: 16, accentColor: '#0f172a' }} />
                <span style={{ fontSize: 13, color: '#374151' }}>Public form</span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <input type="checkbox" checked={formData.auto_create_profile}
                  onChange={e => setFormData({ ...formData, auto_create_profile: e.target.checked })}
                  style={{ width: 16, height: 16, accentColor: '#0f172a' }} />
                <span style={{ fontSize: 13, color: '#374151' }}>Auto-create member profiles</span>
              </label>
            </div>

            <div>
              <label className="form-label" style={{ marginBottom: 10 }}>Fields</label>
              {formData.fields.map((field, idx) => (
                <div key={field.id} style={{ display: 'flex', gap: 8, marginBottom: 8, padding: 10, background: '#f8fafc', borderRadius: 8, border: '1px solid #e5e7eb', alignItems: 'center' }}>
                  <GripVertical className="w-4 h-4" style={{ color: '#d1d5db', flexShrink: 0 }} />
                  <select className="form-input" value={field.type} style={{ fontSize: 13, width: 110 }}
                    onChange={e => updateField(idx, 'type', e.target.value)}>
                    {FIELD_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                  <input className="form-input" value={field.label} placeholder="Field label"
                    onChange={e => updateField(idx, 'label', e.target.value)} style={{ fontSize: 13, flex: 1 }} />
                  <label style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer', whiteSpace: 'nowrap' }}>
                    <input type="checkbox" checked={field.required}
                      onChange={e => updateField(idx, 'required', e.target.checked)}
                      style={{ width: 14, height: 14, accentColor: '#0f172a' }} />
                    <span style={{ fontSize: 11, color: '#64748b' }}>Required</span>
                  </label>
                  <button onClick={() => removeField(idx)} style={{ padding: 4, color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer' }}>
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
              <button onClick={addField} data-testid="add-field-btn"
                style={{ width: '100%', padding: 10, border: '2px dashed #d1d5db', borderRadius: 8, background: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600, color: '#64748b', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                <Plus className="w-4 h-4" /> Add Field
              </button>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 4 }}>
              <Button variant="outline" onClick={() => { setShowBuilder(false); setEditing(null); }}>Cancel</Button>
              <Button onClick={saveForm} data-testid="save-form-btn">
                {editing ? 'Update Form' : 'Create Form'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Submissions Dialog */}
      <Dialog open={!!showSubmissions} onOpenChange={() => setShowSubmissions(null)}>
        <DialogContent className="sm:max-w-[600px]" style={{ maxHeight: '85vh', overflowY: 'auto' }}>
          <DialogHeader>
            <DialogTitle>Form Submissions</DialogTitle>
          </DialogHeader>
          <div>
            {submissions.length === 0 ? (
              <p style={{ textAlign: 'center', color: '#94a3b8', padding: 32 }}>No submissions yet</p>
            ) : submissions.map(sub => (
              <div key={sub.id} style={{ padding: 14, border: '1px solid #e5e7eb', borderRadius: 10, marginBottom: 10 }}>
                <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 8 }}>{new Date(sub.submitted_at).toLocaleString()}</div>
                {Object.entries(sub.data || {}).map(([key, val]) => (
                  <div key={key} style={{ display: 'flex', gap: 8, fontSize: 13, marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, color: '#374151', minWidth: 100 }}>{key}:</span>
                    <span style={{ color: '#64748b' }}>{String(val)}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
