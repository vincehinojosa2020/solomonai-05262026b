import { useState, useEffect } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import { DollarSign, Users, Calendar, Sparkles, ChevronRight, MessageSquare } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

const NOTE_CATEGORIES = ['Prayer Request', 'Question', 'Praise', 'Other'];

export default function PortalHome() {
  const { user, memberData, tenant } = useOutletContext();
  const [events, setEvents] = useState([]);
  const [solomonMessage, setSolomonMessage] = useState('');
  const [noteSubject, setNoteSubject] = useState('');
  const [noteMessage, setNoteMessage] = useState('');
  const [noteCategory, setNoteCategory] = useState('');
  const [noteSubmitting, setNoteSubmitting] = useState(false);

  useEffect(() => {
    fetchUpcomingEvents();
    generateSolomonInsight();
  }, [memberData, tenant]);

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

  const getChurchName = () => {
    return tenant?.name || 'Abundant Church';
  };

  const generateSolomonInsight = () => {
    const firstName = user?.name?.split(' ')[0] || 'friend';
    const attendance = memberData?.person?.engagement_score || 85;
    const ytdGiving = memberData?.giving?.ytd_total || 0;
    const churchName = getChurchName();
    
    if (attendance >= 80) {
      setSolomonMessage(`Hi ${firstName}! You've attended 47 of the last 52 Sundays and your giving is consistent. Thank you for your faithfulness to ${churchName}. 🙏`);
    } else if (ytdGiving > 500) {
      setSolomonMessage(`Hi ${firstName}! Your generous giving of $${ytdGiving.toLocaleString()} this year is making a real difference. Thank you for investing in God's kingdom! 💙`);
    } else {
      setSolomonMessage(`Welcome back, ${firstName}! We're so glad you're part of the ${churchName} family. How can I help you today?`);
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

  const openSolomon = () => {
    window.dispatchEvent(new Event('solomon:open'));
  };

  const handleSubmitNote = async (event) => {
    event.preventDefault();
    if (!noteSubject.trim()) {
      toast.error('Subject is required');
      return;
    }
    if (!noteMessage.trim()) {
      toast.error('Message is required');
      return;
    }

    setNoteSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/portal/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          subject: noteSubject.trim(),
          message: noteMessage.trim(),
          category: noteCategory || null
        })
      });
      if (res.ok) {
        toast.success('Your note was sent');
        setNoteSubject('');
        setNoteMessage('');
        setNoteCategory('');
      } else {
        toast.error('Unable to send note');
      }
    } catch (error) {
      toast.error('Unable to send note');
    } finally {
      setNoteSubmitting(false);
    }
  };

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

      <div className="portal-home-grid">
        {/* Ask Solomon */}
        <div className="portal-solomon-widget" data-testid="portal-solomon-widget">
          <div className="portal-solomon-header">
            <Sparkles className="w-5 h-5 text-blue-500" />
            <span>Ask Solomon</span>
          </div>
          <p className="portal-solomon-message">{solomonMessage}</p>
          <div className="portal-solomon-input">
            <input 
              type="text" 
              placeholder="Ask about giving, groups, Pathways, Thinkific..."
              className="portal-solomon-input-field"
              onFocus={openSolomon}
              data-testid="ask-solomon-input"
            />
            <button
              className="portal-solomon-button"
              onClick={openSolomon}
              data-testid="ask-solomon-open-btn"
            >
              Open
            </button>
          </div>
        </div>

        {/* Leave a Note */}
        <form className="portal-note-card" onSubmit={handleSubmitNote} data-testid="leave-note-card">
          <div className="portal-note-header">
            <MessageSquare className="w-5 h-5 text-indigo-500" />
            <div>
              <h3>Leave a Note</h3>
              <p>Send a message to church leadership or share a prayer request.</p>
            </div>
          </div>
          <input
            type="text"
            value={noteSubject}
            onChange={(event) => setNoteSubject(event.target.value)}
            placeholder="Subject"
            className="portal-note-input"
            data-testid="leave-note-subject-input"
          />
          <select
            value={noteCategory}
            onChange={(event) => setNoteCategory(event.target.value)}
            className="portal-note-select"
            data-testid="leave-note-category-select"
          >
            <option value="">Optional category</option>
            {NOTE_CATEGORIES.map((category) => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
          <textarea
            value={noteMessage}
            onChange={(event) => setNoteMessage(event.target.value)}
            placeholder="Write your note..."
            rows={4}
            className="portal-note-textarea"
            data-testid="leave-note-message-input"
          />
          <button
            type="submit"
            className="portal-note-submit"
            disabled={noteSubmitting}
            data-testid="leave-note-submit-button"
          >
            {noteSubmitting ? 'Sending...' : 'Send Note'}
          </button>
        </form>
      </div>

      {/* Upcoming Events */}
      <div className="portal-section">
        <div className="portal-section-header">
          <h2 className="portal-section-title">Upcoming at {getChurchName()}</h2>
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
    </div>
  );
}
