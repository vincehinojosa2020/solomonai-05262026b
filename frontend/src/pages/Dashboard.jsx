import { useState, useEffect } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import { 
  Users, UsersRound, Calendar, DollarSign, TrendingUp, 
  UserPlus, ArrowUpRight, ArrowDownRight, ChevronRight,
  Plus, RefreshCw, Video, ExternalLink, CalendarCheck
} from 'lucide-react';
import { 
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { API_URL, formatCurrency, formatNumber, formatRelativeTime } from '@/lib/utils';

const StatCard = ({ title, value, change, changeType, icon: Icon, highlight }) => (
  <div className={`stat-card ${highlight ? 'border-l-4 border-l-amber-400' : ''}`} data-testid={`stat-${title.toLowerCase().replace(/\s+/g, '-')}`}>
    <div className="flex items-start justify-between">
      <div>
        <p className="stat-label">{title}</p>
        <p className="stat-value mt-1">{value}</p>
        {change && (
          <p className={`stat-change ${changeType === 'positive' ? 'positive' : 'negative'}`}>
            {changeType === 'positive' ? (
              <ArrowUpRight className="w-3 h-3 inline mr-1" />
            ) : (
              <ArrowDownRight className="w-3 h-3 inline mr-1" />
            )}
            {change}
          </p>
        )}
      </div>
      <div className="p-2 bg-slate-100 rounded-lg">
        <Icon className="w-5 h-5 text-slate-400" />
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
            {entry.name}: {formatCurrency(entry.value)}
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
    if (action.includes('event')) return 'event';
    return 'member';
  };

  return (
    <div className="activity-item" data-testid="activity-item">
      <div className={`activity-dot ${getActivityType(activity.action)}`}></div>
      <div className="activity-content">
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
      <div className="event-info">
        <p className="event-name">{event.name}</p>
        <p className="event-meta">
          {event.location} • {event.registration_count || 0} registered
        </p>
      </div>
    </div>
  );
};

export default function Dashboard() {
  const { greeting } = useOutletContext();
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
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-slate-200 rounded w-64"></div>
        <div className="grid grid-cols-6 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-32 bg-slate-200 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  const mtdProgress = stats ? (stats.mtd_giving / stats.mtd_goal) * 100 : 0;

  return (
    <div className="space-y-8 animate-fade-in" data-testid="dashboard-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title" data-testid="dashboard-greeting">{greeting}, Admin</h1>
          <p className="page-subtitle">
            {new Date().toLocaleDateString('en-US', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="h-9" data-testid="quick-actions-btn">
            <Plus className="w-4 h-4 mr-2" />
            Quick Actions
          </Button>
        </div>
      </div>

      {/* Join Service CTA - Prominent */}
      <div className="join-service-banner" data-testid="join-service-banner">
        <div className="flex items-center gap-4">
          <div className="join-service-icon">
            <Video className="w-6 h-6" />
          </div>
          <div>
            <h2 className="join-service-title">Join Our Online Service</h2>
            <p className="join-service-subtitle">Sundays at 9:00 AM & 11:00 AM PST</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <a 
            href="https://zoom.us/j/placeholder" 
            target="_blank" 
            rel="noopener noreferrer"
            className="btn-join-online"
            data-testid="join-zoom-btn"
          >
            <Video className="w-5 h-5 mr-2" />
            Join Service
            <ExternalLink className="w-4 h-4 ml-2 opacity-70" />
          </a>
          <a 
            href="https://calendly.com/placeholder"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-calendly"
            data-testid="schedule-meeting-btn"
          >
            <CalendarCheck className="w-5 h-5 mr-2" />
            Schedule a Visit
          </a>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard
          title="Total Members"
          value={formatNumber(stats?.total_members || 0)}
          change={`+${stats?.new_this_week || 0} this week`}
          changeType="positive"
          icon={Users}
        />
        <StatCard
          title="Active Groups"
          value={stats?.active_groups || 0}
          change={`${stats?.open_groups || 0} open`}
          changeType="positive"
          icon={UsersRound}
        />
        <StatCard
          title="Last Sunday"
          value={formatNumber(stats?.last_attendance || 0)}
          change={`+${stats?.last_attendance_change || 0} vs last week`}
          changeType="positive"
          icon={Calendar}
        />
        <StatCard
          title="MTD Giving"
          value={formatCurrency(stats?.mtd_giving || 0)}
          change={`${Math.round(mtdProgress)}% of goal`}
          changeType="positive"
          icon={DollarSign}
          highlight={true}
        />
        <StatCard
          title="YTD Giving"
          value={formatCurrency(stats?.ytd_giving || 0)}
          change="+12% vs last year"
          changeType="positive"
          icon={TrendingUp}
        />
        <StatCard
          title="Recurring Givers"
          value={stats?.recurring_givers || 0}
          change="Active schedules"
          changeType="positive"
          icon={RefreshCw}
        />
      </div>

      {/* MTD Goal Progress */}
      <div className="bg-white border border-slate-200 rounded-lg p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-sm font-medium text-slate-700">Monthly Giving Goal</p>
            <p className="text-xs text-slate-500">
              {formatCurrency(stats?.mtd_giving || 0)} of {formatCurrency(stats?.mtd_goal || 350000)} goal
            </p>
          </div>
          <span className="text-2xl font-bold text-slate-900 font-data">
            {Math.round(mtdProgress)}%
          </span>
        </div>
        <Progress value={mtdProgress} className="h-2" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Attendance Trend */}
        <div className="bento-card">
          <div className="card-header">
            <h3 className="card-title">Attendance Trend (12 weeks)</h3>
            <Link to="/attendance" className="card-action">View full report →</Link>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={attendanceTrend}>
                <defs>
                  <linearGradient id="attendanceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4f6ef7" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#4f6ef7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis 
                  dataKey="week" 
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e2e8f0' }}
                />
                <YAxis 
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => formatNumber(value)}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area 
                  type="monotone" 
                  dataKey="attendance" 
                  stroke="#4f6ef7" 
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
            <h3 className="card-title">Giving by Fund (12 months)</h3>
            <Link to="/giving" className="card-action">View full report →</Link>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={givingTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis 
                  dataKey="month" 
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e2e8f0' }}
                />
                <YAxis 
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `$${formatNumber(value)}`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend 
                  iconType="circle" 
                  iconSize={8}
                  wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }}
                />
                <Bar dataKey="General Fund" fill="#4f6ef7" radius={[2, 2, 0, 0]} />
                <Bar dataKey="Building Fund" fill="#f5a623" radius={[2, 2, 0, 0]} />
                <Bar dataKey="Missions" fill="#00c896" radius={[2, 2, 0, 0]} />
                <Bar dataKey="Crypto" fill="#8b5cf6" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Activity & Events Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="bento-card">
          <div className="card-header">
            <h3 className="card-title">Recent Activity</h3>
            <Link to="/reports" className="card-action">View all →</Link>
          </div>
          <div className="space-y-0 max-h-80 overflow-y-auto">
            {activities.length === 0 ? (
              <p className="text-sm text-slate-400 py-8 text-center">No recent activity</p>
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
            <Link to="/events" className="card-action">Add Event →</Link>
          </div>
          <div className="space-y-0 max-h-80 overflow-y-auto">
            {events.length === 0 ? (
              <p className="text-sm text-slate-400 py-8 text-center">No upcoming events</p>
            ) : (
              events.map((event, idx) => (
                <EventCard key={idx} event={event} />
              ))
            )}
          </div>
        </div>
      </div>

      {/* Quick Insights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-red-50 border border-red-100 rounded-lg p-4 flex items-start gap-3">
          <span className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></span>
          <div>
            <p className="text-sm font-medium text-red-900">47 members inactive 90+ days</p>
            <Link to="/people?status=inactive" className="text-xs text-red-600 hover:underline">
              Follow up →
            </Link>
          </div>
        </div>
        <div className="bg-amber-50 border border-amber-100 rounded-lg p-4 flex items-start gap-3">
          <span className="w-2 h-2 bg-amber-500 rounded-full mt-2 flex-shrink-0"></span>
          <div>
            <p className="text-sm font-medium text-amber-900">Building Fund at 67% of goal</p>
            <Link to="/giving" className="text-xs text-amber-600 hover:underline">
              View details →
            </Link>
          </div>
        </div>
        <div className="bg-emerald-50 border border-emerald-100 rounded-lg p-4 flex items-start gap-3">
          <span className="w-2 h-2 bg-emerald-500 rounded-full mt-2 flex-shrink-0"></span>
          <div>
            <p className="text-sm font-medium text-emerald-900">Small Groups at 94% capacity</p>
            <Link to="/groups" className="text-xs text-emerald-600 hover:underline">
              Consider adding new groups →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
