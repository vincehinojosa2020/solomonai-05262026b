import { useState, useEffect, useRef, useCallback } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { Plus, ChevronLeft, ChevronRight, X, MapPin, Users, DollarSign, RefreshCw, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { API_URL, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';
import { HelpTooltip } from '@/components/HelpTooltip';

const EVENT_TYPES = [
  { id: 'service', label: 'Service', color: '#1e40af' },
  { id: 'community', label: 'Community', color: '#16a34a' },
  { id: 'conference', label: 'Conference', color: '#7c3aed' },
  { id: 'youth', label: 'Youth', color: '#db2777' },
  { id: 'group', label: 'Small Group', color: '#d97706' },
  { id: 'training', label: 'Training', color: '#0891b2' },
  { id: 'other', label: 'Other', color: '#64748b' },
];

const RECURRENCE_OPTIONS = [
  { value: '', label: 'Does not repeat' },
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'biweekly', label: 'Every 2 weeks' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'annually', label: 'Annually' },
];

const PRICING_TYPES = [
  { value: 'free', label: 'Free' },
  { value: 'fixed', label: 'Fixed Price' },
  { value: 'donation', label: 'Pay What You Can' },
];

const defaultForm = {
  name: '', description: '', event_date: '', start_time: '', end_time: '',
  location: '', capacity: '', event_type: 'service', is_public: true,
  requires_registration: false, recurring: '', pricing_type: 'free', price: '',
};

export default function CalendarPage() {
  const calendarRef = useRef();
  const token = sessionStorage.getItem('session_token');
  const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [saving, setSaving] = useState(false);
  const [calView, setCalView] = useState('dayGridMonth');
  const [filterType, setFilterType] = useState('');

  const fetchEvents = useCallback(async (start, end) => {
    try {
      const params = new URLSearchParams();
      if (start) params.set('start', start);
      if (end) params.set('end', end);
      if (filterType) params.set('event_type', filterType);
      const res = await fetch(`${API_URL}/admin/events/calendar?${params}`, { headers });
      if (res.ok) {
        const data = await res.json();
        setEvents(data.events || []);
      }
    } catch (e) { console.error(e); }
  }, [filterType]);

  useEffect(() => { fetchEvents(); }, [filterType]);

  const handleDateClick = (arg) => {
    setForm({ ...defaultForm, event_date: arg.dateStr });
    setShowCreateModal(true);
  };

  const handleEventClick = (info) => {
    setSelectedEvent({
      id: info.event.id,
      title: info.event.title,
      start: info.event.startStr,
      end: info.event.endStr,
      ...info.event.extendedProps,
    });
  };

  const handleEventDrop = async (info) => {
    const newDate = info.event.startStr.split('T')[0];
    try {
      await fetch(`${API_URL}/admin/events/${info.event.id}`, {
        method: 'PUT', headers,
        body: JSON.stringify({ event_date: newDate }),
      });
      toast.success('Event rescheduled');
    } catch { info.revert(); toast.error('Failed to reschedule'); }
  };

  const saveEvent = async () => {
    if (!form.name || !form.event_date) { toast.error('Name and date required'); return; }
    setSaving(true);
    try {
      const payload = {
        ...form,
        capacity: form.capacity ? parseInt(form.capacity) : null,
        price: form.price ? parseFloat(form.price) : 0,
        requires_registration: form.requires_registration || form.pricing_type !== 'free',
      };
      const res = await fetch(`${API_URL}/admin/events`, { method: 'POST', headers, body: JSON.stringify(payload) });
      if (res.ok) {
        toast.success('Event created!');
        setShowCreateModal(false);
        setForm(defaultForm);
        fetchEvents();
      } else { toast.error('Failed to create event'); }
    } catch { toast.error('Error saving event'); } finally { setSaving(false); }
  };

  const deleteEvent = async (eventId) => {
    if (!confirm('Delete this event?')) return;
    try {
      await fetch(`${API_URL}/admin/events/${eventId}`, { method: 'DELETE', headers });
      toast.success('Event deleted');
      setSelectedEvent(null);
      fetchEvents();
    } catch { toast.error('Failed to delete'); }
  };

  return (
    <div className="space-y-4 animate-fade-in" data-testid="calendar-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Calendar</h1>
          <p className="page-subtitle">All events, services, and room bookings</p>
        </div>
        <div className="flex items-center gap-2">
          <HelpTooltip featureKey="calendar" />
          {EVENT_TYPES.map(t => (
            <button
              key={t.id}
              onClick={() => setFilterType(filterType === t.id ? '' : t.id)}
              style={{ background: filterType === t.id ? t.color : 'transparent', borderColor: t.color, color: filterType === t.id ? 'white' : t.color }}
              className="px-2 py-1 rounded-full text-xs font-medium border transition-all"
              data-testid={`filter-${t.id}`}
            >{t.label}</button>
          ))}
          <Button className="btn-primary" onClick={() => { setForm(defaultForm); setShowCreateModal(true); }} data-testid="create-event-btn">
            <Plus className="w-4 h-4 mr-1" /> New Event
          </Button>
        </div>
      </div>

      {/* Calendar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 overflow-hidden" data-testid="fullcalendar-container">
        <FullCalendar
          ref={calendarRef}
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView={calView}
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay',
          }}
          events={events}
          editable={true}
          selectable={true}
          dateClick={handleDateClick}
          eventClick={handleEventClick}
          eventDrop={handleEventDrop}
          height="auto"
          viewDidMount={(info) => setCalView(info.view.type)}
          eventDidMount={(info) => {
            info.el.title = info.event.extendedProps.description || '';
          }}
        />
      </div>

      {/* Event Detail Panel */}
      {selectedEvent && (
        <div className="fixed right-0 top-0 h-full w-80 bg-white border-l border-slate-200 shadow-xl z-50 flex flex-col" data-testid="event-detail-panel">
          <div className="p-4 border-b border-slate-100 flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ background: EVENT_TYPES.find(t => t.id === selectedEvent.event_type)?.color || '#64748b' }}
                />
                <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                  {selectedEvent.event_type || 'Event'}
                </span>
              </div>
              <h2 className="font-semibold text-slate-900 text-base">{selectedEvent.title}</h2>
            </div>
            <button onClick={() => setSelectedEvent(null)} className="text-slate-400 hover:text-slate-600">
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2 text-slate-600">
                <Calendar className="w-4 h-4 text-slate-400" />
                <span>{selectedEvent.start?.split('T')[0]}</span>
                {selectedEvent.start?.includes('T') && (
                  <span className="text-slate-400">
                    {selectedEvent.start.split('T')[1]?.slice(0,5)}
                    {selectedEvent.end?.includes('T') && ` – ${selectedEvent.end.split('T')[1]?.slice(0,5)}`}
                  </span>
                )}
              </div>
              {selectedEvent.location && (
                <div className="flex items-center gap-2 text-slate-600">
                  <MapPin className="w-4 h-4 text-slate-400" />
                  <span>{selectedEvent.location}</span>
                </div>
              )}
              {selectedEvent.capacity && (
                <div className="flex items-center gap-2 text-slate-600">
                  <Users className="w-4 h-4 text-slate-400" />
                  <span>Capacity: {selectedEvent.capacity}</span>
                </div>
              )}
              {selectedEvent.price > 0 && (
                <div className="flex items-center gap-2 text-slate-600">
                  <DollarSign className="w-4 h-4 text-slate-400" />
                  <span>{formatCurrency(selectedEvent.price)} registration fee</span>
                </div>
              )}
              {selectedEvent.recurring && (
                <div className="flex items-center gap-2 text-slate-600">
                  <RefreshCw className="w-4 h-4 text-slate-400" />
                  <span>Recurring event</span>
                </div>
              )}
            </div>
            {selectedEvent.description && (
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Description</p>
                <p className="text-sm text-slate-700 leading-relaxed">{selectedEvent.description}</p>
              </div>
            )}
          </div>
          <div className="p-4 border-t border-slate-100 space-y-2">
            <Button variant="outline" className="w-full text-sm" size="sm" data-testid="edit-event-btn">Edit Event</Button>
            <Button
              variant="outline"
              className="w-full text-sm text-red-500 border-red-200 hover:bg-red-50"
              size="sm"
              onClick={() => deleteEvent(selectedEvent.id)}
              data-testid="delete-event-btn"
            >Delete Event</Button>
          </div>
        </div>
      )}

      {/* Create Event Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setShowCreateModal(false)}>
          <div
            className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
            onClick={e => e.stopPropagation()}
            data-testid="create-event-modal"
          >
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <h2 className="font-semibold text-slate-900">Create Event</h2>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-500 uppercase tracking-wider">Event Name *</label>
                <input
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-300"
                  value={form.name} onChange={e => setForm({...form, name: e.target.value})}
                  placeholder="Sunday Worship Service" data-testid="event-name-input"
                />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-medium text-slate-500">Date *</label>
                  <input type="date" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" value={form.event_date} onChange={e => setForm({...form, event_date: e.target.value})} data-testid="event-date-input" />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500">Start</label>
                  <input type="time" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" value={form.start_time} onChange={e => setForm({...form, start_time: e.target.value})} data-testid="event-start-input" />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500">End</label>
                  <input type="time" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" value={form.end_time} onChange={e => setForm({...form, end_time: e.target.value})} data-testid="event-end-input" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-slate-500">Location</label>
                  <input className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" value={form.location} onChange={e => setForm({...form, location: e.target.value})} placeholder="Sanctuary" />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-500">Capacity</label>
                  <input type="number" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" value={form.capacity} onChange={e => setForm({...form, capacity: e.target.value})} placeholder="500" />
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500">Event Type</label>
                <div className="flex flex-wrap gap-2 mt-1">
                  {EVENT_TYPES.map(t => (
                    <button
                      key={t.id}
                      onClick={() => setForm({...form, event_type: t.id})}
                      style={{ background: form.event_type === t.id ? t.color : 'transparent', borderColor: t.color, color: form.event_type === t.id ? 'white' : t.color }}
                      className="px-3 py-1 rounded-full text-xs font-medium border transition-all"
                    >{t.label}</button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500">Recurrence</label>
                <select className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" value={form.recurring} onChange={e => setForm({...form, recurring: e.target.value})} data-testid="event-recurrence">
                  {RECURRENCE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500">Pricing</label>
                <div className="grid grid-cols-3 gap-2 mt-1">
                  {PRICING_TYPES.map(p => (
                    <button key={p.value} onClick={() => setForm({...form, pricing_type: p.value})} className={`py-2 px-3 border rounded-lg text-xs font-medium transition-all ${form.pricing_type === p.value ? 'bg-slate-900 text-white border-slate-900' : 'border-slate-200 text-slate-600'}`}>
                      {p.label}
                    </button>
                  ))}
                </div>
                {form.pricing_type !== 'free' && (
                  <div className="mt-2 relative">
                    <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input type="number" placeholder="0.00" className="w-full pl-8 pr-3 py-2 border border-slate-200 rounded-lg text-sm" value={form.price} onChange={e => setForm({...form, price: e.target.value})} />
                  </div>
                )}
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500">Description</label>
                <textarea rows={2} className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm resize-none" value={form.description} onChange={e => setForm({...form, description: e.target.value})} placeholder="Optional event description..." />
              </div>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
                  <input type="checkbox" checked={form.is_public} onChange={e => setForm({...form, is_public: e.target.checked})} className="rounded" />
                  Public event
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
                  <input type="checkbox" checked={form.requires_registration} onChange={e => setForm({...form, requires_registration: e.target.checked})} className="rounded" />
                  Requires registration
                </label>
              </div>
            </div>
            <div className="p-5 border-t border-slate-100 flex gap-3">
              <Button variant="outline" className="flex-1" onClick={() => setShowCreateModal(false)}>Cancel</Button>
              <Button className="flex-1 btn-primary" onClick={saveEvent} disabled={saving} data-testid="save-event-btn">
                {saving ? 'Creating...' : 'Create Event'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
