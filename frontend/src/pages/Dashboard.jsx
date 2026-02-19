import { useState, useEffect } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import { 
  Users, UsersRound, Calendar, DollarSign, TrendingUp, 
  ArrowUpRight, ArrowDownRight, RefreshCw, Video, ExternalLink, 
  CalendarCheck
} from 'lucide-react';
import { 
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { API_URL, formatCurrency, formatNumber, formatRelativeTime } from '@/lib/utils';

const StatCard = ({ title, value, change, changeType, icon: Icon }) => (
  <div className="stat-card" data-testid={`stat-${title.toLowerCase().replace(/\s+/g, '-')}`}>
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
      <div className="p-2 bg-[#f7f7f5] rounded">
        <Icon className="w-4 h-4 text-[#8a8a8a]" />
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
      <div className="animate-fade-in space-y-6">
        <div className="h-8 bg-[#e8e8e5] rounded w-64"></div>
        <div className="grid grid-cols-6 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-28 bg-[#e8e8e5] rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  const mtdProgress = stats ? (stats.mtd_giving / stats.mtd_goal) * 100 : 0;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="dashboard-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title" data-testid="dashboard-greeting">{greeting}</h1>
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

      {/* Worship Experience Banner - Enterprise */}
      <div className="worship-banner" data-testid="worship-banner">
        <div className="worship-banner-content">
          <div className="worship-banner-icon">
            <Video className="w-5 h-5" />
          </div>
          <div className="worship-banner-text">
            <h3>Experience Worship Live</h3>
            <p>Join thousands gathering online every Sunday at 9:00 AM & 11:00 AM</p>
          </div>
        </div>
        <div className="worship-banner-actions">
          <a 
            href="https://zoom.us/j/placeholder" 
            target="_blank" 
            rel="noopener noreferrer"
            className="btn-worship"
            data-testid="join-worship-btn"
          >
            <Video className="w-4 h-4" />
            Join Now
            <ExternalLink className="w-3 h-3 opacity-60" />
          </a>
          <a 
            href="https://calendly.com/placeholder"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-schedule"
            data-testid="schedule-visit-btn"
          >
            <CalendarCheck className="w-4 h-4" />
            Schedule Visit
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
          change={`${stats?.open_groups || 0} accepting members`}
          changeType="positive"
          icon={UsersRound}
        />
        <StatCard
          title="Last Sunday"
          value={formatNumber(stats?.last_attendance || 0)}
          change={`+${stats?.last_attendance_change || 0} vs prior`}
          changeType="positive"
          icon={Calendar}
        />
        <StatCard
          title="MTD Giving"
          value={formatCurrency(stats?.mtd_giving || 0)}
          change={`${Math.round(mtdProgress)}% of goal`}
          changeType="positive"
          icon={DollarSign}
        />
        <StatCard
          title="YTD Giving"
          value={formatCurrency(stats?.ytd_giving || 0)}
          change="+12% vs last year"
          changeType="positive"
          icon={TrendingUp}
        />
        <StatCard
          title="Recurring Partners"
          value={stats?.recurring_givers || 0}
          change="Active schedules"
          changeType="positive"
          icon={RefreshCw}
        />
      </div>

      {/* Monthly Goal Progress */}
      <div className="bg-white border border-[#e8e8e5] rounded-lg p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-sm font-medium text-[#1a1a1a]">Monthly Stewardship Goal</p>
            <p className="text-xs text-[#8a8a8a]">
              {formatCurrency(stats?.mtd_giving || 0)} of {formatCurrency(stats?.mtd_goal || 350000)} goal
            </p>
          </div>
          <span className="text-xl font-semibold text-[#1a1a1a] font-data">
            {Math.round(mtdProgress)}%
          </span>
        </div>
        <Progress value={mtdProgress} className="h-1.5" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Attendance Trend */}
        <div className="bento-card">
          <div className="card-header">
            <h3 className="card-title">Attendance Trend</h3>
            <Link to="/attendance" className="card-action">View report →</Link>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={attendanceTrend}>
                <defs>
                  <linearGradient id="attendanceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2d7a6b" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#2d7a6b" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e5" />
                <XAxis 
                  dataKey="week" 
                  tick={{ fontSize: 11, fill: '#8a8a8a' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e8e8e5' }}
                />
                <YAxis 
                  tick={{ fontSize: 11, fill: '#8a8a8a' }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => formatNumber(value)}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area 
                  type="monotone" 
                  dataKey="attendance" 
                  stroke="#2d7a6b" 
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
            <h3 className="card-title">Giving by Fund</h3>
            <Link to="/giving" className="card-action">View report →</Link>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={givingTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e5" />
                <XAxis 
                  dataKey="month" 
                  tick={{ fontSize: 11, fill: '#8a8a8a' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e8e8e5' }}
                />
                <YAxis 
                  tick={{ fontSize: 11, fill: '#8a8a8a' }}
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
                <Bar dataKey="General Fund" fill="#2d7a6b" radius={[2, 2, 0, 0]} />
                <Bar dataKey="Building Fund" fill="#3b82f6" radius={[2, 2, 0, 0]} />
                <Bar dataKey="Missions" fill="#8b5cf6" radius={[2, 2, 0, 0]} />
                <Bar dataKey="Crypto" fill="#f59e0b" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Activity & Events Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Recent Activity */}
        <div className="bento-card">
          <div className="card-header">
            <h3 className="card-title">Recent Activity</h3>
            <Link to="/reports" className="card-action">View all →</Link>
          </div>
          <div className="space-y-0 max-h-72 overflow-y-auto">
            {activities.length === 0 ? (
              <p className="text-sm text-[#8a8a8a] py-8 text-center">No recent activity</p>
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
          <div className="space-y-0 max-h-72 overflow-y-auto">
            {events.length === 0 ? (
              <p className="text-sm text-[#8a8a8a] py-8 text-center">No upcoming events</p>
            ) : (
              events.map((event, idx) => (
                <EventCard key={idx} event={event} />
              ))
            )}
          </div>
        </div>
      </div>

      {/* Insights - Frank Luntz style messaging */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-[#e8e8e5] rounded-lg p-4 flex items-start gap-3">
          <span className="w-2 h-2 bg-[#d94f4f] rounded-full mt-2 flex-shrink-0"></span>
          <div>
            <p className="text-sm font-medium text-[#1a1a1a]">47 members need reconnection</p>
            <p className="text-xs text-[#8a8a8a] mt-0.5">Inactive 90+ days</p>
            <Link to="/people?status=inactive" className="text-xs text-[#2d7a6b] font-medium hover:underline mt-1 inline-block">
              Take action →
            </Link>
          </div>
        </div>
        <div className="bg-white border border-[#e8e8e5] rounded-lg p-4 flex items-start gap-3">
          <span className="w-2 h-2 bg-[#f59e0b] rounded-full mt-2 flex-shrink-0"></span>
          <div>
            <p className="text-sm font-medium text-[#1a1a1a]">Building Fund at 67% capacity</p>
            <p className="text-xs text-[#8a8a8a] mt-0.5">$33K remaining to goal</p>
            <Link to="/giving" className="text-xs text-[#2d7a6b] font-medium hover:underline mt-1 inline-block">
              View details →
            </Link>
          </div>
        </div>
        <div className="bg-white border border-[#e8e8e5] rounded-lg p-4 flex items-start gap-3">
          <span className="w-2 h-2 bg-[#2d7a6b] rounded-full mt-2 flex-shrink-0"></span>
          <div>
            <p className="text-sm font-medium text-[#1a1a1a]">Small Groups at 94% capacity</p>
            <p className="text-xs text-[#8a8a8a] mt-0.5">Consider launching new groups</p>
            <Link to="/groups" className="text-xs text-[#2d7a6b] font-medium hover:underline mt-1 inline-block">
              Manage groups →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
