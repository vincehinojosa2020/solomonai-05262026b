import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  Music, Plus, Calendar, Clock, Users, ChevronDown, ChevronUp,
  GripVertical, Trash2, Edit2, Save, ListMusic, Mic2, BookOpen
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

const ITEM_TYPES = [
  { value: 'song', label: 'Song', icon: Music },
  { value: 'prayer', label: 'Prayer', icon: BookOpen },
  { value: 'sermon', label: 'Sermon', icon: Mic2 },
  { value: 'announcement', label: 'Announcement', icon: ListMusic },
  { value: 'other', label: 'Other', icon: ListMusic },
];

const STATUS_COLORS = {
  draft: 'bg-slate-100 text-slate-600',
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

  const token = localStorage.getItem('session_token');
  const authHeaders = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  useEffect(() => { fetchPlans(); }, []);

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
        <Button className="btn-primary" onClick={() => setShowCreate(true)} data-testid="create-service-plan-btn">
          <Plus className="w-4 h-4 mr-2" />
          New Service Plan
        </Button>
      </div>

      {/* Plans List */}
      {plans.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center" data-testid="services-empty">
          <Music className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-1">No service plans yet</h3>
          <p className="text-sm text-slate-500 mb-4">Create your first service plan to start building your worship order.</p>
          <Button className="btn-primary" onClick={() => setShowCreate(true)} data-testid="services-empty-create-btn">
            <Plus className="w-4 h-4 mr-2" />
            Create Service Plan
          </Button>
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
                      {['draft', 'confirmed', 'live', 'completed'].map((s) => (
                        <Button
                          key={s}
                          variant={plan.status === s ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => updateStatus(plan.id, s)}
                          className="capitalize text-xs"
                          data-testid={`service-plan-status-action-${s}`}
                        >
                          {s}
                        </Button>
                      ))}
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
    </div>
  );
}
