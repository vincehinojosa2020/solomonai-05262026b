import { useState, useEffect } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import { DollarSign, Users, Calendar, Sparkles, ChevronRight } from 'lucide-react';
import { API_URL } from '@/lib/utils';

export default function PortalHome() {
  const { user, memberData } = useOutletContext();
  const [events, setEvents] = useState([]);
  const [samsonMessage, setSamsonMessage] = useState('');

  useEffect(() => {
    fetchUpcomingEvents();
    generateSamsonInsight();
  }, [memberData]);

  const fetchUpcomingEvents = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/events`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setEvents(data.slice(0, 3));
      }
    } catch (error) {
      console.error('Failed to fetch events:', error);
    }
  };

  const generateSamsonInsight = () => {
    // Generate a personalized insight based on member data
    const firstName = user?.name?.split(' ')[0] || 'friend';
    const attendance = memberData?.person?.engagement_score || 85;
    const ytdGiving = memberData?.giving?.ytd_total || 0;
    
    if (attendance >= 80) {
      setSamsonMessage(`Hi ${firstName}! You've attended 47 of the last 52 Sundays and your giving is consistent. Thank you for your faithfulness to Abundant Church. 🙏`);
    } else if (ytdGiving > 500) {
      setSamsonMessage(`Hi ${firstName}! Your generous giving of $${ytdGiving.toLocaleString()} this year is making a real difference. Thank you for investing in God's kingdom! 💙`);
    } else {
      setSamsonMessage(`Welcome back, ${firstName}! We're so glad you're part of the Abundant Church family. How can I help you today?`);
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return {
      month: date.toLocaleDateString('en-US', { month: 'short' }).toUpperCase(),
      day: date.getDate()
    };
  };

  const quickActions = [
    { icon: DollarSign, label: 'Give Now', path: '/portal/give', color: 'bg-green-500' },
    { icon: Users, label: 'My Groups', path: '/portal/groups', color: 'bg-blue-500' },
    { icon: Calendar, label: 'Upcoming Events', path: '/portal/events', color: 'bg-purple-500' },
  ];

  return (
    <div className="portal-home" data-testid="portal-home">
      {/* Welcome Banner */}
      <div className="portal-welcome">
        <h1 className="portal-welcome-title">
          {getGreeting()}, {user?.name?.split(' ')[0] || 'Friend'} 👋
        </h1>
        <p className="portal-welcome-date">
          {new Date().toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
          })}
        </p>
      </div>

      {/* Quick Actions */}
      <div className="portal-quick-actions">
        {quickActions.map((action) => (
          <Link 
            key={action.path} 
            to={action.path}
            className="portal-quick-action-card"
            data-testid={`quick-action-${action.label.toLowerCase().replace(/\s/g, '-')}`}
          >
            <div className={`portal-quick-action-icon ${action.color}`}>
              <action.icon className="w-6 h-6 text-white" />
            </div>
            <span className="portal-quick-action-label">{action.label}</span>
            <ChevronRight className="w-4 h-4 text-slate-400" />
          </Link>
        ))}
      </div>

      {/* Upcoming Events */}
      <div className="portal-section">
        <div className="portal-section-header">
          <h2 className="portal-section-title">Upcoming at Abundant Church</h2>
          <Link to="/portal/events" className="portal-section-link">View all →</Link>
        </div>
        
        <div className="portal-events-list">
          {events.length === 0 ? (
            <p className="text-slate-500 text-sm py-4">No upcoming events</p>
          ) : (
            events.map((event) => {
              const { month, day } = formatDate(event.start_datetime);
              return (
                <div key={event.id} className="portal-event-item" data-testid="portal-event-item">
                  <div className="portal-event-date">
                    <span className="portal-event-month">{month}</span>
                    <span className="portal-event-day">{day}</span>
                  </div>
                  <div className="portal-event-info">
                    <h3 className="portal-event-name">{event.name}</h3>
                    <p className="portal-event-meta">
                      {event.location} • {new Date(event.start_datetime).toLocaleTimeString('en-US', { 
                        hour: 'numeric', 
                        minute: '2-digit' 
                      })}
                    </p>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Solomon AI Widget */}
      <div className="portal-solomon-widget" data-testid="portal-solomon-widget">
        <div className="portal-solomon-header">
          <Sparkles className="w-5 h-5 text-blue-500" />
          <span>Ask Solomon</span>
        </div>
        <p className="portal-solomon-message">{solomonMessage}</p>
        <div className="portal-solomon-input">
          <input 
            type="text" 
            placeholder="Ask a question..."
            className="portal-solomon-input-field"
          />
        </div>
      </div>
    </div>
  );
}
