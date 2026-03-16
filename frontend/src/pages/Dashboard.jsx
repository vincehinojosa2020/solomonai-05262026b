import { useState, useEffect, useCallback } from 'react';
import { useOutletContext, Link, useNavigate } from 'react-router-dom';
import { usePolling } from '@/hooks/usePolling';
import { 
  Users, UsersRound, Calendar, DollarSign, TrendingUp, 
  ArrowUpRight, ArrowDownRight, RefreshCw, Video, ExternalLink, 
  CalendarCheck, AlertCircle, ShieldCheck, CircleAlert, CircleCheckBig
} from 'lucide-react';
import { 
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer
} from 'recharts';
import { Progress } from '@/components/ui/progress';
import { API_URL, formatCurrency, formatNumber, formatRelativeTime } from '@/lib/utils';

const StatCard = ({ title, value, change, changeType, icon: Icon }) => (
  <div className="stat-card" data-testid={`stat-${title.toLowerCase().replace(/\s+/g, '-')}`}>
    <div className="flex items-start justify-between">
      <div>
        <p className="stat-label">{title}</p>
        <p className="stat-value">{value}</p>
        {change && (
          <p className={`stat-change ${changeType}`}>
            {changeType === 'positive' ? (
              <ArrowUpRight className="w-3 h-3 inline mr-1" />
            ) : (
              <ArrowDownRight className="w-3 h-3 inline mr-1" />
            )}
            {change}
          </p>
        )}
      </div>
      <div className="p-2 bg-slate-100">
        <Icon className="w-4 h-4 text-slate-500" />
      </div>
    </div>
  </div>
);

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="custom-tooltip">
        <p className="label">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} className="value" style={{ color: entry.color }}>
            {entry.name}: {typeof entry.value === 'number' && entry.value > 100 
              ? formatCurrency(entry.value) 
              : formatNumber(entry.value)}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const ActivityItem = ({ activity }) => {
  const getActivityType = (action) => {
    if (!action) return 'event';
    if (action.includes('member') || action.includes('person') || action.includes('registration')) return 'member';
    if (action.includes('donation') || action.includes('giving')) return 'donation';
    if (action.includes('group')) return 'group';
    return 'event';
  };

  return (
    <div className="activity-item" data-testid="activity-item">
      <div className={`activity-dot ${getActivityType(activity.action || activity.type || '')}`}></div>
      <div className="flex-1 min-w-0">
        <p className="activity-text">{activity.description || activity.message || ''}</p>
        <p className="activity-time">{formatRelativeTime(activity.created_at)}</p>
      </div>
    </div>
  );
};

const EventCard = ({ event }) => {
  const date = new Date(event.start_datetime);
  return (
    <div className="event-card" data-testid="event-card">
      <div className="event-date-block">
        <span className="month">{date.toLocaleDateString('en-US', { month: 'short' })}</span>
        <span className="day">{date.getDate()}</span>
      </div>
      <div className="flex-1 min-w-0">
        <p className="event-name">{event.name}</p>
        <p className="event-meta">
          {event.location} • {event.registration_count || 0} registered
        </p>
      </div>
    </div>
  );
};

export default function Dashboard() {
  const { greeting, user } = useOutletContext();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [givingTrend, setGivingTrend] = useState([]);
  const [attendanceTrend, setAttendanceTrend] = useState([]);
  const [activities, setActivities] = useState([]);
  const [events, setEvents] = useState([]);
  const [launchHealth, setLaunchHealth] = useState(null);
  const [launchHealthLoading, setLaunchHealthLoading] = useState(false);
  const [loading, setLoading] = useState(true);

  // Redirect platform admins to their dashboard
  useEffect(() => {
    if (user?.role === 'platform_admin') {
      navigate('/platform', { replace: true });
    }
  }, [user, navigate]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [statsRes, givingRes, attendanceRes, activityRes, eventsRes] = await Promise.all([
          fetch(`${API_URL}/dashboard/stats`),
          fetch(`${API_URL}/dashboard/giving-trend`),
          fetch(`${API_URL}/dashboard/attendance-trend`),
          fetch(`${API_URL}/dashboard/activity`),
          fetch(`${API_URL}/dashboard/upcoming-events`),
        ]);

        const [statsData, givingData, attendanceData, activityData, eventsData] = await Promise.all([
          statsRes.json(),
          givingRes.json(),
          attendanceRes.json(),
          activityRes.json(),
          eventsRes.json(),
        ]);

        setStats(statsData);
        setGivingTrend(givingData);
        setAttendanceTrend(attendanceData);
        setActivities(activityData);
        setEvents(eventsData);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
    fetchLaunchHealth();
  }, []);

  // Real-time polling every 30 seconds
  const pollDashboard = useCallback(async () => {
    try {
      const [statsRes, givingRes, attendanceRes, activityRes, eventsRes] = await Promise.all([
        fetch(`${API_URL}/dashboard/stats`),
        fetch(`${API_URL}/dashboard/giving-trend`),
        fetch(`${API_URL}/dashboard/attendance-trend`),
        fetch(`${API_URL}/dashboard/activity`),
        fetch(`${API_URL}/dashboard/upcoming-events`),
      ]);
      const [statsData, givingData, attendanceData, activityData, eventsData] = await Promise.all([
        statsRes.json(), givingRes.json(), attendanceRes.json(), activityRes.json(), eventsRes.json(),
      ]);
      setStats(statsData); setGivingTrend(givingData); setAttendanceTrend(attendanceData);
      setActivities(activityData); setEvents(eventsData);
    } catch (_) {}
  }, []);
  usePolling(pollDashboard, 30000);

  const fetchLaunchHealth = async () => {
    setLaunchHealthLoading(true);
    try {
      const res = await fetch(`${API_URL}/health/launch-check`);
      if (res.ok) {
        const data = await res.json();
        setLaunchHealth(data);
      }
    } catch (error) {
      console.error('Failed to fetch launch health:', error);
    } finally {
      setLaunchHealthLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-6 bg-slate-200 w-48"></div>
        <div className="grid grid-cols-6 gap-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-24 bg-slate-200"></div>
          ))}
        </div>
      </div>
    );
  }

  const mtdProgress = stats ? (stats.mtd_giving / stats.mtd_goal) * 100 : 0;

  return (
    <div className="space-y-4" data-testid="dashboard-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title" data-testid="dashboard-greeting">
            {greeting}, {user?.name?.split(' ')[0] || 'Admin'}
          </h1>
          <p className="page-subtitle">
            {new Date().toLocaleDateString('en-US', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </p>
        </div>
      </div>

      {/* System Banner - Online Service */}
      <div className="system-banner" data-testid="system-banner">
        <div className="system-banner-content">
          <div className="system-banner-icon">
            <Video className="w-4 h-4" />
          </div>
          <div className="system-banner-text">
            <h3>Live Worship Service</h3>
            <p>Sundays at 9:00 AM & 11:00 AM PST</p>
          </div>
        </div>
        <div className="system-banner-actions">
          <a 
            href="https://zoom.us/j/placeholder" 
            target="_blank" 
            rel="noopener noreferrer"
            className="btn-system"
            data-testid="join-worship-btn"
          >
            <Video className="w-3 h-3" />
            Join Now
            <ExternalLink className="w-3 h-3" />
          </a>
          <a 
            href="https://calendly.com/placeholder"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-system-secondary"
            data-testid="schedule-visit-btn"
          >
            <CalendarCheck className="w-3 h-3" />
            Schedule Visit
          </a>
        </div>
      </div>

      {/* Go-Live Health Widget */}
      <div className="bg-white border border-slate-200 p-4" data-testid="go-live-health-widget">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500" data-testid="go-live-health-label">Go-Live Health</p>
            <h3 className="text-base font-semibold text-slate-900 mt-1 flex items-center gap-2" data-testid="go-live-health-title">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              Launch Readiness Snapshot
            </h3>
            <p className="text-xs text-slate-500 mt-1" data-testid="go-live-health-tenant">Tenant: {launchHealth?.tenant_id || 'abundant-church-001'}</p>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ${launchHealthLoading || !launchHealth ? 'bg-slate-100 text-slate-600' : launchHealth?.status === 'ready' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}
              data-testid="go-live-health-status-badge"
            >
              {launchHealthLoading || !launchHealth ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : launchHealth?.status === 'ready' ? <CircleCheckBig className="w-3.5 h-3.5" /> : <CircleAlert className="w-3.5 h-3.5" />}
              {(launchHealthLoading || !launchHealth ? 'LOADING' : launchHealth?.status || 'unknown').toUpperCase()}
            </span>
            <button
              onClick={fetchLaunchHealth}
              className="inline-flex items-center gap-1 border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
              data-testid="go-live-health-refresh-button"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${launchHealthLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {launchHealth?.checks && (
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2" data-testid="go-live-health-check-grid">
            {Object.entries(launchHealth.checks).map(([key, passed]) => (
              <div
                key={key}
                className={`flex items-center justify-between border px-2.5 py-2 text-xs ${passed ? 'border-emerald-100 bg-emerald-50/40 text-emerald-700' : 'border-amber-100 bg-amber-50/40 text-amber-700'}`}
                data-testid={`go-live-check-${key.replace(/_/g, '-')}`}
              >
                <span className="font-medium">{key.replace(/_/g, ' ')}</span>
                {passed ? <CircleCheckBig className="w-3.5 h-3.5" /> : <CircleAlert className="w-3.5 h-3.5" />}
              </div>
            ))}
          </div>
        )}

        {launchHealth?.generated_at && (
          <p className="text-xs text-slate-400 mt-3" data-testid="go-live-health-timestamp">
            Last updated: {new Date(launchHealth.generated_at).toLocaleString()}
          </p>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard
          title="TOTAL MEMBERS"
          value={formatNumber(stats?.total_members || 0)}
          change={`+${stats?.new_this_week || 0} this week`}
          changeType="positive"
          icon={Users}
        />
        <StatCard
          title="ACTIVE MEMBERS"
          value={formatNumber(stats?.active_members || 0)}
          change="Last 30 days"
          changeType="positive"
          icon={UsersRound}
        />
        <StatCard
          title="LAST SUNDAY"
          value={formatNumber(stats?.last_attendance || 0)}
          change={`+${stats?.last_attendance_change || 0} vs prior`}
          changeType="positive"
          icon={Calendar}
        />
        <StatCard
          title="MTD GIVING"
          value={formatCurrency(stats?.mtd_giving || 0)}
          change={`${Math.round(mtdProgress)}% of goal`}
          changeType="positive"
          icon={DollarSign}
        />
        <StatCard
          title="YTD GIVING"
          value={formatCurrency(stats?.ytd_giving || 0)}
          change="+12% vs LY"
          changeType="positive"
          icon={TrendingUp}
        />
        <StatCard
          title="RECURRING"
          value={formatNumber(stats?.recurring_givers || 0)}
          change="Active schedules"
          changeType="positive"
          icon={RefreshCw}
        />
      </div>

      {/* Secondary Stats Row - Café, Merch, Events */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          title="CAFÉ THIS WEEK"
          value={stats?.cafe_orders_week || 0}
          change={`+$${stats?.cafe_giving_added || 0} offerings`}
          changeType="positive"
          icon={Calendar}
        />
        <StatCard
          title="MERCH THIS WEEK"
          value={stats?.merch_orders_week || 0}
          change={`+$${stats?.merch_giving_added || 0} offerings`}
          changeType="positive"
          icon={Calendar}
        />
        <StatCard
          title="EVENT SIGNUPS"
          value={formatNumber(stats?.event_registrations_month || 0)}
          change="This month"
          changeType="positive"
          icon={Calendar}
        />
        <StatCard
          title="SMALL GROUPS"
          value={stats?.active_groups || 0}
          change={`${stats?.at_risk_members || 0} at-risk members`}
          changeType="neutral"
          icon={UsersRound}
        />
      </div>

      {/* Monthly Goal Progress */}
      <div className="bg-white border border-slate-200 p-4">
        <div className="flex items-center justify-between mb-2">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Monthly Stewardship Goal</p>
            <p className="text-xs text-slate-400 mt-0.5">
              {formatCurrency(stats?.mtd_giving || 0)} of {formatCurrency(stats?.mtd_goal || 350000)}
            </p>
          </div>
          <span className="text-lg font-mono font-semibold text-slate-900">
            {Math.round(mtdProgress)}%
          </span>
        </div>
        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${Math.min(mtdProgress, 100)}%` }}></div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* Attendance Trend */}
        <div className="bento-card">
          <div className="card-header">
            <h3 className="card-title">Attendance Trend (12 Weeks)</h3>
            <Link to="/attendance" className="card-action">View all →</Link>
          </div>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={attendanceTrend}>
                <defs>
                  <linearGradient id="attendanceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis 
                  dataKey="week" 
                  tick={{ fontSize: 10, fill: '#94a3b8' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e2e8f0' }}
                />
                <YAxis 
                  tick={{ fontSize: 10, fill: '#94a3b8' }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => formatNumber(value)}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area 
                  type="monotone" 
                  dataKey="attendance" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  fill="url(#attendanceGradient)"
                  name="Attendance"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Giving Trend */}
        <div className="bento-card">
          <div className="card-header">
            <h3 className="card-title">Giving by Fund (12 Months)</h3>
            <Link to="/giving" className="card-action">View all →</Link>
          </div>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={givingTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis 
                  dataKey="month" 
                  tick={{ fontSize: 10, fill: '#94a3b8' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e2e8f0' }}
                />
                <YAxis 
                  tick={{ fontSize: 10, fill: '#94a3b8' }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `$${(value/1000).toFixed(0)}k`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="General Fund" fill="#3b82f6" />
                <Bar dataKey="Building Fund" fill="#64748b" />
                <Bar dataKey="Missions" fill="#94a3b8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Activity & Events Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* Recent Activity */}
        <div className="bento-card">
          <div className="card-header">
            <h3 className="card-title">Recent Activity</h3>
            <Link to="/reports" className="card-action">View all →</Link>
          </div>
          <div className="space-y-0 max-h-56 overflow-y-auto">
            {activities.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">No recent activity</p>
            ) : (
              activities.map((activity, idx) => (
                <ActivityItem key={idx} activity={activity} />
              ))
            )}
          </div>
        </div>

        {/* Upcoming Events */}
        <div className="bento-card">
          <div className="card-header">
            <h3 className="card-title">Upcoming Events</h3>
            <Link to="/events" className="card-action">Add event →</Link>
          </div>
          <div className="space-y-0 max-h-56 overflow-y-auto">
            {events.length === 0 ? (
              <p className="text-xs text-slate-400 py-6 text-center">No upcoming events</p>
            ) : (
              events.map((event, idx) => (
                <EventCard key={idx} event={event} />
              ))
            )}
          </div>
        </div>
      </div>

      {/* Alerts Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="bg-white border border-slate-200 p-3 flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-medium text-slate-700">47 members need follow-up</p>
            <p className="text-xs text-slate-400">Inactive 90+ days</p>
            <Link to="/people?status=inactive" className="text-xs text-blue-600 font-medium hover:underline mt-1 inline-block">
              View list →
            </Link>
          </div>
        </div>
        <div className="bg-white border border-slate-200 p-3 flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-medium text-slate-700">Building Fund at 67%</p>
            <p className="text-xs text-slate-400">$33K remaining to goal</p>
            <Link to="/giving" className="text-xs text-blue-600 font-medium hover:underline mt-1 inline-block">
              View details →
            </Link>
          </div>
        </div>
        <div className="bg-white border border-slate-200 p-3 flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-medium text-slate-700">Groups at 94% capacity</p>
            <p className="text-xs text-slate-400">Consider launching new groups</p>
            <Link to="/groups" className="text-xs text-blue-600 font-medium hover:underline mt-1 inline-block">
              Manage groups →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
