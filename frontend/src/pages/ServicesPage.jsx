import { useState, useEffect } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import {
  Music, Plus, Calendar, Clock, Users, ChevronDown, ChevronUp,
  GripVertical, Trash2, Edit2, Save, ListMusic, Mic2, BookOpen,
  Copy, Bookmark, ExternalLink, UserPlus, X, HelpCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import { HelpTooltip } from '@/components/HelpTooltip';

const ITEM_TYPES = [
  { value: 'song', label: 'Song', icon: Music },
  { value: 'prayer', label: 'Prayer', icon: BookOpen },
  { value: 'sermon', label: 'Sermon', icon: Mic2 },
  { value: 'announcement', label: 'Announcement', icon: ListMusic },
  { value: 'other', label: 'Other', icon: ListMusic },
];

const STATUS_COLORS = {
  draft: 'bg-slate-100 text-slate-600',
  published: 'bg-emerald-50 text-emerald-700',
  confirmed: 'bg-blue-50 text-blue-700',
  live: 'bg-emerald-50 text-emerald-700',
  completed: 'bg-slate-100 text-slate-500',
};

export default function ServicesPage() {
  const { tenant } = useOutletContext();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedPlan, setExpandedPlan] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newPlan, setNewPlan] = useState({ title: '', date: '', service_type: 'sunday_morning' });
  const [editingItem, setEditingItem] = useState(null);
  const [itemForm, setItemForm] = useState({ title: '', type: 'song', duration: '', notes: '', leader: '' });
  const [templates, setTemplates] = useState([]);
  const [showTemplates, setShowTemplates] = useState(false);
  const [assignForm, setAssignForm] = useState({ position: '', volunteer_name: '' });
  const [showAssignForm, setShowAssignForm] = useState(null);
  const [showTutorial, setShowTutorial] = useState(false);

  const token = sessionStorage.getItem('session_token');
  const authHeaders = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  useEffect(() => { fetchPlans(); fetchTemplates(); }, []);

  const fetchTemplates = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/services/templates`, { headers: authHeaders });
      if (res.ok) { const d = await res.json(); setTemplates(d.templates || []); }
    } catch {}
  };

  const fetchPlans = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/services/plans`, { headers: authHeaders });
      if (res.ok) {
        const data = await res.json();
        setPlans(data.plans || []);
      }
    } catch (err) {
      console.error('Failed to fetch plans:', err);
    } finally {
      setLoading(false);
    }
  };

  const createPlan = async () => {
    if (!newPlan.title || !newPlan.date) { toast.error('Title and date are required'); return; }
    try {
      const res = await fetch(`${API_URL}/admin/services/plans`, {
        method: 'POST', headers: authHeaders,
        body: JSON.stringify({ ...newPlan, items: [] }),
      });
      if (res.ok) {
        toast.success('Service plan created');
        setShowCreate(false);
        setNewPlan({ title: '', date: '', service_type: 'sunday_morning' });
        fetchPlans();
      }
    } catch (err) { toast.error('Failed to create plan'); }
  };

  const addItem = async (planId) => {
    if (!itemForm.title) { toast.error('Item title is required'); return; }
    const plan = plans.find(p => p.id === planId);
    if (!plan) return;
    const newItem = { ...itemForm, id: crypto.randomUUID(), order: (plan.items || []).length };
    const updatedItems = [...(plan.items || []), newItem];
    try {
      const res = await fetch(`${API_URL}/admin/services/plans/${planId}`, {
        method: 'PUT', headers: authHeaders,
        body: JSON.stringify({ items: updatedItems }),
      });
      if (res.ok) {
        toast.success('Item added');
        setItemForm({ title: '', type: 'song', duration: '', notes: '', leader: '' });
        setEditingItem(null);
        fetchPlans();
      }
    } catch (err) { toast.error('Failed to add item'); }
  };

  const removeItem = async (planId, itemId) => {
    const plan = plans.find(p => p.id === planId);
    if (!plan) return;
    const updatedItems = (plan.items || []).filter(i => i.id !== itemId);
    try {
      await fetch(`${API_URL}/admin/services/plans/${planId}`, {
        method: 'PUT', headers: authHeaders,
        body: JSON.stringify({ items: updatedItems }),
      });
      toast.success('Item removed');
      fetchPlans();
    } catch (err) { toast.error('Failed to remove item'); }
  };

  const updateStatus = async (planId, status) => {
    try {
      await fetch(`${API_URL}/admin/services/plans/${planId}`, {
        method: 'PUT', headers: authHeaders,
        body: JSON.stringify({ status }),
      });
      toast.success(`Status updated to ${status}`);
      fetchPlans();
    } catch (err) { toast.error('Failed to update status'); }
  };

  const saveAsTemplate = async (plan) => {
    try {
      const res = await fetch(`${API_URL}/admin/services/templates`, {
        method: 'POST', headers: authHeaders,
        body: JSON.stringify({ name: plan.title, items: plan.items || [], service_type: plan.service_type })
      });
      if (res.ok) { toast.success('Saved as template'); fetchTemplates(); }
    } catch { toast.error('Failed to save template'); }
  };

  const duplicatePlan = async (planId) => {
    try {
      const res = await fetch(`${API_URL}/admin/services/plans/${planId}/duplicate`, {
        method: 'POST', headers: authHeaders, body: JSON.stringify({})
      });
      if (res.ok) { toast.success('Plan duplicated'); fetchPlans(); }
    } catch { toast.error('Failed to duplicate'); }
  };

  const createFromTemplate = async (templateId) => {
    const date = prompt('Service date (YYYY-MM-DD):', new Date().toISOString().split('T')[0]);
    if (!date) return;
    try {
      const res = await fetch(`${API_URL}/admin/services/plans/from-template`, {
        method: 'POST', headers: authHeaders,
        body: JSON.stringify({ template_id: templateId, date })
      });
      if (res.ok) { toast.success('Plan created from template'); setShowTemplates(false); fetchPlans(); }
    } catch { toast.error('Failed to create from template'); }
  };

  const addTeamAssignment = async (planId) => {
    if (!assignForm.position || !assignForm.volunteer_name) { toast.error('Position and name are required'); return; }
    const plan = plans.find(p => p.id === planId);
    if (!plan) return;
    const newAssignment = { id: crypto.randomUUID(), position: assignForm.position, volunteer_name: assignForm.volunteer_name, status: 'confirmed' };
    const updated = [...(plan.team_assignments || []), newAssignment];
    try {
      const res = await fetch(`${API_URL}/admin/services/plans/${planId}`, {
        method: 'PUT', headers: authHeaders,
        body: JSON.stringify({ team_assignments: updated })
      });
      if (res.ok) { toast.success('Team member assigned'); setAssignForm({ position: '', volunteer_name: '' }); setShowAssignForm(null); fetchPlans(); }
    } catch { toast.error('Failed to assign'); }
  };

  const removeTeamAssignment = async (planId, assignmentId) => {
    const plan = plans.find(p => p.id === planId);
    if (!plan) return;
    const updated = (plan.team_assignments || []).filter(a => a.id !== assignmentId);
    try {
      await fetch(`${API_URL}/admin/services/plans/${planId}`, {
        method: 'PUT', headers: authHeaders,
        body: JSON.stringify({ team_assignments: updated })
      });
      toast.success('Assignment removed'); fetchPlans();
    } catch { toast.error('Failed to remove'); }
  };

  const getItemIcon = (type) => {
    const found = ITEM_TYPES.find(t => t.value === type);
    return found ? found.icon : ListMusic;
  };

  const formatDate = (d) => {
    if (!d) return '';
    return new Date(d + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-6" data-testid="services-loading">
        <div className="h-8 bg-slate-200 rounded w-64" />
        <div className="h-64 bg-slate-200 rounded-lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="services-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Services</h1>
          <p className="page-subtitle">Plan worship services, assign teams, and build your run-of-show</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowTutorial(!showTutorial)} data-testid="services-tutorial-btn">
            <HelpCircle className="w-4 h-4 mr-2" /> How It Works
          </Button>
          <HelpTooltip featureKey="services" />
          {templates.length > 0 && (
            <Button variant="outline" onClick={() => setShowTemplates(true)} data-testid="from-template-btn">
              <Bookmark className="w-4 h-4 mr-2" /> From Template
            </Button>
          )}
          <Button className="btn-primary" onClick={() => setShowCreate(true)} data-testid="create-service-plan-btn">
            <Plus className="w-4 h-4 mr-2" />
            New Service Plan
          </Button>
        </div>
      </div>

      {/* Tutorial */}
      {showTutorial && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 space-y-4" data-testid="services-tutorial">
          <div className="flex items-start justify-between">
            <h3 className="text-base font-semibold text-blue-900 flex items-center gap-2">
              <HelpCircle className="w-5 h-5" /> How Services Works
            </h3>
            <button onClick={() => setShowTutorial(false)} className="text-blue-400 hover:text-blue-600">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-900">
            <div className="space-y-3">
              <div>
                <p className="font-semibold mb-1">1. Create a Service Plan</p>
                <p className="text-blue-700">Click <strong>"New Service Plan"</strong> to start. Choose a title, date, and service type (Sunday Morning, Wednesday Night, or Special Event).</p>
              </div>
              <div>
                <p className="font-semibold mb-1">2. Build Your Run-of-Show</p>
                <p className="text-blue-700">Expand any plan and click <strong>"Add Item"</strong> to add songs, prayers, sermons, or announcements. Each item can have a title, type, leader, duration, and notes.</p>
              </div>
              <div>
                <p className="font-semibold mb-1">3. Assign Your Team</p>
                <p className="text-blue-700">In the <strong>"Team Assignments"</strong> section, click <strong>"Assign"</strong> to add volunteers with their position (Worship Leader, Audio, Vocals, etc.).</p>
              </div>
            </div>
            <div className="space-y-3">
              <div>
                <p className="font-semibold mb-1">4. Publish When Ready</p>
                <p className="text-blue-700">Service plans start as <strong>Draft</strong>. When your plan is ready, click the green <strong>"Publish"</strong> button to make it visible to your team. The workflow is: Draft &rarr; Published &rarr; Live &rarr; Completed.</p>
              </div>
              <div>
                <p className="font-semibold mb-1">5. Use Templates</p>
                <p className="text-blue-700">Click <strong>"Save Template"</strong> on any plan to reuse its structure. Then use <strong>"From Template"</strong> to quickly create a new plan with the same items and layout.</p>
              </div>
              <div>
                <p className="font-semibold mb-1">6. Music Stand View</p>
                <p className="text-blue-700">Click <strong>"Music Stand"</strong> to open a distraction-free, full-screen view showing song lyrics and chord charts (ChordPro format) for your worship team on stage.</p>
              </div>
            </div>
          </div>
          <div className="pt-2 border-t border-blue-200">
            <p className="text-xs text-blue-600"><strong>Tip:</strong> You can also <strong>Duplicate</strong> any plan to create a copy, and use the <strong>Song Library</strong> (in the sidebar) to manage your congregation's full song catalog with lyrics and keys.</p>
          </div>
        </div>
      )}

      {/* Plans List */}
      {plans.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center" data-testid="services-empty">
          <Music className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-1">Create your first service plan</h3>
          <p className="text-sm text-slate-500 mb-1">Plan your Sunday worship services — songs, message, team, and the order of everything from start to finish.</p>
          <p className="text-sm text-slate-400 mb-5">This replaces spreadsheets and group texts.</p>
          <div className="flex gap-3 justify-center">
            <Button className="btn-primary" onClick={() => setShowCreate(true)} data-testid="services-empty-create-btn">
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Service Plan
            </Button>
            <Button variant="outline" onClick={() => setShowTutorial(true)}>
              See How It Works
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {plans.map((plan) => {
            const isExpanded = expandedPlan === plan.id;
            return (
              <div
                key={plan.id}
                className="bg-white border border-slate-200 rounded-xl overflow-hidden transition-shadow hover:shadow-sm"
                data-testid={`service-plan-${plan.id}`}
              >
                {/* Plan Header */}
                <button
                  className="w-full flex items-center justify-between p-5 text-left"
                  onClick={() => setExpandedPlan(isExpanded ? null : plan.id)}
                  data-testid={`service-plan-toggle-${plan.id}`}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                      <Music className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900">{plan.title}</h3>
                      <div className="flex items-center gap-3 mt-0.5 text-sm text-slate-500">
                        <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" />{formatDate(plan.date)}</span>
                        <span className="flex items-center gap-1"><ListMusic className="w-3.5 h-3.5" />{(plan.items || []).length} items</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge className={STATUS_COLORS[plan.status] || STATUS_COLORS.draft} data-testid={`service-plan-status-${plan.id}`}>
                      {plan.status || 'draft'}
                    </Badge>
                    {isExpanded ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
                  </div>
                </button>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="border-t border-slate-100 p-5 space-y-4" data-testid={`service-plan-details-${plan.id}`}>
                    {/* Status Actions */}
                    <div className="flex items-center gap-2 flex-wrap">
                      {['draft', 'published', 'live', 'completed'].map((s) => (
                        <Button
                          key={s}
                          variant={plan.status === s ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => updateStatus(plan.id, s)}
                          className={`capitalize text-xs ${s === 'published' && plan.status !== 'published' ? 'border-emerald-300 text-emerald-700 hover:bg-emerald-50' : ''}`}
                          data-testid={`service-plan-status-action-${s}`}
                        >
                          {s}
                        </Button>
                      ))}
                      {(plan.status === 'draft') && (
                        <Button
                          size="sm"
                          onClick={() => updateStatus(plan.id, 'published')}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs ml-1"
                          data-testid={`publish-plan-${plan.id}`}
                        >
                          Publish
                        </Button>
                      )}
                      <div style={{ borderLeft: '1px solid #e5e7eb', height: 20, margin: '0 4px' }} />
                      <Button size="sm" variant="outline" onClick={() => duplicatePlan(plan.id)} title="Duplicate plan" data-testid={`duplicate-plan-${plan.id}`}>
                        <Copy className="w-3.5 h-3.5 mr-1" /> Duplicate
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => saveAsTemplate(plan)} title="Save as template" data-testid={`save-template-${plan.id}`}>
                        <Bookmark className="w-3.5 h-3.5 mr-1" /> Save Template
                      </Button>
                      <Link to={`/music-stand/${plan.id}`} target="_blank" style={{ textDecoration: 'none' }}>
                        <Button size="sm" variant="outline" title="Open Music Stand" data-testid={`music-stand-${plan.id}`}>
                          <ExternalLink className="w-3.5 h-3.5 mr-1" /> Music Stand
                        </Button>
                      </Link>
                    </div>

                    {/* Items List */}
                    <div className="space-y-2">
                      {(plan.items || []).length === 0 && (
                        <p className="text-sm text-slate-400 py-3">No items in this service plan. Add songs, prayers, or announcements below.</p>
                      )}
                      {(plan.items || []).map((item, idx) => {
                        const ItemIcon = getItemIcon(item.type);
                        return (
                          <div key={item.id || idx} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg group" data-testid={`service-item-${item.id || idx}`}>
                            <GripVertical className="w-4 h-4 text-slate-300" />
                            <div className="w-8 h-8 rounded-md bg-white border border-slate-200 flex items-center justify-center">
                              <ItemIcon className="w-4 h-4 text-slate-500" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-slate-800 truncate">{item.title}</p>
                              <p className="text-xs text-slate-400">
                                {item.type}{item.leader ? ` \u00B7 ${item.leader}` : ''}{item.duration ? ` \u00B7 ${item.duration} min` : ''}
                              </p>
                            </div>
                            <button
                              className="p-1.5 text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                              onClick={() => removeItem(plan.id, item.id)}
                              data-testid={`remove-item-${item.id || idx}`}
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        );
                      })}
                    </div>

                    {/* Add Item Form */}
                    {editingItem === plan.id ? (
                      <div className="border border-blue-200 bg-blue-50/30 rounded-lg p-4 space-y-3" data-testid="add-item-form">
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                          <div>
                            <Label className="text-xs text-slate-500 mb-1 block">Title</Label>
                            <Input
                              placeholder="e.g. Way Maker"
                              value={itemForm.title}
                              onChange={(e) => setItemForm({ ...itemForm, title: e.target.value })}
                              data-testid="item-title-input"
                            />
                          </div>
                          <div>
                            <Label className="text-xs text-slate-500 mb-1 block">Type</Label>
                            <Select value={itemForm.type} onValueChange={(v) => setItemForm({ ...itemForm, type: v })}>
                              <SelectTrigger data-testid="item-type-select">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {ITEM_TYPES.map(t => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}
                              </SelectContent>
                            </Select>
                          </div>
                          <div>
                            <Label className="text-xs text-slate-500 mb-1 block">Leader</Label>
                            <Input
                              placeholder="Worship leader"
                              value={itemForm.leader}
                              onChange={(e) => setItemForm({ ...itemForm, leader: e.target.value })}
                              data-testid="item-leader-input"
                            />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <Label className="text-xs text-slate-500 mb-1 block">Duration (min)</Label>
                            <Input
                              type="number"
                              placeholder="5"
                              value={itemForm.duration}
                              onChange={(e) => setItemForm({ ...itemForm, duration: e.target.value })}
                              data-testid="item-duration-input"
                            />
                          </div>
                          <div>
                            <Label className="text-xs text-slate-500 mb-1 block">Notes</Label>
                            <Input
                              placeholder="Optional notes..."
                              value={itemForm.notes}
                              onChange={(e) => setItemForm({ ...itemForm, notes: e.target.value })}
                              data-testid="item-notes-input"
                            />
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button size="sm" onClick={() => addItem(plan.id)} data-testid="save-item-btn">
                            <Save className="w-3.5 h-3.5 mr-1.5" />Add Item
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => setEditingItem(null)}>Cancel</Button>
                        </div>
                      </div>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setEditingItem(plan.id)}
                        className="text-blue-600 border-blue-200 hover:bg-blue-50"
                        data-testid={`add-item-btn-${plan.id}`}
                      >
                        <Plus className="w-3.5 h-3.5 mr-1.5" />
                        Add Item
                      </Button>
                    )}

                    {/* Team Assignments Section */}
                    <div className="border-t border-slate-100 pt-4 mt-2" data-testid={`team-assignments-${plan.id}`}>
                      <div className="flex items-center justify-between mb-3">
                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide flex items-center gap-1.5">
                          <Users className="w-3.5 h-3.5" /> Team Assignments
                        </p>
                        <Button size="sm" variant="outline" onClick={() => setShowAssignForm(showAssignForm === plan.id ? null : plan.id)}
                          className="text-xs" data-testid={`assign-team-btn-${plan.id}`}>
                          <UserPlus className="w-3.5 h-3.5 mr-1" /> Assign
                        </Button>
                      </div>

                      {(plan.team_assignments || []).length === 0 && !showAssignForm && (
                        <p className="text-sm text-slate-400 py-2">No team members assigned to this service yet.</p>
                      )}

                      {(plan.team_assignments || []).length > 0 && (
                        <div className="space-y-1.5 mb-3">
                          {(plan.team_assignments || []).map((a, idx) => (
                            <div key={a.id || idx} className="flex items-center justify-between p-2.5 bg-purple-50/60 rounded-lg group" data-testid={`team-assignment-${a.id || idx}`}>
                              <div className="flex items-center gap-2">
                                <div className="w-7 h-7 rounded-full bg-purple-100 flex items-center justify-center">
                                  <Users className="w-3.5 h-3.5 text-purple-600" />
                                </div>
                                <div>
                                  <p className="text-sm font-medium text-slate-800">{a.volunteer_name}</p>
                                  <p className="text-xs text-slate-500">{a.position}</p>
                                </div>
                              </div>
                              <button className="p-1 text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                                onClick={() => removeTeamAssignment(plan.id, a.id)}
                                data-testid={`remove-assignment-${a.id || idx}`}>
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          ))}
                        </div>
                      )}

                      {showAssignForm === plan.id && (
                        <div className="border border-purple-200 bg-purple-50/30 rounded-lg p-3 space-y-2" data-testid="assign-team-form">
                          <div className="grid grid-cols-2 gap-2">
                            <div>
                              <Label className="text-xs text-slate-500 mb-1 block">Position / Role</Label>
                              <Input placeholder="e.g. Lead Vocals, Drums, Sound" value={assignForm.position}
                                onChange={e => setAssignForm({ ...assignForm, position: e.target.value })}
                                data-testid="assign-position-input" className="text-sm" />
                            </div>
                            <div>
                              <Label className="text-xs text-slate-500 mb-1 block">Volunteer Name</Label>
                              <Input placeholder="e.g. John Smith" value={assignForm.volunteer_name}
                                onChange={e => setAssignForm({ ...assignForm, volunteer_name: e.target.value })}
                                data-testid="assign-name-input" className="text-sm" />
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button size="sm" onClick={() => addTeamAssignment(plan.id)} data-testid="save-assignment-btn">
                              <Save className="w-3.5 h-3.5 mr-1" /> Assign
                            </Button>
                            <Button size="sm" variant="ghost" onClick={() => setShowAssignForm(null)}>Cancel</Button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Create Plan Dialog */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent data-testid="create-plan-dialog">
          <DialogHeader>
            <DialogTitle>New Service Plan</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label>Title</Label>
              <Input
                placeholder="e.g. Sunday Morning Worship"
                value={newPlan.title}
                onChange={(e) => setNewPlan({ ...newPlan, title: e.target.value })}
                data-testid="plan-title-input"
              />
            </div>
            <div>
              <Label>Date</Label>
              <Input
                type="date"
                value={newPlan.date}
                onChange={(e) => setNewPlan({ ...newPlan, date: e.target.value })}
                data-testid="plan-date-input"
              />
            </div>
            <div>
              <Label>Service Type</Label>
              <Select value={newPlan.service_type} onValueChange={(v) => setNewPlan({ ...newPlan, service_type: v })}>
                <SelectTrigger data-testid="plan-type-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sunday_morning">Sunday Morning</SelectItem>
                  <SelectItem value="sunday_evening">Sunday Evening</SelectItem>
                  <SelectItem value="wednesday">Wednesday Night</SelectItem>
                  <SelectItem value="special">Special Service</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={createPlan} data-testid="save-plan-btn">Create Plan</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Templates Dialog */}
      <Dialog open={showTemplates} onOpenChange={setShowTemplates}>
        <DialogContent className="sm:max-w-[480px]" data-testid="templates-dialog">
          <DialogHeader>
            <DialogTitle>Plan Templates</DialogTitle>
          </DialogHeader>
          <div className="space-y-2 py-2 max-h-[400px] overflow-y-auto">
            {templates.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-6">No templates saved yet. Save a plan as a template first.</p>
            ) : templates.map(t => (
              <div key={t.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors" data-testid={`template-${t.id}`}>
                <div>
                  <p className="text-sm font-medium text-slate-800">{t.name}</p>
                  <p className="text-xs text-slate-500">{(t.items || []).length} items &middot; {t.service_type}</p>
                </div>
                <Button size="sm" onClick={() => createFromTemplate(t.id)} data-testid={`use-template-${t.id}`}>
                  Use Template
                </Button>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
