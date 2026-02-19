import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { MapPin, Clock, Users, CheckCircle, Calendar as CalendarIcon } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

export default function PortalEvents() {
  const { user, memberData } = useOutletContext();
  const [events, setEvents] = useState([]);
  const [filter, setFilter] = useState('all');
  const [registeredEvents, setRegisteredEvents] = useState(['event_sunday_service', 'event_womens_conf']);

  useEffect(() => {
    fetchEvents();
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
    }
  };

  const handleRegister = (eventId) => {
    setRegisteredEvents([...registeredEvents, eventId]);
    toast.success('Successfully registered for the event!');
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
    { id: 'registered', label: 'Registered' },
  ];

  const filteredEvents = events.filter(event => {
    if (filter === 'registered') {
      return registeredEvents.includes(event.id);
    }
    // For now, show all events for other filters
    return true;
  });

  const EventCard = ({ event }) => {
    const isRegistered = registeredEvents.includes(event.id);
    const { month, day, time, full } = formatDate(event.start_datetime);

    return (
      <div className="portal-event-card" data-testid={`event-card-${event.id}`}>
        <div className="portal-event-date-chip">
          <span className="portal-event-month">{month}</span>
          <span className="portal-event-day">{day}</span>
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
            <span className="portal-event-card-info">
              <Clock className="w-3.5 h-3.5" />
              {time}
            </span>
            {event.registration_count > 0 && (
              <span className="portal-event-card-info">
                <Users className="w-3.5 h-3.5" />
                {event.registration_count} registered
              </span>
            )}
          </div>

          <div className="portal-event-card-actions">
            {isRegistered ? (
              <span className="portal-registered-badge">
                <CheckCircle className="w-4 h-4" />
                Registered ✓
              </span>
            ) : (
              <>
                <button className="portal-event-btn secondary">View Details</button>
                {event.registration_required && (
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
