import { useState, useEffect } from 'react';
import {
  GitBranch, Plus, Trash2, Edit, Users, Play, Pause,
  ChevronRight, Loader2, CheckCircle, Clock, Mail, Phone, UserPlus, ArrowRight
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from '@/components/ui/dialog';

const STEP_TYPES = [
  { value: 'email', label: 'Send Email', icon: Mail, color: '#3b82f6' },
  { value: 'task', label: 'Assign Task', icon: CheckCircle, color: '#22c55e' },
  { value: 'call', label: 'Phone Call', icon: Phone, color: '#f59e0b' },
  { value: 'add_to_group', label: 'Add to Group', icon: UserPlus, color: '#8b5cf6' },
  { value: 'wait', label: 'Wait Period', icon: Clock, color: '#94a3b8' },
];

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showBuilder, setShowBuilder] = useState(false);
  const [editing, setEditing] = useState(null);
  const [showEnrollments, setShowEnrollments] = useState(null);
  const [enrollments, setEnrollments] = useState([]);
  const [wfForm, setWfForm] = useState({
    name: '', description: '', trigger: 'manual',
    steps: [{ id: 's1', order: 1, type: 'email', title: 'Send Welcome Email', description: '', assignee: '', due_days: 1 }]
  });

  const fetchWorkflows = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/workflows`);
      if (res.ok) { const d = await res.json(); setWorkflows(d.workflows || []); }
    } catch {} finally { setLoading(false); }
  };

  useEffect(() => { fetchWorkflows(); }, []);

  const saveWorkflow = async () => {
    if (!wfForm.name) { toast.error('Name is required'); return; }
    const url = editing
      ? `${API_URL}/admin/workflows/${editing}`
      : `${API_URL}/admin/workflows`;
    try {
      const res = await fetch(url, {
        method: editing ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(wfForm)
      });
      if (res.ok) {
        toast.success(editing ? 'Workflow updated' : 'Workflow created');
        setShowBuilder(false);
        setEditing(null);
        resetForm();
        fetchWorkflows();
      }
    } catch { toast.error('Failed to save'); }
  };

  const deleteWorkflow = async (id) => {
    if (!confirm('Delete this workflow?')) return;
    try {
      await fetch(`${API_URL}/admin/workflows/${id}`, { method: 'DELETE' });
      toast.success('Workflow deleted');
      fetchWorkflows();
    } catch { toast.error('Failed to delete'); }
  };

  const loadEnrollments = async (wfId) => {
    try {
      const res = await fetch(`${API_URL}/admin/workflows/${wfId}/enrollments`);
      if (res.ok) {
        const d = await res.json();
        setEnrollments(d.enrollments || []);
        setShowEnrollments(wfId);
      }
    } catch {}
  };

  const resetForm = () => {
    setWfForm({
      name: '', description: '', trigger: 'manual',
      steps: [{ id: 's1', order: 1, type: 'email', title: 'Send Welcome Email', description: '', assignee: '', due_days: 1 }]
    });
  };

  const openEdit = (wf) => {
    setWfForm({ name: wf.name, description: wf.description || '', trigger: wf.trigger || 'manual', steps: wf.steps || [] });
    setEditing(wf.id);
    setShowBuilder(true);
  };

  const addStep = () => {
    const order = wfForm.steps.length + 1;
    setWfForm({
      ...wfForm,
      steps: [...wfForm.steps, { id: `s${Date.now()}`, order, type: 'task', title: '', description: '', assignee: '', due_days: 3 }]
    });
  };

  const removeStep = (idx) => {
    const steps = wfForm.steps.filter((_, i) => i !== idx).map((s, i) => ({ ...s, order: i + 1 }));
    setWfForm({ ...wfForm, steps });
  };

  const updateStep = (idx, field, value) => {
    const steps = [...wfForm.steps];
    steps[idx] = { ...steps[idx], [field]: value };
    setWfForm({ ...wfForm, steps });
  };

  return (
    <div className="page-container" data-testid="workflows-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>Workflows</h1>
          <p style={{ fontSize: 14, color: '#64748b', marginTop: 4 }}>
            Automate multi-step follow-up processes for your church
          </p>
        </div>
        <Button onClick={() => { resetForm(); setEditing(null); setShowBuilder(true); }} data-testid="new-workflow-btn">
          <Plus className="w-4 h-4 mr-2" /> New Workflow
        </Button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}><Loader2 className="w-6 h-6 animate-spin" style={{ margin: '0 auto', color: '#64748b' }} /></div>
      ) : workflows.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>
          <GitBranch className="w-10 h-10" style={{ margin: '0 auto 12px' }} />
          <p style={{ fontSize: 15, fontWeight: 600 }}>No workflows yet</p>
          <p style={{ fontSize: 13, marginTop: 4 }}>Create your first workflow to automate follow-up processes</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {workflows.map(wf => (
            <div key={wf.id} data-testid={`workflow-${wf.id}`}
              style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 14, padding: '20px 24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                    <GitBranch className="w-4 h-4" style={{ color: '#3b82f6' }} />
                    <h3 style={{ fontSize: 16, fontWeight: 700, color: '#0f172a' }}>{wf.name}</h3>
                    <span style={{
                      fontSize: 11, fontWeight: 600, padding: '2px 10px', borderRadius: 100,
                      background: wf.is_active ? '#dcfce7' : '#f1f5f9', color: wf.is_active ? '#166534' : '#64748b'
                    }}>
                      {wf.is_active ? 'Active' : 'Paused'}
                    </span>
                  </div>
                  {wf.description && <p style={{ fontSize: 13, color: '#64748b', marginBottom: 8 }}>{wf.description}</p>}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
                    {(wf.steps || []).map((step, i) => {
                      const stepType = STEP_TYPES.find(t => t.value === step.type) || STEP_TYPES[1];
                      const StepIcon = stepType.icon;
                      return (
                        <div key={step.id} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                          <div style={{
                            display: 'flex', alignItems: 'center', gap: 6, padding: '4px 10px',
                            background: '#f8fafc', border: '1px solid #e5e7eb', borderRadius: 8, fontSize: 12, color: '#374151'
                          }}>
                            <StepIcon className="w-3 h-3" style={{ color: stepType.color }} />
                            <span style={{ fontWeight: 500 }}>{step.title || stepType.label}</span>
                          </div>
                          {i < (wf.steps || []).length - 1 && <ArrowRight className="w-3 h-3" style={{ color: '#d1d5db' }} />}
                        </div>
                      );
                    })}
                  </div>
                  <div style={{ display: 'flex', gap: 16, marginTop: 10, fontSize: 12, color: '#94a3b8' }}>
                    <span>{(wf.steps || []).length} steps</span>
                    <span>{wf.enrolled_count || 0} enrolled</span>
                    <span>{wf.completed_count || 0} completed</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                  <Button size="sm" variant="outline" onClick={() => loadEnrollments(wf.id)}>
                    <Users className="w-3.5 h-3.5" />
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => openEdit(wf)}>
                    <Edit className="w-3.5 h-3.5" />
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => deleteWorkflow(wf.id)} className="text-red-500 hover:text-red-700">
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Workflow Builder Dialog */}
      <Dialog open={showBuilder} onOpenChange={setShowBuilder}>
        <DialogContent className="sm:max-w-[600px]" style={{ maxHeight: '85vh', overflowY: 'auto' }}>
          <DialogHeader>
            <DialogTitle>{editing ? 'Edit Workflow' : 'New Workflow'}</DialogTitle>
            <DialogDescription>Define the steps for your automated follow-up process</DialogDescription>
          </DialogHeader>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 8 }}>
            <div>
              <label className="form-label">Workflow Name *</label>
              <input className="form-input" value={wfForm.name} data-testid="wf-name"
                onChange={e => setWfForm({ ...wfForm, name: e.target.value })} placeholder="New Visitor Follow-up" />
            </div>
            <div>
              <label className="form-label">Description</label>
              <textarea className="form-input" rows={2} value={wfForm.description}
                onChange={e => setWfForm({ ...wfForm, description: e.target.value })} placeholder="Describe the workflow..." />
            </div>
            <div>
              <label className="form-label">Trigger</label>
              <select className="form-input" value={wfForm.trigger}
                onChange={e => setWfForm({ ...wfForm, trigger: e.target.value })}>
                <option value="manual">Manual enrollment</option>
                <option value="new_visitor">New visitor added</option>
                <option value="form_submission">Form submission</option>
                <option value="first_donation">First donation</option>
              </select>
            </div>

            <div>
              <label className="form-label" style={{ marginBottom: 10 }}>Steps</label>
              {wfForm.steps.map((step, idx) => (
                <div key={step.id} style={{ display: 'flex', gap: 8, marginBottom: 10, padding: 12, background: '#f8fafc', borderRadius: 10, border: '1px solid #e5e7eb' }}>
                  <div style={{ width: 24, height: 24, borderRadius: '50%', background: '#0f172a', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, flexShrink: 0, marginTop: 2 }}>
                    {idx + 1}
                  </div>
                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                      <select className="form-input" value={step.type}
                        onChange={e => updateStep(idx, 'type', e.target.value)} style={{ fontSize: 13 }}>
                        {STEP_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                      </select>
                      <input className="form-input" value={step.title} placeholder="Step title"
                        onChange={e => updateStep(idx, 'title', e.target.value)} style={{ fontSize: 13 }} />
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                      <input className="form-input" value={step.assignee || ''} placeholder="Assignee (optional)"
                        onChange={e => updateStep(idx, 'assignee', e.target.value)} style={{ fontSize: 13 }} />
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontSize: 12, color: '#64748b', whiteSpace: 'nowrap' }}>Due in</span>
                        <input className="form-input" type="number" min="1" value={step.due_days || 1}
                          onChange={e => updateStep(idx, 'due_days', parseInt(e.target.value) || 1)} style={{ fontSize: 13, width: 60 }} />
                        <span style={{ fontSize: 12, color: '#64748b' }}>days</span>
                      </div>
                    </div>
                  </div>
                  {wfForm.steps.length > 1 && (
                    <button onClick={() => removeStep(idx)} style={{ padding: 4, color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer', flexShrink: 0 }}>
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
              <button onClick={addStep} data-testid="add-step-btn"
                style={{ width: '100%', padding: '10px', border: '2px dashed #d1d5db', borderRadius: 10, background: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600, color: '#64748b', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                <Plus className="w-4 h-4" /> Add Step
              </button>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 4 }}>
              <Button variant="outline" onClick={() => { setShowBuilder(false); setEditing(null); }}>Cancel</Button>
              <Button onClick={saveWorkflow} data-testid="save-workflow-btn">
                {editing ? 'Update Workflow' : 'Create Workflow'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Enrollments Dialog */}
      <Dialog open={!!showEnrollments} onOpenChange={() => setShowEnrollments(null)}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Workflow Enrollments</DialogTitle>
          </DialogHeader>
          <div style={{ maxHeight: 400, overflowY: 'auto' }}>
            {enrollments.length === 0 ? (
              <p style={{ textAlign: 'center', color: '#94a3b8', padding: 32 }}>No enrollments yet</p>
            ) : enrollments.map(e => (
              <div key={e.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', borderBottom: '1px solid #f1f5f9' }}>
                <div style={{ width: 36, height: 36, borderRadius: '50%', background: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, color: '#64748b' }}>
                  {(e.person_name || '?').charAt(0)}
                </div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: 14, fontWeight: 600, color: '#0f172a' }}>{e.person_name || 'Unknown'}</p>
                  <p style={{ fontSize: 12, color: '#94a3b8' }}>{e.person_email}</p>
                </div>
                <span style={{
                  fontSize: 11, fontWeight: 600, padding: '2px 10px', borderRadius: 100,
                  background: e.status === 'active' ? '#dcfce7' : '#f1f5f9',
                  color: e.status === 'active' ? '#166534' : '#64748b'
                }}>
                  Step {e.current_step + 1}
                </span>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
