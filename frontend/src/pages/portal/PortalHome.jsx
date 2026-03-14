import { useState, useEffect, useCallback } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import { usePolling } from '@/hooks/usePolling';
import { DollarSign, Users, Calendar, ChevronRight, Flame, GraduationCap, ExternalLink } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { ServiceModeBanner, AttendanceStreakCard } from '@/components/ServiceMode';

export default function PortalHome() {
  const { user, memberData, tenant } = useOutletContext();
  const [events, setEvents] = useState([]);
  const [solomonMessage, setSolomonMessage] = useState('');
  
  // Service Mode State
  const [serviceMode, setServiceMode] = useState(null);
  const [streakData, setStreakData] = useState(null);
  const [nextSteps, setNextSteps] = useState(null);

  useEffect(() => {
    fetchUpcomingEvents();
    generateSolomonInsight();
    fetchServiceMode();
    fetchStreakData();
    fetchNextSteps();
  }, [memberData, tenant]);

  // Real-time polling every 30 seconds
  const pollHome = useCallback(() => {
    fetchUpcomingEvents(); fetchServiceMode(); fetchStreakData(); fetchNextSteps();
  }, [memberData, tenant]);
  usePolling(pollHome, 30000);

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

  const fetchNextSteps = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/next-steps/status`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setNextSteps(data);
      }
    } catch (error) {
      console.error('Failed to fetch next steps:', error);
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
    if (!dateStr) return { month: 'TBD', day: '-' };
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return { month: 'TBD', day: '-' };
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
        {/* Attendance Streak Card */}
        {streakData && (
          <AttendanceStreakCard
            currentStreak={streakData.current_streak}
            longestStreak={streakData.longest_streak}
            totalAttended={streakData.total_attended}
            badges={streakData.streak_badges}
          />
        )}

        {/* Next Steps Membership Journey */}
        {nextSteps && (
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" data-testid="home-next-steps-card">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold text-blue-700 uppercase tracking-wide" data-testid="home-next-steps-label">Membership Journey</p>
                <h3 className="text-lg font-semibold text-slate-900 mt-1" data-testid="home-next-steps-title">Abundant Next Steps</h3>
                <p className="text-sm text-slate-600 mt-1" data-testid="home-next-steps-status">
                  {nextSteps.completion_percent || 0}% complete • {nextSteps.approval_status?.replaceAll('_', ' ') || 'in progress'}
                </p>
              </div>
              <GraduationCap className="w-5 h-5 text-blue-600" />
            </div>
            <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden mt-4" data-testid="home-next-steps-progress-bar">
              <div className="h-full bg-blue-600 transition-[width] duration-500" style={{ width: `${nextSteps.completion_percent || 0}%` }} />
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link
                to="/portal/pathways"
                className="inline-flex items-center gap-2 rounded-full bg-slate-900 text-white px-4 py-2 text-sm font-semibold"
                data-testid="home-next-steps-open-pathways"
              >
                Continue Track
                <ChevronRight className="w-4 h-4" />
              </Link>
              <a
                href={nextSteps.thinkific_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700"
                data-testid="home-next-steps-open-thinkific"
              >
                Thinkific Course
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </div>
        )}
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
              const { month, day } = formatDate(event.start_datetime || event.event_date);
              return (
                <div key={event.id} className="portal-event-item" data-testid="portal-event-item">
                  <div className="portal-event-date">
                    <span className="portal-event-month">{month}</span>
                    <span className="portal-event-day">{day}</span>
                  </div>
                  <div className="portal-event-info">
                    <h3 className="portal-event-name">{event.name}</h3>
                    <p className="portal-event-meta">
                      {event.location || 'TBD'} {(event.start_datetime || event.start_time) ? '• ' + (event.start_time || new Date(event.start_datetime).toLocaleTimeString('en-US', { 
                        hour: 'numeric', 
                        minute: '2-digit' 
                      })) : ''}
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
