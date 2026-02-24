import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { MapPin, Clock, Users, CheckCircle, Calendar as CalendarIcon, X } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

export default function PortalEvents() {
  const { user, memberData } = useOutletContext();
  const [events, setEvents] = useState([]);
  const [myEvents, setMyEvents] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEvents();
    fetchMyEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/events`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setEvents(data);
      }
    } catch (error) {
      console.error('Failed to fetch events:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMyEvents = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/my-events`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setMyEvents(data.events || []);
      }
    } catch (error) {
      console.error('Failed to fetch my events:', error);
    }
  };

  const registeredEventIds = myEvents.map(e => e.id);

  const handleRegister = async (eventId) => {
    try {
      const res = await fetch(`${API_URL}/portal/events/${eventId}/register`, {
        method: 'POST',
        credentials: 'include'
      });
      
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message || 'Successfully registered!');
        fetchEvents();
        fetchMyEvents();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Failed to register');
      }
    } catch (error) {
      toast.error('Failed to register for event');
    }
  };

  const handleCancelRegistration = async (eventId) => {
    if (!confirm('Cancel your registration for this event?')) return;
    
    try {
      const res = await fetch(`${API_URL}/portal/events/${eventId}/register`, {
        method: 'DELETE',
        credentials: 'include'
      });
      
      if (res.ok) {
        toast.success('Registration cancelled');
        fetchEvents();
        fetchMyEvents();
      } else {
        toast.error('Failed to cancel registration');
      }
    } catch (error) {
      toast.error('Failed to cancel registration');
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return {
      month: date.toLocaleDateString('en-US', { month: 'short' }).toUpperCase(),
      day: date.getDate(),
      time: date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
      full: date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
    };
  };

  const filterTabs = [
    { id: 'all', label: 'All' },
    { id: 'week', label: 'This Week' },
    { id: 'month', label: 'This Month' },
    { id: 'registered', label: 'My Registrations' },
  ];

  const filteredEvents = events.filter(event => {
    if (filter === 'registered') {
      return registeredEventIds.includes(event.id);
    }
    // For now, show all events for other filters
    return true;
  });

  const EventCard = ({ event }) => {
    const isRegistered = registeredEventIds.includes(event.id);
    const dateInfo = event.start_datetime ? formatDate(event.start_datetime) : 
                     event.event_date ? formatDate(event.event_date) : { month: '?', day: '?', time: '' };

    return (
      <div className="portal-event-card" data-testid={`event-card-${event.id}`}>
        <div className="portal-event-date-chip">
          <span className="portal-event-month">{dateInfo.month}</span>
          <span className="portal-event-day">{dateInfo.day}</span>
        </div>
        
        <div className="portal-event-card-content">
          <h3 className="portal-event-card-title">{event.name}</h3>
          
          <div className="portal-event-card-meta">
            {event.location && (
              <span className="portal-event-card-info">
                <MapPin className="w-3.5 h-3.5" />
                {event.location}
              </span>
            )}
            {(event.start_time || dateInfo.time) && (
              <span className="portal-event-card-info">
                <Clock className="w-3.5 h-3.5" />
                {event.start_time || dateInfo.time}
              </span>
            )}
            {event.registration_count > 0 && (
              <span className="portal-event-card-info">
                <Users className="w-3.5 h-3.5" />
                {event.registration_count} registered
              </span>
            )}
          </div>

          <div className="portal-event-card-actions">
            {isRegistered ? (
              <>
                <span className="portal-registered-badge">
                  <CheckCircle className="w-4 h-4" />
                  Registered ✓
                </span>
                <button 
                  onClick={() => handleCancelRegistration(event.id)}
                  className="portal-event-btn secondary"
                  style={{ color: '#dc2626' }}
                >
                  <X className="w-3 h-3" />
                  Cancel
                </button>
              </>
            ) : (
              <>
                <button className="portal-event-btn secondary">View Details</button>
                {(event.registration_required || event.requires_registration) && (
                  <button 
                    onClick={() => handleRegister(event.id)}
                    className="portal-event-btn primary"
                  >
                    Register
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="portal-events" data-testid="portal-events">
      <div className="portal-page-header">
        <h1 className="portal-page-title">Events at Abundant Church</h1>
      </div>

      {/* Filter Tabs */}
      <div className="portal-filter-tabs">
        {filterTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setFilter(tab.id)}
            className={`portal-filter-tab ${filter === tab.id ? 'active' : ''}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Events Grid */}
      <div className="portal-events-grid">
        {filteredEvents.length === 0 ? (
          <p className="text-slate-500 text-sm py-8 text-center col-span-full">
            No events found.
          </p>
        ) : (
          filteredEvents.map((event) => (
            <EventCard key={event.id} event={event} />
          ))
        )}
      </div>
    </div>
  );
}
