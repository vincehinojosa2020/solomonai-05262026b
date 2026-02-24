import { useState, useEffect } from 'react';
import { 
  Calendar, Plus, Search, Edit, Trash2, MapPin, Clock,
  Users, ChevronRight, Loader2, CheckCircle, X, UserPlus
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';

export default function EventsManagerPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingEvent, setEditingEvent] = useState(null);
  const [viewingEvent, setViewingEvent] = useState(null);
  const [showPast, setShowPast] = useState(false);
  const [stats, setStats] = useState({ total: 0, upcoming: 0, registrations: 0 });

  useEffect(() => {
    fetchEvents();
  }, [showPast]);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('upcoming_only', (!showPast).toString());
      
      const res = await fetch(`${API_URL}/admin/events?${params}`, { credentials: 'include' });
      
      if (res.ok) {
        const data = await res.json();
        setEvents(data.events || []);
        
        const totalRegs = (data.events || []).reduce((sum, e) => sum + (e.registration_count || 0), 0);
        setStats({
          total: data.total || 0,
          upcoming: data.total || 0,
          registrations: totalRegs
        });
      }
    } catch (error) {
      console.error('Error fetching events:', error);
      toast.error('Failed to load events');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteEvent = async (eventId) => {
    if (!confirm('Are you sure you want to delete this event? All registrations will be removed.')) return;
    
    try {
      const res = await fetch(`${API_URL}/admin/events/${eventId}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      
      if (res.ok) {
        toast.success('Event deleted');
        fetchEvents();
      } else {
        toast.error('Failed to delete event');
      }
    } catch (error) {
      toast.error('Failed to delete event');
    }
  };

  const filteredEvents = events.filter(e => {
    if (!searchQuery) return true;
    return e.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
           e.location?.toLowerCase().includes(searchQuery.toLowerCase());
  });

  return (
    <div className="events-manager" data-testid="events-manager">
      {/* Header */}
      <div className="events-manager-header">
        <div className="events-manager-title-row">
          <div>
            <h1 className="events-manager-title">
              <Calendar className="w-7 h-7 text-orange-600" />
              Events & Services
            </h1>
            <p className="events-manager-subtitle">
              Create events that members can discover and register for
            </p>
          </div>
          
          <Button 
            onClick={() => setShowAddModal(true)}
            className="events-add-btn"
            data-testid="add-event-btn"
          >
            <Plus className="w-4 h-4" />
            Create Event
          </Button>
        </div>

        {/* Stats */}
        <div className="events-stats-row">
          <div className="events-stat">
            <span className="events-stat-value">{stats.total}</span>
            <span className="events-stat-label">{showPast ? 'All Events' : 'Upcoming'}</span>
          </div>
          <div className="events-stat">
            <span className="events-stat-value text-orange-600">{stats.registrations}</span>
            <span className="events-stat-label">Registrations</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="events-filters-bar">
        <div className="events-search">
          <Search className="w-4 h-4 text-slate-400" />
          <Input
            type="text"
            placeholder="Search events..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="events-search-input"
          />
        </div>

        <label className="events-toggle-past">
          <input
            type="checkbox"
            checked={showPast}
            onChange={(e) => setShowPast(e.target.checked)}
          />
          Show past events
        </label>
      </div>

      {/* Events List */}
      {loading ? (
        <div className="events-loading">
          <Loader2 className="w-8 h-8 animate-spin text-orange-600" />
          <p>Loading events...</p>
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="events-empty-state">
          <Calendar className="w-16 h-16 text-slate-300" />
          <h2>No events yet</h2>
          <p>Create events for members to discover and register.</p>
          <Button onClick={() => setShowAddModal(true)} className="events-add-btn">
            <Plus className="w-4 h-4" />
            Create Your First Event
          </Button>
        </div>
      ) : (
        <div className="events-list" data-testid="events-list">
          {filteredEvents.map(event => (
            <EventCard 
              key={event.id} 
              event={event}
              onEdit={() => setEditingEvent(event)}
              onDelete={() => handleDeleteEvent(event.id)}
              onViewRegistrations={() => setViewingEvent(event)}
            />
          ))}
        </div>
      )}

      {/* Add Event Modal */}
      <AddEventModal 
        open={showAddModal} 
        onClose={() => setShowAddModal(false)}
        onSuccess={() => {
          setShowAddModal(false);
          fetchEvents();
        }}
      />

      {/* Edit Event Modal */}
      {editingEvent && (
        <EditEventModal 
          event={editingEvent}
          open={!!editingEvent} 
          onClose={() => setEditingEvent(null)}
          onSuccess={() => {
            setEditingEvent(null);
            fetchEvents();
          }}
        />
      )}

      {/* View Registrations Modal */}
      {viewingEvent && (
        <ViewRegistrationsModal
          event={viewingEvent}
          open={!!viewingEvent}
          onClose={() => {
            setViewingEvent(null);
            fetchEvents();
          }}
        />
      )}
    </div>
  );
}

function EventCard({ event, onEdit, onDelete, onViewRegistrations }) {
  const eventDate = new Date(event.event_date);
  const isPast = eventDate < new Date();
  const isFull = event.capacity && event.registration_count >= event.capacity;

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
  };

  return (
    <div className={`event-card ${isPast ? 'past' : ''}`} data-testid={`event-card-${event.id}`}>
      <div className="event-card-date">
        <span className="event-month">{eventDate.toLocaleDateString('en-US', { month: 'short' })}</span>
        <span className="event-day">{eventDate.getDate()}</span>
      </div>

      <div className="event-card-content">
        <div className="event-card-header">
          <h3 className="event-card-title">{event.name}</h3>
          {isFull && <span className="event-full-badge">Full</span>}
        </div>
        
        {event.description && (
          <p className="event-card-desc">{event.description}</p>
        )}
        
        <div className="event-card-meta">
          <div className="event-meta-item">
            <Calendar className="w-4 h-4" />
            <span>{formatDate(event.event_date)}</span>
          </div>
          {event.start_time && (
            <div className="event-meta-item">
              <Clock className="w-4 h-4" />
              <span>{event.start_time}{event.end_time && ` - ${event.end_time}`}</span>
            </div>
          )}
          {event.location && (
            <div className="event-meta-item">
              <MapPin className="w-4 h-4" />
              <span>{event.location}</span>
            </div>
          )}
          <div className="event-meta-item">
            <Users className="w-4 h-4" />
            <span>{event.registration_count || 0} registered{event.capacity && ` / ${event.capacity}`}</span>
          </div>
        </div>
      </div>

      <div className="event-card-actions">
        <button onClick={onViewRegistrations} className="action-btn" title="View Registrations">
          <Users className="w-4 h-4" />
        </button>
        <button onClick={onEdit} className="action-btn" title="Edit">
          <Edit className="w-4 h-4" />
        </button>
        <button onClick={onDelete} className="action-btn danger" title="Delete">
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

function AddEventModal({ open, onClose, onSuccess }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [eventDate, setEventDate] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');
  const [location, setLocation] = useState('');
  const [capacity, setCapacity] = useState('');
  const [requiresRegistration, setRequiresRegistration] = useState(true);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name || !eventDate) {
      toast.error('Please enter event name and date');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/admin/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          name,
          description,
          event_date: eventDate,
          start_time: startTime || null,
          end_time: endTime || null,
          location: location || null,
          capacity: capacity ? parseInt(capacity) : null,
          requires_registration: requiresRegistration,
          is_public: true
        })
      });

      if (res.ok) {
        toast.success('Event created!');
        onSuccess();
        // Reset form
        setName('');
        setDescription('');
        setEventDate('');
        setStartTime('');
        setEndTime('');
        setLocation('');
        setCapacity('');
        setRequiresRegistration(true);
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Failed to create event');
      }
    } catch (error) {
      toast.error('Failed to create event');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="add-event-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-orange-600" />
            Create New Event
          </DialogTitle>
          <DialogDescription>
            Add an event for members to discover
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="add-event-form">
          <div className="form-group">
            <label>Event Name *</label>
            <Input
              type="text"
              placeholder="e.g., Easter Sunday Service"
              value={name}
              onChange={(e) => setName(e.target.value)}
              data-testid="event-name-input"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Date *</label>
              <Input
                type="date"
                value={eventDate}
                onChange={(e) => setEventDate(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Capacity (optional)</label>
              <Input
                type="number"
                placeholder="Max attendees"
                value={capacity}
                onChange={(e) => setCapacity(e.target.value)}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Start Time</label>
              <Input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>End Time</label>
              <Input
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Location</label>
            <Input
              type="text"
              placeholder="e.g., Main Sanctuary"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Description (optional)</label>
            <textarea
              placeholder="Brief description of the event..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="form-textarea"
              rows={2}
            />
          </div>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={requiresRegistration}
              onChange={(e) => setRequiresRegistration(e.target.checked)}
            />
            <CheckCircle className="w-4 h-4 text-orange-500" />
            Require registration
          </label>

          <div className="modal-actions">
            <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={loading || !name || !eventDate}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Create Event
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function EditEventModal({ event, open, onClose, onSuccess }) {
  const [name, setName] = useState(event.name || '');
  const [description, setDescription] = useState(event.description || '');
  const [eventDate, setEventDate] = useState(event.event_date || '');
  const [startTime, setStartTime] = useState(event.start_time || '');
  const [endTime, setEndTime] = useState(event.end_time || '');
  const [location, setLocation] = useState(event.location || '');
  const [capacity, setCapacity] = useState(event.capacity?.toString() || '');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/admin/events/${event.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          name,
          description,
          event_date: eventDate,
          start_time: startTime || null,
          end_time: endTime || null,
          location: location || null,
          capacity: capacity ? parseInt(capacity) : null
        })
      });

      if (res.ok) {
        toast.success('Event updated!');
        onSuccess();
      } else {
        toast.error('Failed to update event');
      }
    } catch (error) {
      toast.error('Failed to update event');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="edit-event-modal">
        <DialogHeader>
          <DialogTitle>Edit Event</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="edit-event-form">
          <div className="form-group">
            <label>Event Name</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Date</label>
              <Input type="date" value={eventDate} onChange={(e) => setEventDate(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Capacity</label>
              <Input type="number" value={capacity} onChange={(e) => setCapacity(e.target.value)} />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Start Time</label>
              <Input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
            </div>
            <div className="form-group">
              <label>End Time</label>
              <Input type="time" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
            </div>
          </div>

          <div className="form-group">
            <label>Location</label>
            <Input value={location} onChange={(e) => setLocation(e.target.value)} />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} className="form-textarea" rows={2} />
          </div>

          <div className="modal-actions">
            <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={loading}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save Changes'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}


function ViewRegistrationsModal({ event, open, onClose }) {
  const [registrations, setRegistrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newName, setNewName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [addLoading, setAddLoading] = useState(false);

  useEffect(() => {
    if (open) {
      fetchRegistrations();
    }
  }, [open, event.id]);

  const fetchRegistrations = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/admin/events/${event.id}/registrations`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setRegistrations(data.registrations || []);
      }
    } catch (error) {
      console.error('Failed to fetch registrations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddRegistration = async (e) => {
    e.preventDefault();
    if (!newName) {
      toast.error('Please enter a name');
      return;
    }

    setAddLoading(true);
    try {
      const res = await fetch(`${API_URL}/admin/events/${event.id}/registrations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name: newName, email: newEmail || null })
      });

      if (res.ok) {
        toast.success('Registration added');
        fetchRegistrations();
        setNewName('');
        setNewEmail('');
        setShowAddForm(false);
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Failed to add registration');
      }
    } catch (error) {
      toast.error('Failed to add registration');
    } finally {
      setAddLoading(false);
    }
  };

  const handleCancelRegistration = async (registrationId) => {
    if (!confirm('Remove this registration?')) return;

    try {
      const res = await fetch(`${API_URL}/admin/events/${event.id}/registrations/${registrationId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (res.ok) {
        toast.success('Registration removed');
        fetchRegistrations();
      } else {
        toast.error('Failed to remove registration');
      }
    } catch (error) {
      toast.error('Failed to remove registration');
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="view-registrations-modal" style={{ maxWidth: '550px' }}>
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>{event.name} - Registrations</span>
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => setShowAddForm(!showAddForm)}
            >
              <UserPlus className="w-4 h-4 mr-1" />
              Add
            </Button>
          </DialogTitle>
          <DialogDescription>
            {registrations.length} registration{registrations.length !== 1 ? 's' : ''}
            {event.capacity && ` / ${event.capacity} capacity`}
          </DialogDescription>
        </DialogHeader>

        {/* Add Registration Form */}
        {showAddForm && (
          <form onSubmit={handleAddRegistration} style={{ 
            padding: '12px', 
            background: '#f8fafc', 
            borderRadius: '8px',
            marginBottom: '12px' 
          }}>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
              <Input
                type="text"
                placeholder="Name *"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                style={{ flex: 1 }}
              />
              <Input
                type="email"
                placeholder="Email (optional)"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                style={{ flex: 1 }}
              />
            </div>
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <Button type="button" size="sm" variant="ghost" onClick={() => setShowAddForm(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm" disabled={addLoading || !newName}>
                {addLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
                Add Registration
              </Button>
            </div>
          </form>
        )}

        <div className="registrations-list" style={{ maxHeight: '350px', overflowY: 'auto' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '30px' }}>
              <Loader2 className="w-5 h-5 animate-spin inline" /> Loading registrations...
            </div>
          ) : registrations.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
              <Users className="w-12 h-12 mx-auto mb-3 opacity-40" />
              <p style={{ fontWeight: '500' }}>No registrations yet</p>
              <p style={{ fontSize: '13px' }}>Add registrations using the button above</p>
            </div>
          ) : (
            registrations.map((reg, idx) => (
              <div 
                key={reg.id || idx} 
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '12px',
                  borderBottom: '1px solid #f1f5f9',
                  gap: '12px'
                }}
              >
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: '#f97316',
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: '600',
                  fontSize: '14px'
                }}>
                  {reg.user_name?.charAt(0) || '?'}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: '500', fontSize: '14px' }}>{reg.user_name || 'Unknown'}</div>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>
                    {reg.user_email || 'No email'} • Registered {formatDate(reg.registered_at)}
                  </div>
                </div>
                {reg.registered_by_admin && (
                  <span style={{
                    fontSize: '10px',
                    padding: '2px 6px',
                    background: '#e0f2fe',
                    color: '#0369a1',
                    borderRadius: '10px'
                  }}>
                    Admin
                  </span>
                )}
                <button 
                  onClick={() => handleCancelRegistration(reg.id)}
                  style={{
                    padding: '4px',
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    color: '#94a3b8',
                    borderRadius: '4px'
                  }}
                  title="Remove registration"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
