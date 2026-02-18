import { useState, useEffect } from 'react';
import { Calendar, MapPin, Users, Plus, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { API_URL, formatDateTime } from '@/lib/utils';

const EventCard = ({ event }) => {
  const startDate = new Date(event.start_datetime);
  
  return (
    <div className="bg-white border border-slate-200 rounded-lg overflow-hidden hover:border-blue-200 hover:shadow-sm transition-all" data-testid={`event-${event.id}`}>
      {event.cover_image_url && (
        <img src={event.cover_image_url} alt="" className="w-full h-32 object-cover" />
      )}
      <div className="p-5">
        <div className="flex items-start gap-4">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-3 text-center text-white min-w-[60px]">
            <p className="text-xs font-semibold uppercase">
              {startDate.toLocaleDateString('en-US', { month: 'short' })}
            </p>
            <p className="text-2xl font-bold">{startDate.getDate()}</p>
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-slate-900">{event.name}</h3>
            {event.description && (
              <p className="text-sm text-slate-500 mt-1 line-clamp-2">{event.description}</p>
            )}
            <div className="flex items-center gap-4 mt-3 text-xs text-slate-400">
              {event.location && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {event.location}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {startDate.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
              </span>
              {event.registration_required && (
                <span className="flex items-center gap-1">
                  <Users className="w-3 h-3" />
                  {event.registration_count} registered
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 mt-4 pt-4 border-t border-slate-100">
          <Button variant="outline" size="sm" className="flex-1">View Details</Button>
          {event.registration_required && (
            <Button size="sm" className="btn-primary flex-1">Register</Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default function EventsPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const response = await fetch(`${API_URL}/events?upcoming=true&limit=20`);
      const data = await response.json();
      setEvents(data);
    } catch (error) {
      console.error('Failed to fetch events:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="events-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Events</h1>
          <p className="page-subtitle">Manage church events and registrations</p>
        </div>
        <Button className="h-9 btn-primary" data-testid="create-event-btn">
          <Plus className="w-4 h-4 mr-2" />
          Create Event
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Upcoming Events</p>
          <p className="text-2xl font-bold font-data text-slate-900">{events.length}</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">This Week</p>
          <p className="text-2xl font-bold font-data text-slate-900">
            {events.filter(e => {
              const date = new Date(e.start_datetime);
              const now = new Date();
              const weekFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
              return date >= now && date <= weekFromNow;
            }).length}
          </p>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Total Registrations</p>
          <p className="text-2xl font-bold font-data text-slate-900">
            {events.reduce((acc, e) => acc + (e.registration_count || 0), 0)}
          </p>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Public Events</p>
          <p className="text-2xl font-bold font-data text-slate-900">
            {events.filter(e => e.is_public).length}
          </p>
        </div>
      </div>

      {/* Events Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-64 bg-slate-100 rounded-lg animate-pulse"></div>
          ))}
        </div>
      ) : events.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-lg p-12 text-center">
          <Calendar className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="font-semibold text-slate-900 mb-2">No upcoming events</h3>
          <p className="text-slate-400 text-sm mb-4">Create your first event to get started</p>
          <Button className="btn-primary">Create Event</Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {events.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      )}
    </div>
  );
}
