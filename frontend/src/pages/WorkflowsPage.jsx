import { useState, useEffect } from 'react';
import {
  GitBranch, Plus, Trash2, Edit2, Play, Pause, Users, ChevronRight,
  Loader2, CheckCircle, Clock, Mail, Phone, UserPlus, ArrowRight,
  Zap, MessageSquare, Bell, Tag, FileText, Filter, AlertTriangle,
  Calendar, Heart, X, Save, Settings, Activity, ToggleLeft, ToggleRight
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { FeatureEducationHeader } from '@/components/FeatureEducationHeader';

const TRIGGERS = [
  { value: 'new_member', label: 'New Member Added', icon: UserPlus, color: '#059669', desc: 'Fires when a new person is created' },
  { value: 'first_visit', label: 'First-Time Visitor Check-In', icon: CheckCircle, color: '#2563eb', desc: 'Fires after first check-in' },
  { value: 'first_donation', label: 'First Donation', icon: Heart, color: '#dc2626', desc: 'Fires after first gift' },
  { value: 'missed_attendance', label: 'Missed Attendance (3+ weeks)', icon: Calendar, color: '#f59e0b', desc: 'Fires after 3 consecutive missed Sundays' },
  { value: 'group_join', label: 'Group Join', icon: Users, color: '#7c3aed', desc: 'Fires when someone joins a group' },
  { value: 'group_leave', label: 'Group Leave', icon: Users, color: '#6b7280', desc: 'Fires when someone leaves a group' },
  { value: 'event_registration', label: 'Event Registration', icon: Calendar, color: '#0891b2', desc: 'Fires on event sign-up' },
  { value: 'birthday', label: 'Birthday (7 days before)', icon: Heart, color: '#ec4899', desc: 'Fires 7 days before birthday' },
  { value: 'giving_milestone', label: 'Giving Milestone', icon: Heart, color: '#059669', desc: 'Fires at $1K, $5K, $10K lifetime' },
  { value: 'lapsed_donor', label: 'Lapsed Donor (90 days)', icon: AlertTriangle, color: '#f59e0b', desc: 'Gave before, silent 90+ days' },
  { value: 'membership_change', label: 'Membership Status Change', icon: Tag, color: '#2563eb', desc: 'Fires when status is updated' },
  { value: 'manual', label: 'Manual Trigger', icon: Zap, color: '#64748b', desc: 'Run manually or via API' },
];

const ACTIONS = [
  { value: 'send_email', label: 'Send Email', icon: Mail, color: '#2563eb', desc: 'Send from a saved template' },
  { value: 'send_sms', label: 'Send SMS', icon: MessageSquare, color: '#7c3aed', desc: 'Send via Twilio' },
  { value: 'push_notification', label: 'Push Notification', icon: Bell, color: '#0891b2', desc: 'Send mobile push' },
  { value: 'assign_task', label: 'Assign Task to Staff', icon: CheckCircle, color: '#059669', desc: 'Create a follow-up task' },
  { value: 'add_to_group', label: 'Add to Group', icon: UserPlus, color: '#7c3aed', desc: 'Auto-enroll in a group' },
  { value: 'remove_from_group', label: 'Remove from Group', icon: Users, color: '#6b7280', desc: 'Remove from a group' },
  { value: 'update_field', label: 'Update Custom Field', icon: Settings, color: '#f59e0b', desc: 'Change a person field value' },
  { value: 'add_note', label: 'Add Note', icon: FileText, color: '#64748b', desc: 'Add internal note to profile' },
  { value: 'add_tag', label: 'Add Tag', icon: Tag, color: '#ec4899', desc: 'Tag this person' },
];

const CONDITIONS = [
  { value: 'campus_is', label: 'Campus is', field: 'campus' },
  { value: 'status_is', label: 'Status is', field: 'membership_status' },
  { value: 'giving_tier', label: 'Giving tier is', field: 'giving_tier' },
  { value: 'age_above', label: 'Age is above', field: 'age' },
  { value: 'in_group', label: 'Is in group', field: 'group' },
  { value: 'giving_above', label: 'YTD giving above $', field: 'ytd_giving' },
];

const NODE_COLORS = {
  trigger: '#059669',
  action: '#2563eb',
  condition: '#d97706',
  delay: '#f59e0b',
  end: '#dc2626',
};

function NodeCard({ node, onDelete, onEdit }) {
  const isAction = ACTIONS.find(a => a.value === node.type);
  const isTrigger = TRIGGERS.find(t => t.value === node.type);
  const isCondition = node.nodeType === 'condition';
  const isDelay = node.nodeType === 'delay';
  const isEnd = node.nodeType === 'end';

  const color = isEnd ? '#dc2626' : isDelay ? '#f59e0b' : isCondition ? '#d97706' : isAction?.color || isTrigger?.color || '#64748b';
  const label = isEnd ? 'End' : isDelay ? `Wait ${node.days || 1} day(s)` : isCondition ? `If ${node.field} ${node.operator} "${node.value}"` : isAction?.label || isTrigger?.label || node.type;
  const Icon = isEnd ? X : isDelay ? Clock : isCondition ? Filter : isAction?.icon || isTrigger?.icon || Zap;
  const nodeType = isEnd ? 'End' : isDelay ? 'Delay' : isCondition ? 'Condition' : isAction ? 'Action' : 'Trigger';

  return (
    <div className="relative flex flex-col items-center" data-testid={`workflow-node-${node.id}`}>
      <div
        className="rounded-xl border-2 p-4 w-64 bg-white shadow-sm hover:shadow-md transition-shadow group"
        style={{ borderColor: color }}
      >
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${color}20` }}>
              <Icon className="w-4 h-4" style={{ color }} />
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color }}>{nodeType}</p>
              <p className="text-sm font-semibold text-slate-800 leading-tight">{label}</p>
            </div>
          </div>
          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {onEdit && <button onClick={() => onEdit(node)} className="p-1 text-slate-400 hover:text-blue-600"><Edit2 className="w-3 h-3" /></button>}
            {onDelete && <button onClick={() => onDelete(node.id)} className="p-1 text-slate-400 hover:text-red-500"><Trash2 className="w-3 h-3" /></button>}
          </div>
        </div>
        {node.description && <p className="text-xs text-slate-500">{node.description}</p>}
      </div>
    </div>
  );
}

function AddNodeButton({ onAdd }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="flex flex-col items-center">
      <div className="w-0.5 h-6 bg-slate-200" />
      {open ? (
        <div className="bg-white border border-slate-200 rounded-xl shadow-lg p-3 w-72 z-10">
          <div className="grid grid-cols-2 gap-1.5">
            {[
              { label: 'Action', type: 'action_select', color: '#2563eb', icon: Zap },
              { label: 'Condition', type: 'condition', color: '#d97706', icon: Filter },
              { label: 'Delay', type: 'delay', color: '#f59e0b', icon: Clock },
              { label: 'End', type: 'end', color: '#dc2626', icon: X },
            ].map(opt => (
              <button
                key={opt.type}
                onClick={() => { onAdd(opt.type); setOpen(false); }}
                className="flex items-center gap-2 p-2 border border-slate-200 rounded-lg hover:bg-slate-50 text-left"
              >
                <opt.icon className="w-4 h-4" style={{ color: opt.color }} />
                <span className="text-sm font-medium text-slate-700">{opt.label}</span>
              </button>
            ))}
          </div>
          <button onClick={() => setOpen(false)} className="w-full mt-2 text-xs text-slate-400 hover:text-slate-600">Cancel</button>
        </div>
      ) : (
        <button
          onClick={() => setOpen(true)}
          className="w-8 h-8 rounded-full border-2 border-dashed border-slate-300 hover:border-blue-400 flex items-center justify-center text-slate-400 hover:text-blue-500 transition-all"
          data-testid="add-node-btn"
        >
          <Plus className="w-4 h-4" />
        </button>
      )}
      <div className="w-0.5 h-6 bg-slate-200" />
    </div>
  );
}

const defaultWfForm = {
  name: '', description: '', trigger: 'new_member', is_active: false,
  nodes: [
    { id: 'trigger-1', nodeType: 'trigger', type: 'new_member', description: 'Fires when a new person is added' },
  ]
};

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showBuilder, setShowBuilder] = useState(false);
  const [editing, setEditing] = useState(null);
  const [wfForm, setWfForm] = useState(defaultWfForm);
  const [showActionPicker, setShowActionPicker] = useState(false);
  const [addingAfterIndex, setAddingAfterIndex] = useState(null);
  const [saving, setSaving] = useState(false);

  const token = sessionStorage.getItem('session_token');
  const headers = token ? { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };

  useEffect(() => { fetchWorkflows(); }, []);

  const fetchWorkflows = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/workflows`, { headers });
      if (res.ok) { const d = await res.json(); setWorkflows(d.workflows || []); }
    } catch {} finally { setLoading(false); }
  };

  const addNode = (type, afterIndex) => {
    const newNode = { id: `node-${Date.now()}`, nodeType: type };
    if (type === 'action_select') {
      // default to first action
      newNode.type = 'send_email';
      newNode.nodeType = 'action';
      newNode.description = 'Send welcome email from template';
    } else if (type === 'condition') {
      newNode.field = 'campus';
      newNode.operator = '=';
      newNode.value = '';
    } else if (type === 'delay') {
      newNode.days = 1;
    } else if (type === 'end') {
      // end node
    }
    const nodes = [...wfForm.nodes];
    nodes.splice(afterIndex + 1, 0, newNode);
    setWfForm(f => ({ ...f, nodes }));
  };

  const deleteNode = (id) => {
    if (wfForm.nodes.length <= 1) { toast.error('A workflow must have at least a trigger'); return; }
    setWfForm(f => ({ ...f, nodes: f.nodes.filter(n => n.id !== id) }));
  };

  const saveWorkflow = async () => {
    if (!wfForm.name) { toast.error('Workflow name is required'); return; }
    setSaving(true);
    try {
      const payload = {
        name: wfForm.name,
        description: wfForm.description,
        trigger: wfForm.trigger,
        is_active: wfForm.is_active,
        steps: wfForm.nodes.filter(n => n.nodeType === 'action').map((n, i) => ({
          id: n.id, order: i + 1, type: n.type, title: n.label || n.type, description: n.description || '', due_days: n.days || 1
        })),
        nodes: wfForm.nodes,
      };
      const url = editing ? `${API_URL}/admin/workflows/${editing}` : `${API_URL}/admin/workflows`;
      const res = await fetch(url, { method: editing ? 'PUT' : 'POST', headers, body: JSON.stringify(payload) });
      if (res.ok) {
        toast.success(editing ? 'Workflow updated!' : 'Workflow created and ready to run.');
        setShowBuilder(false); setEditing(null); setWfForm(defaultWfForm); fetchWorkflows();
      } else { toast.error('Failed to save workflow'); }
    } catch { toast.error('Error saving workflow'); } finally { setSaving(false); }
  };

  const toggleActive = async (wf) => {
    try {
      const res = await fetch(`${API_URL}/admin/workflows/${wf.id}`, {
        method: 'PUT', headers, body: JSON.stringify({ ...wf, is_active: !wf.is_active })
      });
      if (res.ok) { toast.success(wf.is_active ? 'Workflow paused' : 'Workflow activated'); fetchWorkflows(); }
    } catch { toast.error('Failed to update'); }
  };

  const openEdit = (wf) => {
    setEditing(wf.id);
    setWfForm({
      name: wf.name || '',
      description: wf.description || '',
      trigger: wf.trigger || 'manual',
      is_active: wf.is_active || false,
      nodes: wf.nodes?.length ? wf.nodes : [
        { id: 'trigger-1', nodeType: 'trigger', type: wf.trigger || 'manual', description: '' },
        ...( wf.steps || []).map(s => ({ id: s.id || `s-${s.order}`, nodeType: 'action', type: s.type, description: s.description || '' })),
      ],
    });
    setShowBuilder(true);
  };

  if (showBuilder) {
    const triggerNode = wfForm.nodes.find(n => n.nodeType === 'trigger') || wfForm.nodes[0];
    const otherNodes = wfForm.nodes.filter(n => n !== triggerNode);
    const allNodes = [triggerNode, ...otherNodes];

    return (
      <div className="animate-fade-in" data-testid="workflow-builder">
        {/* Builder Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <button onClick={() => { setShowBuilder(false); setEditing(null); setWfForm(defaultWfForm); }} className="text-sm text-blue-600 hover:underline flex items-center gap-1 mb-1">
              ← All Workflows
            </button>
            <input
              className="text-xl font-bold text-slate-900 border-none outline-none w-full bg-transparent"
              value={wfForm.name}
              onChange={e => setWfForm(f => ({...f, name: e.target.value}))}
              placeholder="Name this workflow..."
              data-testid="workflow-name-input"
            />
            <input
              className="text-sm text-slate-500 border-none outline-none w-full bg-transparent mt-0.5"
              value={wfForm.description}
              onChange={e => setWfForm(f => ({...f, description: e.target.value}))}
              placeholder="What does this workflow do? (optional)"
            />
          </div>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
              <input type="checkbox" checked={wfForm.is_active} onChange={e => setWfForm(f => ({...f, is_active: e.target.checked}))} className="rounded" />
              Active
            </label>
            <Button onClick={saveWorkflow} disabled={saving} className="btn-primary flex items-center gap-1.5" data-testid="save-workflow-btn">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              {saving ? 'Saving...' : 'Save Workflow'}
            </Button>
          </div>
        </div>

        {/* Visual Canvas */}
        <div className="bg-slate-50 rounded-2xl p-8 min-h-[500px] border border-slate-200">
          <div className="flex flex-col items-center gap-0">
            {allNodes.map((node, i) => (
              <div key={node.id} className="flex flex-col items-center">
                {i === 0 ? (
                  // Trigger — show selector
                  <div className="bg-white border-2 border-emerald-400 rounded-xl p-4 w-72 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                      <Zap className="w-4 h-4 text-emerald-600" />
                      <p className="text-[10px] font-semibold uppercase tracking-wider text-emerald-700">Trigger</p>
                    </div>
                    <select
                      value={wfForm.trigger}
                      onChange={e => { setWfForm(f => ({...f, trigger: e.target.value, nodes: [{...f.nodes[0], type: e.target.value}, ...f.nodes.slice(1)]})); }}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
                      data-testid="trigger-select"
                    >
                      {TRIGGERS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                    </select>
                    <p className="text-xs text-slate-500 mt-1">{TRIGGERS.find(t => t.value === wfForm.trigger)?.desc}</p>
                  </div>
                ) : node.nodeType === 'action' ? (
                  <div className="bg-white border-2 border-blue-400 rounded-xl p-4 w-72 shadow-sm group relative">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4 text-blue-600" />
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-blue-700">Action</p>
                      </div>
                      <button onClick={() => deleteNode(node.id)} className="text-slate-300 hover:text-red-500 transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                    <select
                      value={node.type}
                      onChange={e => { const nodes = wfForm.nodes.map(n => n.id === node.id ? {...n, type: e.target.value} : n); setWfForm(f => ({...f, nodes})); }}
                      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-2"
                    >
                      {ACTIONS.map(a => <option key={a.value} value={a.value}>{a.label}</option>)}
                    </select>
                    <input
                      value={node.description || ''}
                      onChange={e => { const nodes = wfForm.nodes.map(n => n.id === node.id ? {...n, description: e.target.value} : n); setWfForm(f => ({...f, nodes})); }}
                      placeholder="Add a note about this action..."
                      className="w-full text-xs border border-slate-200 rounded-lg px-2 py-1.5"
                    />
                  </div>
                ) : node.nodeType === 'condition' ? (
                  <div className="bg-amber-50 border-2 border-amber-400 rounded-xl p-4 w-72 shadow-sm">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Filter className="w-4 h-4 text-amber-600" />
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-amber-700">Condition</p>
                      </div>
                      <button onClick={() => deleteNode(node.id)} className="text-slate-300 hover:text-red-500 transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                    <div className="flex gap-1.5">
                      <select
                        value={node.field || 'campus'}
                        onChange={e => { const nodes = wfForm.nodes.map(n => n.id === node.id ? {...n, field: e.target.value} : n); setWfForm(f => ({...f, nodes})); }}
                        className="flex-1 border border-amber-200 rounded-lg px-2 py-1.5 text-xs bg-white"
                      >
                        {CONDITIONS.map(c => <option key={c.value} value={c.field}>{c.label}</option>)}
                      </select>
                      <input
                        value={node.value || ''}
                        onChange={e => { const nodes = wfForm.nodes.map(n => n.id === node.id ? {...n, value: e.target.value} : n); setWfForm(f => ({...f, nodes})); }}
                        placeholder="value"
                        className="w-20 border border-amber-200 rounded-lg px-2 py-1.5 text-xs bg-white"
                      />
                    </div>
                  </div>
                ) : node.nodeType === 'delay' ? (
                  <div className="bg-orange-50 border-2 border-orange-400 rounded-xl p-4 w-72 shadow-sm">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-orange-600" />
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-orange-700">Delay</p>
                      </div>
                      <button onClick={() => deleteNode(node.id)} className="text-slate-300 hover:text-red-500 transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-slate-600">Wait</span>
                      <input
                        type="number" min={1} max={365}
                        value={node.days || 1}
                        onChange={e => { const nodes = wfForm.nodes.map(n => n.id === node.id ? {...n, days: parseInt(e.target.value)} : n); setWfForm(f => ({...f, nodes})); }}
                        className="w-16 border border-orange-200 rounded-lg px-2 py-1.5 text-sm bg-white text-center"
                      />
                      <span className="text-sm text-slate-600">day(s)</span>
                    </div>
                  </div>
                ) : node.nodeType === 'end' ? (
                  <div className="bg-red-50 border-2 border-red-400 rounded-xl p-3 w-40 shadow-sm text-center">
                    <div className="flex items-center justify-center gap-2">
                      <X className="w-4 h-4 text-red-500" />
                      <p className="text-sm font-semibold text-red-700">End</p>
                      <button onClick={() => deleteNode(node.id)} className="text-slate-300 hover:text-red-500 transition-colors ml-1"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  </div>
                ) : null}
                {i < allNodes.length - 1 && (
                  <AddNodeButton onAdd={(type) => addNode(type, i)} />
                )}
              </div>
            ))}
            {/* Add node after last */}
            {allNodes.length > 0 && allNodes[allNodes.length - 1]?.nodeType !== 'end' && (
              <AddNodeButton onAdd={(type) => addNode(type, allNodes.length - 1)} />
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-fade-in" data-testid="workflows-page">
      <FeatureEducationHeader featureKey="workflows" />
      <div className="page-header">
        <div>
          <h1 className="page-title">Workflows</h1>
          <p className="page-subtitle">Automated care — nobody falls through the cracks</p>
        </div>
        <Button className="btn-primary" onClick={() => { setEditing(null); setWfForm(defaultWfForm); setShowBuilder(true); }} data-testid="new-workflow-btn">
          <Plus className="w-4 h-4 mr-1" /> New Workflow
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16"><Loader2 className="w-6 h-6 animate-spin text-blue-600" /></div>
      ) : workflows.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center" data-testid="workflows-empty">
          <GitBranch className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-1">Automate your follow-ups</h3>
          <p className="text-sm text-slate-500 mb-1">Create your first workflow to ensure no one falls through the cracks.</p>
          <p className="text-sm text-slate-400 mb-5">Start with a "New Visitor Follow-Up" — it converts 40% more visitors into regulars.</p>
          <Button className="btn-primary" onClick={() => { setWfForm(defaultWfForm); setShowBuilder(true); }} data-testid="create-first-workflow-btn">
            <Plus className="w-4 h-4 mr-2" /> Create Your First Workflow
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          {workflows.map(wf => {
            const trigger = TRIGGERS.find(t => t.value === wf.trigger);
            const TriggerIcon = trigger?.icon || Zap;
            return (
              <div key={wf.id} className="bg-white border border-slate-200 rounded-xl p-5 hover:shadow-sm transition-shadow" data-testid={`workflow-${wf.id}`}>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: `${trigger?.color || '#64748b'}15` }}>
                      <TriggerIcon className="w-5 h-5" style={{ color: trigger?.color || '#64748b' }} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900">{wf.name}</h3>
                      <p className="text-xs text-slate-500 mt-0.5">{wf.description || trigger?.desc}</p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
                        <span>Trigger: {trigger?.label || wf.trigger}</span>
                        <span>{(wf.steps || []).length} actions</span>
                        <span>{wf.enrolled_count || 0} enrolled</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => toggleActive(wf)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${wf.is_active ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-500 border border-slate-200'}`}
                      data-testid={`workflow-toggle-${wf.id}`}
                    >
                      {wf.is_active ? <><Activity className="w-3 h-3" /> Active</> : <><Pause className="w-3 h-3" /> Paused</>}
                    </button>
                    <Button variant="outline" size="sm" onClick={() => openEdit(wf)} data-testid={`edit-workflow-${wf.id}`}>
                      <Edit2 className="w-3.5 h-3.5 mr-1" /> Edit
                    </Button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
