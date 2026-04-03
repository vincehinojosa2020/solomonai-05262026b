import { useState, useEffect } from 'react';
import {
  ListFilter, Plus, Trash2, Play, Loader2, Users, ChevronRight
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '@/components/ui/dialog';

const FILTER_FIELDS = [
  { value: 'membership_status', label: 'Membership Status' },
  { value: 'role', label: 'Role' },
  { value: 'name', label: 'Name' },
  { value: 'email', label: 'Email' },
  { value: 'phone', label: 'Phone' },
  { value: 'city', label: 'City' },
  { value: 'state', label: 'State' },
  { value: 'gender', label: 'Gender' },
  { value: 'source', label: 'Source' },
];

const OPERATORS = [
  { value: 'equals', label: 'equals' },
  { value: 'not_equals', label: 'does not equal' },
  { value: 'contains', label: 'contains' },
  { value: 'exists', label: 'has any value' },
  { value: 'not_exists', label: 'is empty' },
];

export default function SmartListsPage() {
  const [lists, setLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showBuilder, setShowBuilder] = useState(false);
  const [showResults, setShowResults] = useState(null);
  const [results, setResults] = useState([]);
  const [resultCount, setResultCount] = useState(0);
  const [running, setRunning] = useState(null);
  const [formData, setFormData] = useState({
    name: '', description: '',
    rules: [{ field: 'membership_status', operator: 'equals', value: 'active' }]
  });

  const fetchLists = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/smart-lists`);
      if (res.ok) { const d = await res.json(); setLists(d.lists || []); }
    } catch {} finally { setLoading(false); }
  };

  useEffect(() => { fetchLists(); }, []);

  const createList = async () => {
    if (!formData.name) { toast.error('List name is required'); return; }
    try {
      const res = await fetch(`${API_URL}/admin/smart-lists`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        toast.success('Smart list created');
        setShowBuilder(false);
        setFormData({ name: '', description: '', rules: [{ field: 'membership_status', operator: 'equals', value: 'active' }] });
        fetchLists();
      }
    } catch { toast.error('Failed to create'); }
  };

  const runList = async (listId) => {
    setRunning(listId);
    try {
      const res = await fetch(`${API_URL}/admin/smart-lists/${listId}/run`, { method: 'POST' });
      if (res.ok) {
        const d = await res.json();
        setResults(d.members || []);
        setResultCount(d.count || 0);
        setShowResults(listId);
      }
    } catch { toast.error('Failed to run list'); }
    finally { setRunning(null); }
  };

  const addRule = () => {
    setFormData({
      ...formData,
      rules: [...formData.rules, { field: 'membership_status', operator: 'equals', value: '' }]
    });
  };

  const removeRule = (idx) => {
    setFormData({ ...formData, rules: formData.rules.filter((_, i) => i !== idx) });
  };

  const updateRule = (idx, key, value) => {
    const rules = [...formData.rules];
    rules[idx] = { ...rules[idx], [key]: value };
    setFormData({ ...formData, rules });
  };

  return (
    <div className="page-container" data-testid="smart-lists-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>Smart Lists</h1>
          <p style={{ fontSize: 14, color: '#64748b', marginTop: 4 }}>
            Create rule-based lists that automatically update as your data changes
          </p>
        </div>
        <Button onClick={() => setShowBuilder(true)} data-testid="new-smart-list-btn">
          <Plus className="w-4 h-4 mr-2" /> New Smart List
        </Button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}><Loader2 className="w-6 h-6 animate-spin" style={{ margin: '0 auto', color: '#64748b' }} /></div>
      ) : lists.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>
          <ListFilter className="w-10 h-10" style={{ margin: '0 auto 12px' }} />
          <p style={{ fontSize: 15, fontWeight: 600 }}>No smart lists yet</p>
          <p style={{ fontSize: 13, marginTop: 4 }}>Create rule-based lists to segment your members</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {lists.map(list => (
            <div key={list.id} data-testid={`smart-list-${list.id}`}
              style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 14, padding: '18px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 700, color: '#0f172a', marginBottom: 4 }}>{list.name}</h3>
                {list.description && <p style={{ fontSize: 13, color: '#64748b', marginBottom: 6 }}>{list.description}</p>}
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {(list.rules || []).map((rule, i) => (
                    <span key={i} style={{ fontSize: 11, padding: '3px 10px', background: '#f1f5f9', borderRadius: 6, color: '#475569', fontWeight: 500 }}>
                      {FILTER_FIELDS.find(f => f.value === rule.field)?.label || rule.field} {rule.operator} {rule.value || ''}
                    </span>
                  ))}
                </div>
              </div>
              <Button size="sm" onClick={() => runList(list.id)} disabled={running === list.id} data-testid={`run-list-${list.id}`}>
                {running === list.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <><Play className="w-3.5 h-3.5 mr-1" /> Run</>}
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Builder Dialog */}
      <Dialog open={showBuilder} onOpenChange={setShowBuilder}>
        <DialogContent className="sm:max-w-[560px]">
          <DialogHeader>
            <DialogTitle>New Smart List</DialogTitle>
            <DialogDescription>Define filter rules to automatically segment your members</DialogDescription>
          </DialogHeader>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 8 }}>
            <div>
              <label className="form-label">List Name *</label>
              <input className="form-input" value={formData.name} data-testid="sl-name"
                onChange={e => setFormData({ ...formData, name: e.target.value })} placeholder="Active Members in Charlotte" />
            </div>
            <div>
              <label className="form-label">Description</label>
              <input className="form-input" value={formData.description}
                onChange={e => setFormData({ ...formData, description: e.target.value })} placeholder="Optional description" />
            </div>
            <div>
              <label className="form-label" style={{ marginBottom: 10 }}>Filter Rules</label>
              {formData.rules.map((rule, idx) => (
                <div key={`filter-${idx}`} style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'center' }}>
                  {idx > 0 && <span style={{ fontSize: 11, fontWeight: 700, color: '#3b82f6', width: 30 }}>AND</span>}
                  {idx === 0 && <span style={{ width: 30 }} />}
                  <select className="form-input" value={rule.field} style={{ fontSize: 13, flex: 1 }}
                    onChange={e => updateRule(idx, 'field', e.target.value)}>
                    {FILTER_FIELDS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
                  </select>
                  <select className="form-input" value={rule.operator} style={{ fontSize: 13, flex: 1 }}
                    onChange={e => updateRule(idx, 'operator', e.target.value)}>
                    {OPERATORS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                  {!['exists', 'not_exists'].includes(rule.operator) && (
                    <input className="form-input" value={rule.value} placeholder="Value"
                      onChange={e => updateRule(idx, 'value', e.target.value)} style={{ fontSize: 13, flex: 1 }} />
                  )}
                  {formData.rules.length > 1 && (
                    <button onClick={() => removeRule(idx)} style={{ padding: 4, color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer' }}>
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
              <button onClick={addRule} data-testid="add-rule-btn"
                style={{ width: '100%', padding: 8, border: '2px dashed #d1d5db', borderRadius: 8, background: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 600, color: '#64748b' }}>
                <Plus className="w-3 h-3 inline mr-1" /> Add Rule
              </button>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 4 }}>
              <Button variant="outline" onClick={() => setShowBuilder(false)}>Cancel</Button>
              <Button onClick={createList} data-testid="save-smart-list-btn">Create List</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Results Dialog */}
      <Dialog open={!!showResults} onOpenChange={() => setShowResults(null)}>
        <DialogContent className="sm:max-w-[500px]" style={{ maxHeight: '85vh', overflowY: 'auto' }}>
          <DialogHeader>
            <DialogTitle>List Results ({resultCount} members)</DialogTitle>
          </DialogHeader>
          <div>
            {results.length === 0 ? (
              <p style={{ textAlign: 'center', color: '#94a3b8', padding: 32 }}>No members match these criteria</p>
            ) : results.map(m => (
              <div key={m.user_id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', borderBottom: '1px solid #f1f5f9' }}>
                <div style={{
                  width: 36, height: 36, borderRadius: '50%', background: '#f1f5f9',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 13, fontWeight: 700, color: '#64748b'
                }}>
                  {(m.name || '?').charAt(0)}
                </div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: 14, fontWeight: 600, color: '#0f172a' }}>{m.name}</p>
                  <p style={{ fontSize: 12, color: '#94a3b8' }}>{m.email}</p>
                </div>
                <span style={{ fontSize: 11, padding: '2px 8px', background: '#f1f5f9', borderRadius: 4, color: '#64748b' }}>
                  {m.membership_status || 'unknown'}
                </span>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
