import { useState, useEffect } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import { DollarSign, Users, Calendar, Sparkles, ChevronRight, MessageSquare, Heart, Flame, Play } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import { ServiceModeBanner, AttendanceStreakCard, PrayerWallCard } from '@/components/ServiceMode';

const NOTE_CATEGORIES = ['Prayer Request', 'Question', 'Praise', 'Other'];

export default function PortalHome() {
  const { user, memberData, tenant } = useOutletContext();
  const [events, setEvents] = useState([]);
  const [solomonMessage, setSolomonMessage] = useState('');
  const [noteSubject, setNoteSubject] = useState('');
  const [noteMessage, setNoteMessage] = useState('');
  const [noteCategory, setNoteCategory] = useState('');
  const [noteSubmitting, setNoteSubmitting] = useState(false);
  
  // Service Mode State
  const [serviceMode, setServiceMode] = useState(null);
  const [streakData, setStreakData] = useState(null);
  const [prayerWall, setPrayerWall] = useState([]);

  useEffect(() => {
    fetchUpcomingEvents();
    generateSolomonInsight();
    fetchServiceMode();
    fetchStreakData();
    fetchPrayerWall();
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

  const fetchServiceMode = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/service-mode`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setServiceMode(data);
      }
    } catch (error) {
      console.error('Failed to fetch service mode:', error);
    }
  };

  const fetchStreakData = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/attendance-streak`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setStreakData(data);
      }
    } catch (error) {
      console.error('Failed to fetch streak data:', error);
    }
  };

  const fetchPrayerWall = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/prayer/wall`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setPrayerWall(data.requests || []);
      }
    } catch (error) {
      console.error('Failed to fetch prayer wall:', error);
    }
  };

  const handleServiceCheckIn = async (checkInType) => {
    try {
      const res = await fetch(`${API_URL}/portal/service-checkin?check_in_type=${checkInType}`, {
        method: 'POST',
        credentials: 'include'
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message);
        // Refresh service mode
        fetchServiceMode();
        fetchStreakData();
      } else {
        toast.error('Check-in failed');
      }
    } catch (error) {
      toast.error('Error during check-in');
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
      {/* Service Mode Banner - Shows on service days */}
      {serviceMode && (serviceMode.is_service_day || serviceMode.is_service_time) && (
        <ServiceModeBanner
          isServiceDay={serviceMode.is_service_day}
          isServiceTime={serviceMode.is_service_time}
          currentService={serviceMode.current_service}
          nextService={serviceMode.next_service}
          checkInStatus={serviceMode.check_in_status}
          onCheckIn={handleServiceCheckIn}
          streak={serviceMode.attendance_streak}
        />
      )}

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
        {/* Streak Badge on Welcome */}
        {streakData && streakData.current_streak > 0 && (
          <div className="portal-streak-badge" data-testid="home-streak-badge">
            <Flame className="w-4 h-4" />
            <span>{streakData.current_streak} Week Streak!</span>
          </div>
        )}
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

        {/* Attendance Streak Card */}
        {streakData && (
          <AttendanceStreakCard
            currentStreak={streakData.current_streak}
            longestStreak={streakData.longest_streak}
            totalAttended={streakData.total_attended}
            badges={streakData.streak_badges}
          />
        )}

        {/* Prayer Wall Preview */}
        <PrayerWallCard
          requests={prayerWall}
          onViewAll={() => window.location.href = '/portal/prayer'}
        />
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
