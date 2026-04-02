import { useState, useEffect } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import {
  ClipboardList, Plus, Search, Calendar, Users, DollarSign,
  ChevronDown, ChevronUp, Trash2, Edit2, Settings, Eye,
  UserCheck, Clock, Loader2, ExternalLink, Tag, Gift
} from 'lucide-react';
import { SectionTutorial, TUTORIALS } from '@/components/SectionTutorial';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
} from '@/components/ui/dialog';
import { API_URL, formatDate } from '@/lib/utils';
import { toast } from 'sonner';

export default function RegistrationsPage() {
  const { tenant } = useOutletContext();
  const navigate = useNavigate();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedEvent, setExpandedEvent] = useState(null);
  const [registrants, setRegistrants] = useState([]);
  const [configEvent, setConfigEvent] = useState(null);
  const [config, setConfig] = useState(null);
  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [showPromoDialog, setShowPromoDialog] = useState(false);
  const [promoForm, setPromoForm] = useState({ code: '', discount_type: 'percentage', discount_value: 10, max_uses: '' });

  const token = sessionStorage.getItem('session_token');
  const authHeaders = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  useEffect(() => { fetchEvents(); }, []);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/admin/registrations/events`, { headers: authHeaders });
      if (res.ok) { const d = await res.json(); setEvents(d.events || []); }
    } catch (e) { toast.error('Failed to load events'); }
    finally { setLoading(false); }
  };

  const fetchRegistrants = async (eventId) => {
    try {
      const res = await fetch(`${API_URL}/admin/registrations/${eventId}/registrants`, { headers: authHeaders });
      if (res.ok) { const d = await res.json(); setRegistrants(d.registrants || []); }
    } catch (e) { console.error(e); }
  };

  const fetchConfig = async (eventId) => {
    try {
      const res = await fetch(`${API_URL}/admin/registrations/configs/${eventId}`, { headers: authHeaders });
      if (res.ok) { const d = await res.json(); setConfig(d.config); }
    } catch (e) { console.error(e); }
  };

  const toggleEvent = async (eventId) => {
    if (expandedEvent === eventId) { setExpandedEvent(null); return; }
    setExpandedEvent(eventId);
    fetchRegistrants(eventId);
  };

  const openConfig = async (event) => {
    setConfigEvent(event);
    await fetchConfig(event.id);
    setShowConfigDialog(true);
  };

  const saveConfig = async () => {
    if (!configEvent || !config) return;
    try {
      const res = await fetch(`${API_URL}/admin/registrations/configs/${configEvent.id}`, {
        method: 'POST', headers: authHeaders, body: JSON.stringify(config)
      });
      if (res.ok) { toast.success('Config saved'); setShowConfigDialog(false); fetchEvents(); }
    } catch (e) { toast.error('Failed to save'); }
  };

  const updateRegistrantStatus = async (eventId, regId, status) => {
    try {
      await fetch(`${API_URL}/admin/registrations/${eventId}/registrants/${regId}`, {
        method: 'PUT', headers: authHeaders, body: JSON.stringify({ status })
      });
      toast.success(`Registrant ${status}`);
      fetchRegistrants(eventId);
    } catch (e) { toast.error('Failed to update'); }
  };

  const addPromoCode = async () => {
    if (!configEvent || !promoForm.code) { toast.error('Code is required'); return; }
    try {
      await fetch(`${API_URL}/admin/registrations/${configEvent.id}/promo-codes`, {
        method: 'POST', headers: authHeaders,
        body: JSON.stringify({
          code: promoForm.code,
          discount_type: promoForm.discount_type,
          discount_value: parseFloat(promoForm.discount_value),
          max_uses: promoForm.max_uses ? parseInt(promoForm.max_uses) : null,
        })
      });
      toast.success('Promo code added');
      setShowPromoDialog(false);
      setPromoForm({ code: '', discount_type: 'percentage', discount_value: 10, max_uses: '' });
      fetchConfig(configEvent.id);
    } catch (e) { toast.error('Failed to add promo code'); }
  };

  const baseUrl = window.location.origin;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="registrations-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2.5">
            <ClipboardList className="w-7 h-7 text-blue-600" />
            Registrations
          </h1>
          <p className="text-sm text-slate-500 mt-1">Manage event signups, add-ons, pricing, and waitlists</p>
        </div>
        <SectionTutorial {...TUTORIALS.registrations} />
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : events.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-16 text-center" data-testid="reg-empty">
          <ClipboardList className="w-14 h-14 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">No registration events</h3>
          <p className="text-sm text-slate-500">Enable registration on an event from the Calendar to get started.</p>
        </div>
      ) : (
        <div className="space-y-3" data-testid="reg-events-list">
          {events.map(evt => (
            <div key={evt.id} className="bg-white border border-slate-200 rounded-xl overflow-hidden" data-testid={`reg-event-${evt.id}`}>
              <button
                onClick={() => toggleEvent(evt.id)}
                className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition-colors text-left"
                data-testid={`reg-toggle-${evt.id}`}
              >
                <div className="flex items-center gap-4">
                  <div className="w-11 h-11 rounded-lg bg-blue-50 flex items-center justify-center">
                    <Calendar className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-800">{evt.name}</h3>
                    <p className="text-xs text-slate-500 flex items-center gap-3 mt-0.5">
                      <span>{formatDate(evt.start_datetime)}</span>
                      {evt.location && <span>{evt.location}</span>}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant="outline" className="text-emerald-600 border-emerald-200 text-xs">
                    <UserCheck className="w-3 h-3 mr-1" />{evt.confirmed_count || 0} registered
                  </Badge>
                  {evt.waitlist_count > 0 && (
                    <Badge variant="outline" className="text-amber-600 border-amber-200 text-xs">
                      <Clock className="w-3 h-3 mr-1" />{evt.waitlist_count} waitlisted
                    </Badge>
                  )}
                  {evt.capacity && (
                    <span className="text-xs text-slate-400">{evt.capacity} capacity</span>
                  )}
                  {expandedEvent === evt.id ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                </div>
              </button>

              {expandedEvent === evt.id && (
                <div className="border-t border-slate-100 p-4 space-y-4" data-testid={`reg-details-${evt.id}`}>
                  {/* Actions bar */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <Button size="sm" variant="outline" onClick={() => openConfig(evt)} data-testid={`reg-config-btn-${evt.id}`}>
                      <Settings className="w-3.5 h-3.5 mr-1.5" /> Configure
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => { setConfigEvent(evt); setShowPromoDialog(true); }} data-testid={`reg-promo-btn-${evt.id}`}>
                      <Tag className="w-3.5 h-3.5 mr-1.5" /> Add Promo Code
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => navigator.clipboard.writeText(`${baseUrl}/register/${evt.id}`).then(() => toast.success('Link copied!'))} data-testid={`reg-link-btn-${evt.id}`}>
                      <ExternalLink className="w-3.5 h-3.5 mr-1.5" /> Copy Registration Link
                    </Button>
                    <a href={`/register/${evt.id}`} target="_blank" rel="noopener noreferrer">
                      <Button size="sm" variant="outline">
                        <Eye className="w-3.5 h-3.5 mr-1.5" /> Preview Form
                      </Button>
                    </a>
                  </div>

                  {/* Config summary */}
                  {evt.pricing?.enabled && (
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <DollarSign className="w-3.5 h-3.5" />
                      <span>Price: ${evt.pricing.amount} {evt.pricing.currency}</span>
                    </div>
                  )}

                  {/* Registrants table */}
                  <div className="bg-slate-50/50 rounded-lg overflow-hidden">
                    <table className="w-full text-sm" data-testid={`reg-table-${evt.id}`}>
                      <thead>
                        <tr className="border-b border-slate-200">
                          <th className="text-left p-3 text-xs font-semibold text-slate-500 uppercase">Name</th>
                          <th className="text-left p-3 text-xs font-semibold text-slate-500 uppercase">Email</th>
                          <th className="text-left p-3 text-xs font-semibold text-slate-500 uppercase">Status</th>
                          <th className="text-left p-3 text-xs font-semibold text-slate-500 uppercase">Amount</th>
                          <th className="text-left p-3 text-xs font-semibold text-slate-500 uppercase">Registered</th>
                          <th className="text-right p-3 text-xs font-semibold text-slate-500 uppercase">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {registrants.length === 0 ? (
                          <tr><td colSpan={6} className="text-center py-8 text-slate-400">No registrants yet</td></tr>
                        ) : registrants.map((r, idx) => (
                          <tr key={r.id} className="border-t border-slate-100" data-testid={`registrant-${r.id}`}>
                            <td className="p-3 font-medium text-slate-700">{r.user_name || '-'}</td>
                            <td className="p-3 text-slate-600">{r.user_email || '-'}</td>
                            <td className="p-3">
                              <Badge variant="outline" className={
                                r.status === 'confirmed' ? 'text-emerald-600 border-emerald-200' :
                                r.status === 'waitlisted' ? 'text-amber-600 border-amber-200' :
                                'text-red-600 border-red-200'
                              }>{r.status || 'confirmed'}</Badge>
                            </td>
                            <td className="p-3 text-slate-600">{r.amount_total ? `$${r.amount_total}` : 'Free'}</td>
                            <td className="p-3 text-slate-500 text-xs">{formatDate(r.registered_at)}</td>
                            <td className="p-3 text-right">
                              {r.status === 'waitlisted' && (
                                <Button size="sm" variant="outline" className="text-emerald-600 text-xs"
                                  onClick={() => updateRegistrantStatus(evt.id, r.id, 'confirmed')} data-testid={`confirm-${r.id}`}>
                                  Confirm
                                </Button>
                              )}
                              {r.status !== 'cancelled' && (
                                <Button size="sm" variant="ghost" className="text-red-400 text-xs ml-1"
                                  onClick={() => updateRegistrantStatus(evt.id, r.id, 'cancelled')} data-testid={`cancel-${r.id}`}>
                                  Cancel
                                </Button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Registration Config Dialog */}
      <Dialog open={showConfigDialog} onOpenChange={setShowConfigDialog}>
        <DialogContent className="sm:max-w-[560px]" data-testid="reg-config-dialog">
          <DialogHeader>
            <DialogTitle>Registration Settings — {configEvent?.name}</DialogTitle>
          </DialogHeader>
          {config ? (
            <div className="space-y-5 py-2 max-h-[500px] overflow-y-auto">
              {/* Pricing */}
              <div className="space-y-2">
                <Label className="text-xs font-semibold text-slate-500 uppercase">Pricing</Label>
                <div className="flex items-center gap-3">
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={config.pricing?.enabled || false}
                      onChange={e => setConfig({ ...config, pricing: { ...config.pricing, enabled: e.target.checked }})} />
                    Paid event
                  </label>
                  {config.pricing?.enabled && (
                    <Input type="number" className="w-28" placeholder="Amount" value={config.pricing?.amount || ''}
                      onChange={e => setConfig({ ...config, pricing: { ...config.pricing, amount: parseFloat(e.target.value) || 0 }})}
                      data-testid="config-price-input" />
                  )}
                </div>
              </div>

              {/* Add-ons */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-xs font-semibold text-slate-500 uppercase">Add-ons</Label>
                  <Button size="sm" variant="outline" className="text-xs" onClick={() => {
                    const addons = [...(config.add_ons || []), { id: `addon_${Date.now()}`, name: '', price: 0, description: '', max_qty: 0, required: false }];
                    setConfig({ ...config, add_ons: addons });
                  }} data-testid="add-addon-btn"><Plus className="w-3 h-3 mr-1" />Add</Button>
                </div>
                {(config.add_ons || []).length === 0 && (
                  <p className="text-xs text-slate-400 text-center py-3">No add-ons yet. Add optional items like t-shirts, meals, or materials.</p>
                )}
                {(config.add_ons || []).map((addon, i) => (
                  <div key={addon.id} className="p-3 bg-slate-50 rounded-lg space-y-2 border border-slate-100" data-testid={`addon-card-${i}`}>
                    <div className="flex items-center gap-2">
                      <Gift className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                      <Input placeholder="Add-on name (e.g. T-Shirt, Lunch)" className="text-sm flex-1" value={addon.name}
                        onChange={e => { const a = [...config.add_ons]; a[i] = { ...a[i], name: e.target.value }; setConfig({ ...config, add_ons: a }); }}
                        data-testid={`addon-name-${i}`} />
                      <div className="flex items-center gap-1">
                        <span className="text-xs text-slate-400">$</span>
                        <Input type="number" placeholder="0" className="w-16 text-sm" value={addon.price}
                          onChange={e => { const a = [...config.add_ons]; a[i] = { ...a[i], price: parseFloat(e.target.value) || 0 }; setConfig({ ...config, add_ons: a }); }}
                          data-testid={`addon-price-${i}`} />
                      </div>
                      <button onClick={() => { const a = config.add_ons.filter((_, idx) => idx !== i); setConfig({ ...config, add_ons: a }); }}
                        className="text-red-400 hover:text-red-600 p-1"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                    <Input placeholder="Description (shown to registrants)" className="text-xs" value={addon.description || ''}
                      onChange={e => { const a = [...config.add_ons]; a[i] = { ...a[i], description: e.target.value }; setConfig({ ...config, add_ons: a }); }}
                      data-testid={`addon-desc-${i}`} />
                    <div className="flex items-center gap-4">
                      <label className="flex items-center gap-1.5 text-xs text-slate-500 cursor-pointer">
                        <input type="checkbox" checked={addon.required || false}
                          onChange={e => { const a = [...config.add_ons]; a[i] = { ...a[i], required: e.target.checked }; setConfig({ ...config, add_ons: a }); }}
                          className="rounded w-3.5 h-3.5" />
                        Required
                      </label>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs text-slate-400">Max qty:</span>
                        <Input type="number" min="0" placeholder="0=unlimited" className="w-20 text-xs h-7" value={addon.max_qty || ''}
                          onChange={e => { const a = [...config.add_ons]; a[i] = { ...a[i], max_qty: parseInt(e.target.value) || 0 }; setConfig({ ...config, add_ons: a }); }}
                          data-testid={`addon-qty-${i}`} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Custom Questions */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-xs font-semibold text-slate-500 uppercase">Custom Questions</Label>
                  <Button size="sm" variant="outline" className="text-xs" onClick={() => {
                    const qs = [...(config.custom_questions || []), { id: `q_${Date.now()}`, label: '', type: 'text', required: false }];
                    setConfig({ ...config, custom_questions: qs });
                  }} data-testid="add-question-btn"><Plus className="w-3 h-3 mr-1" />Add</Button>
                </div>
                {(config.custom_questions || []).map((q, i) => (
                  <div key={q.id} className="flex items-center gap-2 p-2 bg-slate-50 rounded-lg">
                    <Input placeholder="Question" className="text-sm flex-1" value={q.label}
                      onChange={e => { const qs = [...config.custom_questions]; qs[i] = { ...qs[i], label: e.target.value }; setConfig({ ...config, custom_questions: qs }); }}
                      data-testid={`question-label-${i}`} />
                    <select className="text-xs border rounded px-2 py-1.5" value={q.type}
                      onChange={e => { const qs = [...config.custom_questions]; qs[i] = { ...qs[i], type: e.target.value }; setConfig({ ...config, custom_questions: qs }); }}>
                      <option value="text">Text</option>
                      <option value="select">Select</option>
                      <option value="checkbox">Checkbox</option>
                    </select>
                    <label className="flex items-center gap-1 text-xs whitespace-nowrap">
                      <input type="checkbox" checked={q.required}
                        onChange={e => { const qs = [...config.custom_questions]; qs[i] = { ...qs[i], required: e.target.checked }; setConfig({ ...config, custom_questions: qs }); }} />
                      Req
                    </label>
                    <button onClick={() => { const qs = config.custom_questions.filter((_, idx) => idx !== i); setConfig({ ...config, custom_questions: qs }); }}
                      className="text-red-400 hover:text-red-600"><Trash2 className="w-3.5 h-3.5" /></button>
                  </div>
                ))}
              </div>

              {/* Promo Codes List */}
              {(config.promo_codes || []).length > 0 && (
                <div className="space-y-2">
                  <Label className="text-xs font-semibold text-slate-500 uppercase">Active Promo Codes</Label>
                  {config.promo_codes.map(pc => (
                    <div key={pc.id} className="flex items-center justify-between p-2 bg-amber-50 rounded-lg text-sm">
                      <span className="font-mono font-semibold text-amber-700">{pc.code}</span>
                      <span className="text-xs text-amber-600">
                        {pc.discount_type === 'percentage' ? `${pc.discount_value}% off` : `$${pc.discount_value} off`}
                        {pc.max_uses && ` (${pc.uses_count}/${pc.max_uses} used)`}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Settings */}
              <div className="space-y-2">
                <Label className="text-xs font-semibold text-slate-500 uppercase">Settings</Label>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={config.waitlist_enabled ?? true}
                    onChange={e => setConfig({ ...config, waitlist_enabled: e.target.checked })} />
                  Enable waitlist when full
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={config.auto_confirm ?? true}
                    onChange={e => setConfig({ ...config, auto_confirm: e.target.checked })} />
                  Auto-confirm registrations
                </label>
              </div>
            </div>
          ) : (
            <div className="py-8 text-center">
              <p className="text-sm text-slate-400">No configuration yet. Save to create one.</p>
              <Button className="mt-3" onClick={() => setConfig({
                pricing: { enabled: false, amount: 0, currency: 'USD' },
                add_ons: [], custom_questions: [], promo_codes: [],
                waitlist_enabled: true, auto_confirm: true, require_payment: false
              })}>Create Config</Button>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowConfigDialog(false)}>Cancel</Button>
            {config && <Button onClick={saveConfig} data-testid="save-config-btn">Save Configuration</Button>}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Promo Code Dialog */}
      <Dialog open={showPromoDialog} onOpenChange={setShowPromoDialog}>
        <DialogContent data-testid="promo-dialog">
          <DialogHeader><DialogTitle>Add Promo Code</DialogTitle></DialogHeader>
          <div className="space-y-3 py-2">
            <div>
              <Label>Code</Label>
              <Input placeholder="e.g. EARLYBIRD" value={promoForm.code}
                onChange={e => setPromoForm({ ...promoForm, code: e.target.value.toUpperCase() })}
                className="font-mono" data-testid="promo-code-input" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Discount Type</Label>
                <select className="w-full rounded-md border p-2 text-sm" value={promoForm.discount_type}
                  onChange={e => setPromoForm({ ...promoForm, discount_type: e.target.value })} data-testid="promo-type-select">
                  <option value="percentage">Percentage (%)</option>
                  <option value="fixed">Fixed Amount ($)</option>
                </select>
              </div>
              <div>
                <Label>Value</Label>
                <Input type="number" value={promoForm.discount_value}
                  onChange={e => setPromoForm({ ...promoForm, discount_value: e.target.value })} data-testid="promo-value-input" />
              </div>
            </div>
            <div>
              <Label>Max Uses (blank for unlimited)</Label>
              <Input type="number" placeholder="Unlimited" value={promoForm.max_uses}
                onChange={e => setPromoForm({ ...promoForm, max_uses: e.target.value })} data-testid="promo-max-input" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPromoDialog(false)}>Cancel</Button>
            <Button onClick={addPromoCode} data-testid="save-promo-btn">Add Code</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
