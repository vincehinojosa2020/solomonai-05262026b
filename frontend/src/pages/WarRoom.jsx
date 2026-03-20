import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users, Baby, Coffee, DollarSign, Activity, Bell,
  Megaphone, Eye, ArrowLeft, Radio
} from 'lucide-react';
import { API_URL } from '@/lib/utils';

const REFRESH_MS = 15000;

function AnimatedCounter({ value, prefix = '', suffix = '' }) {
  const [display, setDisplay] = useState(value);
  const [flash, setFlash] = useState(false);
  const prevRef = useRef(value);

  useEffect(() => {
    if (value !== prevRef.current) {
      setFlash(true);
      const timer = setTimeout(() => setFlash(false), 1200);
      prevRef.current = value;

      // Animate count up/down
      const start = display;
      const end = value;
      const diff = end - start;
      if (diff === 0) return;
      const steps = Math.min(Math.abs(diff), 20);
      const stepTime = 600 / steps;
      let current = 0;
      const interval = setInterval(() => {
        current++;
        setDisplay(Math.round(start + (diff * current) / steps));
        if (current >= steps) { clearInterval(interval); setDisplay(end); }
      }, stepTime);
      return () => { clearInterval(interval); clearTimeout(timer); };
    }
  }, [value]);

  const formatted = typeof display === 'number' && prefix === '$'
    ? display.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
    : typeof display === 'number' ? display.toLocaleString() : display;

  return (
    <span className={`transition-all duration-300 ${flash ? 'text-green-400 scale-110' : ''}`} style={{ display: 'inline-block' }}>
      {prefix}{formatted}{suffix}
    </span>
  );
}

function CapacityGauge({ label, current, max, pct, colorThresholds }) {
  const getColor = (p) => {
    if (p >= 90) return '#ef4444';
    if (p >= 75) return '#f59e0b';
    return '#22c55e';
  };
  const color = colorThresholds ? getColor(pct) : '#4f6ef7';

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</span>
        <span className="text-sm font-mono text-slate-300">{current}/{max}</span>
      </div>
      <div className="h-3 bg-slate-700/50 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs text-slate-500">{pct}%</span>
    </div>
  );
}

function ActivityItem({ item }) {
  const getLabel = (action) => {
    const map = {
      'kid_checkin': 'checked in a child',
      'kid_checkout': 'checked out a child',
      'donation_processed': 'gave',
      'member_created': 'New member joined',
      'church_created': 'New church onboarded',
      'role_updated': 'Role updated',
      'service_checkin': 'checked in for service',
    };
    return map[action] || action?.replace(/_/g, ' ') || 'Activity';
  };

  const getTimeAgo = (ts) => {
    if (!ts) return '';
    const diff = (Date.now() - new Date(ts).getTime()) / 1000;
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  };

  const details = item.details || {};
  const extra = details.amount ? ` $${details.amount}` : details.tenant ? ` — ${details.tenant}` : '';

  return (
    <div className="flex items-start gap-3 py-3 border-b border-slate-700/40 last:border-0 animate-fade-in">
      <div className="w-2 h-2 rounded-full bg-green-400 mt-2 flex-shrink-0 animate-pulse" />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-200 truncate">
          <span className="font-medium text-white">{item.performed_by_name || 'System'}</span>
          {' '}{getLabel(item.action)}{extra}
        </p>
        <p className="text-xs text-slate-500 mt-0.5">{getTimeAgo(item.timestamp)}</p>
      </div>
    </div>
  );
}

export default function WarRoom() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [pulse, setPulse] = useState(false);
  const intervalRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      const token = localStorage.getItem('session_token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      const res = await fetch(`${API_URL}/admin/war-room`, { headers });
      if (res.ok) {
        const d = await res.json();
        setData(d);
        setLastUpdate(new Date());
        setPulse(true);
        setTimeout(() => setPulse(false), 800);
      }
    } catch (err) {
      console.error('War Room fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    intervalRef.current = setInterval(fetchData, REFRESH_MS);
    return () => clearInterval(intervalRef.current);
  }, [fetchData]);

  const c = data?.counters || {};
  const cap = data?.capacity || {};

  return (
    <div className="min-h-screen bg-[#0a0e1a] text-white" data-testid="war-room">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700/50">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            data-testid="war-room-back"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold tracking-tight">War Room</h1>
            <p className="text-xs text-slate-500">Sunday Morning Command Center</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {lastUpdate && (
            <span className="text-xs text-slate-500">
              Updated {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${pulse ? 'bg-green-500/20' : 'bg-green-500/10'} transition-colors`} data-testid="live-badge">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            <span className="text-xs font-semibold text-green-400 uppercase tracking-wider">Live</span>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-[calc(100vh-64px)]">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="p-6 space-y-6">
          {/* Top Row — Big Counters */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4" data-testid="war-room-counters">
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5 hover:bg-slate-800/70 transition-colors">
              <div className="flex items-center gap-2 mb-2">
                <Users className="w-4 h-4 text-blue-400" />
                <span className="text-xs text-slate-400 uppercase tracking-wider font-medium">Members</span>
              </div>
              <p className="text-4xl font-bold font-mono tracking-tight text-blue-300" data-testid="counter-members">
                <AnimatedCounter value={c.total_members || 0} />
              </p>
              <p className="text-xs text-slate-500 mt-1">{c.active_members || 0} active</p>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5 hover:bg-slate-800/70 transition-colors">
              <div className="flex items-center gap-2 mb-2">
                <Baby className="w-4 h-4 text-green-400" />
                <span className="text-xs text-slate-400 uppercase tracking-wider font-medium">Kids Checked In</span>
              </div>
              <p className="text-4xl font-bold font-mono tracking-tight text-green-300" data-testid="counter-kids">
                <AnimatedCounter value={c.kids_checked_in || 0} />
              </p>
              <p className="text-xs text-slate-500 mt-1">{c.kids_total_today || 0} total today</p>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5 hover:bg-slate-800/70 transition-colors">
              <div className="flex items-center gap-2 mb-2">
                <Coffee className="w-4 h-4 text-amber-400" />
                <span className="text-xs text-slate-400 uppercase tracking-wider font-medium">Cafe Orders</span>
              </div>
              <p className="text-4xl font-bold font-mono tracking-tight text-amber-300" data-testid="counter-cafe">
                <AnimatedCounter value={c.cafe_orders_total || 0} />
              </p>
              <p className="text-xs text-slate-500 mt-1">{c.cafe_orders_today || 0} today</p>
            </div>

            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5 hover:bg-slate-800/70 transition-colors">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="w-4 h-4 text-emerald-400" />
                <span className="text-xs text-slate-400 uppercase tracking-wider font-medium">MTD Giving</span>
              </div>
              <p className="text-4xl font-bold font-mono tracking-tight text-emerald-300" data-testid="counter-giving">
                <AnimatedCounter value={Math.round(c.mtd_giving || 0)} prefix="$" />
              </p>
              <p className="text-xs text-slate-500 mt-1">Goal: ${(c.giving_goal || 250000).toLocaleString()}</p>
            </div>
          </div>

          {/* Middle: Activity Feed + Capacity Gauges */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Activity Feed */}
            <div className="lg:col-span-2 bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5" data-testid="activity-feed">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="w-4 h-4 text-blue-400" />
                <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Live Activity</h3>
                <div className={`w-1.5 h-1.5 rounded-full bg-green-400 ${pulse ? 'animate-ping' : 'animate-pulse'}`} />
              </div>
              <div className="space-y-0 max-h-[340px] overflow-y-auto pr-2 scrollbar-thin">
                {data?.activity_feed?.length > 0 ? (
                  data.activity_feed.map((item, i) => <ActivityItem key={i} item={item} />)
                ) : (
                  <p className="text-sm text-slate-500 py-8 text-center">No recent activity. Waiting for Sunday morning...</p>
                )}
              </div>
            </div>

            {/* Capacity Gauges */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5 space-y-6" data-testid="capacity-gauges">
              <div className="flex items-center gap-2 mb-2">
                <Radio className="w-4 h-4 text-purple-400" />
                <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Capacity</h3>
              </div>
              <CapacityGauge
                label="Kids Check-In"
                current={cap.kids?.current || 0}
                max={cap.kids?.max || 40}
                pct={cap.kids?.pct || 0}
                colorThresholds
              />
              <CapacityGauge
                label="Cafe Queue"
                current={cap.cafe?.queue || 0}
                max={100}
                pct={Math.min((cap.cafe?.queue || 0), 100)}
              />
              <CapacityGauge
                label="Giving Goal (MTD)"
                current={Math.round(cap.giving?.current || 0)}
                max={cap.giving?.goal || 250000}
                pct={cap.giving?.pct || 0}
              />
            </div>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3" data-testid="war-room-actions">
            <button
              onClick={() => navigate('/communications')}
              className="flex items-center gap-3 p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl hover:bg-slate-700/50 hover:border-blue-500/30 transition-all group"
              data-testid="action-announcement"
            >
              <Megaphone className="w-5 h-5 text-blue-400 group-hover:text-blue-300" />
              <span className="text-sm font-medium text-slate-300 group-hover:text-white">Send Announcement</span>
            </button>
            <button
              onClick={() => navigate('/communications')}
              className="flex items-center gap-3 p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl hover:bg-slate-700/50 hover:border-purple-500/30 transition-all group"
              data-testid="action-push"
            >
              <Bell className="w-5 h-5 text-purple-400 group-hover:text-purple-300" />
              <span className="text-sm font-medium text-slate-300 group-hover:text-white">Push Notification</span>
            </button>
            <button
              onClick={() => navigate('/kids-checkin')}
              className="flex items-center gap-3 p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl hover:bg-slate-700/50 hover:border-green-500/30 transition-all group"
              data-testid="action-kids"
            >
              <Baby className="w-5 h-5 text-green-400 group-hover:text-green-300" />
              <span className="text-sm font-medium text-slate-300 group-hover:text-white">View Kids Check-In</span>
            </button>
            <button
              onClick={() => navigate('/giving')}
              className="flex items-center gap-3 p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl hover:bg-slate-700/50 hover:border-emerald-500/30 transition-all group"
              data-testid="action-giving"
            >
              <DollarSign className="w-5 h-5 text-emerald-400 group-hover:text-emerald-300" />
              <span className="text-sm font-medium text-slate-300 group-hover:text-white">View Giving</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
