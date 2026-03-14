import { useState, useEffect, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import { usePolling } from '@/hooks/usePolling';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MapPin, Clock, Users, CheckCircle, Calendar as CalendarIcon,
  X, Share2, Ticket, AlertCircle, ChevronRight
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

const EVENT_CATEGORIES = [
  { id: 'all', label: 'All Events' },
  { id: 'worship', label: 'Worship' },
  { id: 'women', label: 'Women' },
  { id: 'men', label: 'Men' },
  { id: 'youth', label: 'Youth' },
  { id: 'community', label: 'Community' },
  { id: 'conferences', label: 'Conferences' },
];

export default function PortalEvents() {
  const { user, memberData, tenant } = useOutletContext();
  const [events, setEvents] = useState([]);
  const [myEvents, setMyEvents] = useState([]);
  const [filter, setFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState(null);

  useEffect(() => { fetchEvents(); fetchMyEvents(); }, []);

  // Real-time polling every 30 seconds
  const pollEvents = useCallback(() => { fetchEvents(); fetchMyEvents(); }, []);
  usePolling(pollEvents, 30000);

  const fetchEvents = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/events`, { credentials: 'include' });
      if (res.ok) setEvents(await res.json());
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const fetchMyEvents = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/my-events`, { credentials: 'include' });
      if (res.ok) { const data = await res.json(); setMyEvents(data.events || []); }
    } catch (e) { console.error(e); }
  };

  const registeredEventIds = myEvents.map(e => e.id);

  const handleRegister = async (eventId) => {
    try {
      const res = await fetch(`${API_URL}/portal/events/${eventId}/register`, {
        method: 'POST', credentials: 'include'
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message || 'Successfully registered!');
        fetchEvents(); fetchMyEvents();
      } else {
        toast.error(data.detail || 'Failed to register');
      }
    } catch { toast.error('Failed to register for event'); }
  };

  const handleCancelRegistration = async (eventId) => {
    if (!confirm('Cancel your registration for this event?')) return;
    try {
      const res = await fetch(`${API_URL}/portal/events/${eventId}/register`, {
        method: 'DELETE', credentials: 'include'
      });
      if (res.ok) { toast.success('Registration cancelled'); fetchEvents(); fetchMyEvents(); }
      else toast.error('Failed to cancel registration');
    } catch { toast.error('Failed to cancel registration'); }
  };

  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    return {
      month: d.toLocaleDateString('en-US', { month: 'short' }).toUpperCase(),
      day: d.getDate(),
      time: d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
      full: d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }),
      weekday: d.toLocaleDateString('en-US', { weekday: 'long' }),
    };
  };

  const handleShare = (event) => {
    const shareText = `I'm attending ${event.name} at ${tenant?.name || 'our church'}! Join me: `;
    if (navigator.share) {
      navigator.share({ title: event.name, text: shareText, url: window.location.href });
    } else {
      navigator.clipboard.writeText(shareText + window.location.href);
      toast.success('Link copied to clipboard!');
    }
  };

  const filterTabs = [
    { id: 'all', label: 'All' },
    { id: 'week', label: 'This Week' },
    { id: 'month', label: 'This Month' },
    { id: 'registered', label: 'My Events' },
  ];

  const filteredEvents = events.filter(event => {
    if (filter === 'registered') return registeredEventIds.includes(event.id);
    if (categoryFilter !== 'all') return event.category?.toLowerCase() === categoryFilter.toLowerCase();
    return true;
  });

  const nextMajorEvent = events.find(e => e.is_featured) || events[0];

  const getCapacityInfo = (event) => {
    if (!event.capacity) return null;
    const count = event.registration_count || 0;
    const pct = Math.min(100, Math.round((count / event.capacity) * 100));
    const isFull = count >= event.capacity;
    return { count, capacity: event.capacity, pct, isFull, waitlist: event.waitlist_count || 0 };
  };

  return (
    <div className="portal-events" data-testid="portal-events">
      {/* Hero Banner */}
      {nextMajorEvent && (
        <div className="events-hero" data-testid="events-hero">
          <div className="events-hero-overlay" />
          <div className="events-hero-content">
            <span className="events-hero-tag">Coming Up</span>
            <h1>{nextMajorEvent.name}</h1>
            <p className="events-hero-date">
              {nextMajorEvent.start_datetime ? formatDate(nextMajorEvent.start_datetime).full : nextMajorEvent.event_date ? formatDate(nextMajorEvent.event_date).full : 'TBD'}
              {nextMajorEvent.location ? ` • ${nextMajorEvent.location}` : ''}
            </p>
            {nextMajorEvent.registration_count > 0 && (
              <p className="events-hero-count">{nextMajorEvent.registration_count} people registered</p>
            )}
            <div className="events-hero-actions">
              {!registeredEventIds.includes(nextMajorEvent.id) ? (
                <button className="events-hero-btn primary" onClick={() => handleRegister(nextMajorEvent.id)} data-testid="hero-register-btn">
                  Register Now
                </button>
              ) : (
                <span className="events-hero-registered"><CheckCircle className="w-5 h-5" /> You're Registered!</span>
              )}
              <button className="events-hero-btn secondary" onClick={() => handleShare(nextMajorEvent)}>
                <Share2 className="w-4 h-4" /> Share
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="portal-page-header">
        <h2 className="portal-page-title">Upcoming Events</h2>
      </div>

      {/* Category Pills */}
      <div className="events-category-tabs">
        {EVENT_CATEGORIES.map(cat => (
          <button key={cat.id} onClick={() => setCategoryFilter(cat.id)} className={`events-cat-tab ${categoryFilter === cat.id ? 'active' : ''}`}>
            {cat.label}
          </button>
        ))}
      </div>

      {/* Filter Tabs */}
      <div className="portal-filter-tabs">
        {filterTabs.map(tab => (
          <button key={tab.id} onClick={() => setFilter(tab.id)} className={`portal-filter-tab ${filter === tab.id ? 'active' : ''}`}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Events Grid */}
      <div className="portal-events-grid">
        {loading ? (
          <p className="text-slate-500 text-sm py-8 text-center col-span-full">Loading events...</p>
        ) : filteredEvents.length === 0 ? (
          <p className="text-slate-500 text-sm py-8 text-center col-span-full">No events found.</p>
        ) : (
          filteredEvents.map((event, i) => {
            const isRegistered = registeredEventIds.includes(event.id);
            const dateInfo = event.start_datetime ? formatDate(event.start_datetime) : event.event_date ? formatDate(event.event_date) : { month: '?', day: '?', time: '' };
            const capInfo = getCapacityInfo(event);
            const tiers = event.ticket_tiers || [];

            return (
              <motion.div
                key={event.id}
                className="portal-event-card"
                data-testid={`event-card-${event.id}`}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
              >
                <div className="portal-event-date-chip">
                  <span className="portal-event-month">{dateInfo.month}</span>
                  <span className="portal-event-day">{dateInfo.day}</span>
                </div>

                <div className="portal-event-card-content">
                  <h3 className="portal-event-card-title">{event.name}</h3>

                  <div className="portal-event-card-meta">
                    {event.location && (
                      <span className="portal-event-card-info"><MapPin className="w-3.5 h-3.5" /> {event.location}</span>
                    )}
                    {(event.start_time || dateInfo.time) && (
                      <span className="portal-event-card-info"><Clock className="w-3.5 h-3.5" /> {event.start_time || dateInfo.time}</span>
                    )}
                    {event.registration_count > 0 && (
                      <span className="portal-event-card-info"><Users className="w-3.5 h-3.5" /> {event.registration_count} attending</span>
                    )}
                    {event.category && (
                      <span className="portal-event-card-info" style={{ background: '#eff6ff', color: '#3b82f6', padding: '1px 8px', borderRadius: '99px', fontSize: '11px', fontWeight: '600' }}>
                        {event.category}
                      </span>
                    )}
                  </div>

                  {/* Capacity Bar */}
                  {capInfo && (
                    <div data-testid={`event-capacity-${event.id}`} style={{ margin: '8px 0' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#64748b', fontWeight: '500', marginBottom: '4px' }}>
                        <span>{capInfo.count} / {capInfo.capacity} spots</span>
                        {capInfo.isFull && <span style={{ color: '#ef4444', fontWeight: '600' }}>FULL</span>}
                      </div>
                      <div style={{ height: '4px', background: '#e5e7eb', borderRadius: '2px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${capInfo.pct}%`, background: capInfo.isFull ? '#ef4444' : '#3b82f6', borderRadius: '2px', transition: 'width 0.3s' }} />
                      </div>
                      {capInfo.waitlist > 0 && (
                        <span style={{ fontSize: '10px', color: '#f59e0b', fontWeight: '600', marginTop: '2px', display: 'block' }}>
                          {capInfo.waitlist} on waitlist
                        </span>
                      )}
                    </div>
                  )}

                  {/* Ticket Tiers */}
                  {tiers.length > 0 && (
                    <div data-testid={`event-tiers-${event.id}`} style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', margin: '6px 0' }}>
                      {tiers.map((tier, ti) => (
                        <span key={ti} style={{
                          fontSize: '10px', fontWeight: '600', padding: '2px 8px', borderRadius: '99px',
                          background: tier.price === 0 ? '#f0fdf4' : tier.name?.toLowerCase().includes('vip') ? '#fef3c7' : '#f1f5f9',
                          color: tier.price === 0 ? '#16a34a' : tier.name?.toLowerCase().includes('vip') ? '#d97706' : '#475569',
                        }}>
                          <Ticket className="w-3 h-3 inline mr-0.5" style={{ verticalAlign: '-2px' }} />
                          {tier.name}{tier.price > 0 ? ` $${tier.price}` : ' Free'}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Actions */}
                  <div className="portal-event-card-actions">
                    {isRegistered ? (
                      <>
                        <span className="portal-registered-badge"><CheckCircle className="w-4 h-4" /> Registered</span>
                        <button onClick={() => handleCancelRegistration(event.id)} className="portal-event-btn secondary" style={{ color: '#dc2626' }}>
                          <X className="w-3 h-3" /> Cancel
                        </button>
                      </>
                    ) : (
                      <>
                        <button className="portal-event-btn secondary" onClick={() => setSelectedEvent(event)}>View Details</button>
                        {(event.registration_required || event.requires_registration) && (
                          <button onClick={() => handleRegister(event.id)} className="portal-event-btn primary" data-testid={`register-event-${event.id}`}>
                            {capInfo?.isFull ? 'Join Waitlist' : 'Register'}
                          </button>
                        )}
                      </>
                    )}
                    <button onClick={() => handleShare(event)} style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: '4px' }}>
                      <Share2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </motion.div>
            );
          })
        )}
      </div>

      {/* Event Detail Modal */}
      <AnimatePresence>
        {selectedEvent && (
          <motion.div
            className="fixed inset-0 z-[9998] flex items-center justify-center p-4"
            style={{ background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setSelectedEvent(null)}
          >
            <motion.div
              className="bg-white rounded-2xl w-full max-w-lg overflow-hidden"
              initial={{ y: 30, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 30, opacity: 0 }}
              onClick={e => e.stopPropagation()}
              data-testid="event-detail-modal"
            >
              {/* Modal Header */}
              <div style={{ background: '#0f172a', padding: '24px', color: '#fff', position: 'relative' }}>
                <button onClick={() => setSelectedEvent(null)} style={{ position: 'absolute', top: '12px', right: '12px', background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '50%', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: '#fff' }}>
                  <X className="w-4 h-4" />
                </button>
                {selectedEvent.category && (
                  <span style={{ fontSize: '11px', background: 'rgba(59,130,246,0.2)', color: '#93c5fd', padding: '2px 10px', borderRadius: '99px', fontWeight: '600' }}>{selectedEvent.category}</span>
                )}
                <h2 style={{ fontSize: '20px', fontWeight: '700', margin: '8px 0 4px' }}>{selectedEvent.name}</h2>
                <p style={{ fontSize: '13px', color: '#94a3b8' }}>
                  {selectedEvent.event_date ? formatDate(selectedEvent.event_date).full : 'TBD'}
                  {selectedEvent.location ? ` • ${selectedEvent.location}` : ''}
                </p>
              </div>

              <div style={{ padding: '20px' }}>
                {selectedEvent.description && (
                  <p style={{ fontSize: '14px', color: '#475569', lineHeight: 1.6, marginBottom: '16px' }}>{selectedEvent.description}</p>
                )}

                {/* Details */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '16px' }}>
                  {selectedEvent.start_time && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: '#475569' }}>
                      <Clock className="w-4 h-4" style={{ color: '#3b82f6' }} /> {selectedEvent.start_time}{selectedEvent.end_time ? ` - ${selectedEvent.end_time}` : ''}
                    </div>
                  )}
                  {selectedEvent.location && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: '#475569' }}>
                      <MapPin className="w-4 h-4" style={{ color: '#3b82f6' }} /> {selectedEvent.location}
                    </div>
                  )}
                  {selectedEvent.registration_count > 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: '#475569' }}>
                      <Users className="w-4 h-4" style={{ color: '#3b82f6' }} /> {selectedEvent.registration_count} registered
                    </div>
                  )}
                </div>

                {/* Capacity in modal */}
                {(() => {
                  const cap = getCapacityInfo(selectedEvent);
                  if (!cap) return null;
                  return (
                    <div style={{ background: '#f8fafc', borderRadius: '10px', padding: '12px', marginBottom: '16px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: '600', marginBottom: '6px' }}>
                        <span style={{ color: '#475569' }}>{cap.count} / {cap.capacity} spots filled</span>
                        {cap.isFull && <span style={{ color: '#ef4444' }}>Event Full</span>}
                      </div>
                      <div style={{ height: '6px', background: '#e5e7eb', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${cap.pct}%`, background: cap.isFull ? '#ef4444' : '#3b82f6', borderRadius: '3px' }} />
                      </div>
                      {cap.waitlist > 0 && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '6px', fontSize: '11px', color: '#f59e0b', fontWeight: '600' }}>
                          <AlertCircle className="w-3 h-3" /> {cap.waitlist} on waitlist
                        </div>
                      )}
                    </div>
                  );
                })()}

                {/* Ticket Tiers in modal */}
                {(selectedEvent.ticket_tiers || []).length > 0 && (
                  <div style={{ marginBottom: '16px' }}>
                    <h4 style={{ fontSize: '13px', fontWeight: '600', color: '#0f172a', marginBottom: '8px' }}>Ticket Options</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {selectedEvent.ticket_tiers.map((tier, i) => (
                        <div key={i} style={{
                          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                          padding: '10px 12px', borderRadius: '8px',
                          border: '1px solid #e5e7eb', background: '#fff',
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Ticket className="w-4 h-4" style={{ color: tier.name?.toLowerCase().includes('vip') ? '#d97706' : '#3b82f6' }} />
                            <div>
                              <div style={{ fontSize: '13px', fontWeight: '600', color: '#0f172a' }}>{tier.name}</div>
                              {tier.description && <div style={{ fontSize: '11px', color: '#94a3b8' }}>{tier.description}</div>}
                            </div>
                          </div>
                          <span style={{ fontSize: '14px', fontWeight: '700', color: tier.price === 0 ? '#16a34a' : '#0f172a' }}>
                            {tier.price === 0 ? 'Free' : `$${tier.price}`}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Register Button */}
                {!registeredEventIds.includes(selectedEvent.id) ? (
                  (selectedEvent.registration_required || selectedEvent.requires_registration) && (
                    <button
                      data-testid="modal-register-btn"
                      onClick={() => { handleRegister(selectedEvent.id); setSelectedEvent(null); }}
                      style={{
                        width: '100%', padding: '12px', background: '#3b82f6', color: '#fff',
                        border: 'none', borderRadius: '10px', fontSize: '14px', fontWeight: '600', cursor: 'pointer',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                      }}
                    >
                      {getCapacityInfo(selectedEvent)?.isFull ? (
                        <><AlertCircle className="w-4 h-4" /> Join Waitlist</>
                      ) : (
                        <><CheckCircle className="w-4 h-4" /> Register Now</>
                      )}
                    </button>
                  )
                ) : (
                  <div style={{ textAlign: 'center', padding: '12px', background: '#f0fdf4', borderRadius: '10px', color: '#16a34a', fontWeight: '600', fontSize: '14px' }}>
                    <CheckCircle className="w-4 h-4 inline mr-1" style={{ verticalAlign: '-2px' }} /> You're Registered!
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
