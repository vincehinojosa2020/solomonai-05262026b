import { useState, useEffect } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import { 
  Users, UsersRound, Calendar, DollarSign, TrendingUp, 
  ArrowUpRight, ArrowDownRight, RefreshCw, Video, ExternalLink, 
  CalendarCheck, AlertCircle
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
    if (action.includes('member') || action.includes('person')) return 'member';
    if (action.includes('donation') || action.includes('giving')) return 'donation';
    if (action.includes('group')) return 'group';
    return 'event';
  };

  return (
    <div className="activity-item" data-testid="activity-item">
      <div className={`activity-dot ${getActivityType(activity.action)}`}></div>
      <div className="flex-1 min-w-0">
        <p className="activity-text">{activity.description}</p>
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
  const [stats, setStats] = useState(null);
  const [givingTrend, setGivingTrend] = useState([]);
  const [attendanceTrend, setAttendanceTrend] = useState([]);
  const [activities, setActivities] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

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
  }, []);

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
          title="ACTIVE GROUPS"
          value={stats?.active_groups || 0}
          change={`${stats?.open_groups || 0} open`}
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
          value={stats?.recurring_givers || 0}
          change="Active schedules"
          changeType="positive"
          icon={RefreshCw}
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
