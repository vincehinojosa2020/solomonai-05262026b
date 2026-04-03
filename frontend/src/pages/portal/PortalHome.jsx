import { useState, useEffect, useCallback } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import { usePolling } from '@/hooks/usePolling';
import { DollarSign, Users, Calendar, ChevronRight, Flame, GraduationCap, ExternalLink, Coffee, Heart } from 'lucide-react';
import { API_URL, formatCurrency } from '@/lib/utils';
import { ServiceModeBanner, AttendanceStreakCard } from '@/components/ServiceMode';
import { toast } from 'sonner';

export default function PortalHome() {
  const { user, memberData, tenant } = useOutletContext();
  const [events, setEvents] = useState([]);
  const [solomonMessage, setSolomonMessage] = useState('');
  
  // Service Mode State
  const [serviceMode, setServiceMode] = useState(null);
  const [streakData, setStreakData] = useState(null);
  const [nextSteps, setNextSteps] = useState(null);
  const [checkinNudge, setCheckinNudge] = useState(null);

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
      const res = await fetch(`${API_URL}/portal/events`);
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
      const res = await fetch(`${API_URL}/portal/service-mode`);
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
      const res = await fetch(`${API_URL}/portal/attendance-streak`);
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
      const res = await fetch(`${API_URL}/portal/next-steps/status`);
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
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message || 'Checked in!');
        // Show arrival nudge if available
        if (data.nudge && data.nudge.show) {
          setCheckinNudge({
            ...data.nudge,
            streak: data.streak,
            churchName: tenant?.name || 'your church',
          });
        }
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

      {/* Arrival Welcome Card — shows after check-in with nudge */}
      {checkinNudge && (
        <div className="arrival-nudge-card" data-testid="arrival-nudge-card">
          <div className="arrival-nudge-header">
            <span className="arrival-welcome-text">Welcome to {checkinNudge.churchName}!</span>
            <button className="arrival-dismiss" onClick={() => setCheckinNudge(null)}>Dismiss</button>
          </div>
          {checkinNudge.streak && (
            <div className="arrival-streak">
              <Flame className="w-4 h-4" style={{ color: '#f97316' }} />
              <span>{checkinNudge.streak.current} week streak!</span>
            </div>
          )}
          <div className="arrival-actions">
            {checkinNudge.cafe_open && (
              <Link to="/portal/cafe" className="arrival-action-btn cafe" data-testid="nudge-order-coffee">
                <Coffee className="w-5 h-5" />
                <div>
                  <span className="arrival-action-title">Order your coffee</span>
                  <span className="arrival-action-sub">{checkinNudge.cafe_message}</span>
                </div>
                <ChevronRight className="w-4 h-4" />
              </Link>
            )}
            {checkinNudge.show_giving && (
              <div className="arrival-giving" data-testid="nudge-give-today">
                <div className="arrival-giving-header">
                  <Heart className="w-4 h-4" style={{ color: '#ec4899' }} />
                  <span>{checkinNudge.give_message}</span>
                </div>
                <div className="arrival-giving-amounts">
                  {(checkinNudge.give_amounts || [25, 50, 100, 250]).map((amt) => (
                    <Link
                      key={amt}
                      to={`/portal/give?amount=${amt}`}
                      className="arrival-give-btn"
                    >
                      ${amt}
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Welcome Banner */}
      <div className="portal-welcome">
        <h1 className="portal-welcome-title">
          {getGreeting()}, {user?.name?.split(' ')[0] || 'Friend'}
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

      <div className="portal-home-grid" style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '16px' }}>
        {/* Membership Journey — expanded */}
        {nextSteps && (
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm" data-testid="home-next-steps-card">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold text-blue-700 uppercase tracking-wide" data-testid="home-next-steps-label">Membership Journey</p>
                <h3 className="text-lg font-semibold text-slate-900 mt-1" data-testid="home-next-steps-title">Abundant Next Steps</h3>
                <p className="text-sm text-slate-600 mt-1" data-testid="home-next-steps-status">
                  {nextSteps.completion_percent || 0}% complete
                </p>
              </div>
              <GraduationCap className="w-5 h-5 text-blue-600" />
            </div>
            <div className="h-3 w-full rounded-full bg-slate-100 overflow-hidden mt-4" data-testid="home-next-steps-progress-bar">
              <div className="h-full bg-blue-600 transition-[width] duration-500 rounded-full" style={{ width: `${nextSteps.completion_percent || 0}%` }} />
            </div>
            {nextSteps.steps && nextSteps.steps.length > 0 && (
              <div className="mt-4 space-y-2">
                {nextSteps.steps.slice(0, 4).map((step, i) => (
                  <div key={`item-${i}`} className="flex items-center gap-3 text-sm">
                    <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${step.completed ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-100 text-slate-400'}`}>
                      {step.completed ? <Heart className="w-3 h-3" /> : <span className="text-xs font-bold">{i + 1}</span>}
                    </div>
                    <span className={step.completed ? 'text-slate-500 line-through' : 'text-slate-800 font-medium'}>{step.name || step.title}</span>
                  </div>
                ))}
              </div>
            )}
            <div className="mt-5 flex flex-wrap gap-2">
              <Link
                to="/portal/pathways"
                className="inline-flex items-center gap-2 rounded-full bg-slate-900 text-white px-5 py-2.5 text-sm font-semibold hover:bg-slate-800 transition-colors"
                data-testid="home-next-steps-open-pathways"
              >
                Continue Track
                <ChevronRight className="w-4 h-4" />
              </Link>
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
                <Link key={event.id} to={`/portal/events/${event.id}`} className="portal-event-item" data-testid="portal-event-item" style={{ textDecoration: 'none', color: 'inherit', cursor: 'pointer' }}>
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
                  <ChevronRight className="w-4 h-4 text-slate-300" />
                </Link>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
