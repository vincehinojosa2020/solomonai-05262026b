import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users, Baby, Coffee, DollarSign, Activity, ArrowLeft, 
  ShoppingBag, UserPlus, ShieldCheck, Heart, TrendingUp, Zap
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
    <span className={`transition-all duration-300 ${flash ? 'scale-105' : ''}`} style={{ display: 'inline-block' }}>
      {prefix}{formatted}{suffix}
    </span>
  );
}

function GivingSparkline({ data }) {
  if (!data || data.length === 0) return null;
  const max = Math.max(...data.map(d => d.amount), 1);
  const w = 100 / data.length;
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 80 }}>
      {data.map((d, i) => {
        const h = Math.max(8, (d.amount / max) * 70);
        const isToday = i === data.length - 1;
        return (
          <div key={`item-${i}`} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
            <div
              style={{
                width: '100%', height: h, borderRadius: 4,
                background: isToday ? '#f59e0b' : '#334155',
                transition: 'height 0.6s ease-out',
                position: 'relative'
              }}
            >
              {isToday && (
                <div style={{ position: 'absolute', top: -20, left: '50%', transform: 'translateX(-50%)', fontSize: 10, color: '#f59e0b', fontWeight: 700, whiteSpace: 'nowrap' }}>
                  ${d.amount.toLocaleString()}
                </div>
              )}
            </div>
            <span style={{ fontSize: 9, color: isToday ? '#f59e0b' : '#64748b', fontWeight: isToday ? 700 : 400 }}>{d.label}</span>
          </div>
        );
      })}
    </div>
  );
}

function FeedItem({ item }) {
  const iconMap = {
    kid_checkin: { icon: Baby, color: '#4ade80', bg: '#064e3b' },
    kid_checkout: { icon: Baby, color: '#94a3b8', bg: '#1e293b' },
    donation_processed: { icon: Heart, color: '#34d399', bg: '#064e3b' },
    cafe_order: { icon: Coffee, color: '#fbbf24', bg: '#451a03' },
    merch_sale: { icon: ShoppingBag, color: '#a78bfa', bg: '#2e1065' },
    visitor_registered: { icon: UserPlus, color: '#38bdf8', bg: '#0c4a6e' },
    service_checkin: { icon: Users, color: '#60a5fa', bg: '#1e3a5f' },
    volunteer_checkin: { icon: ShieldCheck, color: '#f472b6', bg: '#500724' },
  };
  const cfg = iconMap[item.action] || { icon: Activity, color: '#94a3b8', bg: '#1e293b' };
  const Icon = cfg.icon;
  const ts = item.timestamp ? new Date(item.timestamp) : null;
  const time = ts ? ts.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }) : '';

  const getLabel = () => {
    const d = item.details || {};
    switch (item.action) {
      case 'kid_checkin': return `${d.child || 'Child'} checked in to ${d.classroom || 'classroom'}`;
      case 'donation_processed': return `${item.performed_by_name} gave $${d.amount || '?'} to ${d.fund || 'General'}`;
      case 'cafe_order': return `${item.performed_by_name} ordered ${d.items || 'coffee'}`;
      case 'merch_sale': return `${d.item || 'Item'} sold — $${d.amount || '?'}`;
      case 'visitor_registered': return `New visitor: ${item.performed_by_name}`;
      case 'service_checkin': return `${item.performed_by_name} checked in`;
      case 'volunteer_checkin': return `${item.performed_by_name} — ${d.role || 'Volunteer'}`;
      default: return `${item.performed_by_name || 'System'} — ${item.action?.replace(/_/g, ' ')}`;
    }
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', borderBottom: '1px solid rgba(51,65,85,0.4)' }}>
      <div style={{ width: 32, height: 32, borderRadius: 8, background: cfg.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        <Icon style={{ width: 16, height: 16, color: cfg.color }} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{ fontSize: 13, color: '#e2e8f0', margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{getLabel()}</p>
      </div>
      <span style={{ fontSize: 11, color: '#64748b', fontFamily: 'monospace', flexShrink: 0 }}>{time}</span>
    </div>
  );
}

export default function WarRoom() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [pulse, setPulse] = useState(false);
  const [clock, setClock] = useState(new Date());
  const intervalRef = useRef(null);

  useEffect(() => {
    const t = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const fetchData = useCallback(async () => {
    try {
      const token = sessionStorage.getItem('session_token');
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
  const churchName = data?.church_name || 'Abundant Church';

  const kpiCards = [
    { label: 'Members Present', value: c.members_present || 0, sub: `vs last Sunday`, icon: Users, color: '#60a5fa', prefix: '' },
    { label: 'Kids in Sunday School', value: c.kids_checked_in || 0, sub: `${c.classrooms_active || 0} classrooms active`, icon: Baby, color: '#4ade80', prefix: '' },
    { label: 'Volunteers On Duty', value: c.volunteers_on_duty || 0, sub: `roles covered`, icon: ShieldCheck, color: '#f472b6', prefix: '' },
    { label: 'First-Time Visitors', value: c.first_time_visitors || 0, sub: 'This Sunday', icon: UserPlus, color: '#38bdf8', prefix: '' },
    { label: 'Given Today', value: Math.round(c.given_today || 0), sub: `${(c.given_today ? Math.ceil(c.given_today / 85) : 0)} transactions`, icon: Heart, color: '#34d399', prefix: '$' },
    { label: 'MTD Giving', value: Math.round(c.mtd_giving || 0), sub: `${c.giving_goal ? Math.round(c.mtd_giving / c.giving_goal * 100) : 0}% of goal`, icon: TrendingUp, color: '#a78bfa', prefix: '$' },
    { label: 'Cafe Orders', value: c.cafe_orders_today || 0, sub: `$${c.cafe_revenue?.toLocaleString() || 0} revenue`, icon: Coffee, color: '#fbbf24', prefix: '' },
    { label: 'Merch Sales', value: c.merch_sales || 0, sub: `$${c.merch_revenue?.toLocaleString() || 0} today`, icon: ShoppingBag, color: '#c084fc', prefix: '' },
  ];

  return (
    <div style={{ minHeight: '100vh', background: '#0a0e1a', color: 'white' }} data-testid="war-room">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 24px', borderBottom: '1px solid rgba(51,65,85,0.4)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <button onClick={() => navigate('/dashboard')} style={{ padding: 8, borderRadius: 8, background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }} data-testid="war-room-back">
            <ArrowLeft style={{ width: 20, height: 20 }} />
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Zap style={{ width: 22, height: 22, color: '#f59e0b' }} />
            <div>
              <h1 style={{ fontSize: 18, fontWeight: 800, margin: 0, letterSpacing: '-0.02em', color: '#f8fafc' }}>WAR ROOM</h1>
              <p style={{ fontSize: 11, color: '#64748b', margin: 0, letterSpacing: '0.05em', textTransform: 'uppercase' }}>Solomon AI Command Center</p>
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
          <span style={{ fontSize: 13, color: '#94a3b8', fontWeight: 500 }}>{churchName}</span>
          <span style={{ fontSize: 13, color: '#64748b', fontFamily: 'monospace' }}>
            {clock.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
          </span>
          <span style={{ fontSize: 18, color: '#f8fafc', fontFamily: 'monospace', fontWeight: 700, minWidth: 85 }}>
            {clock.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 14px', borderRadius: 20, background: pulse ? 'rgba(74,222,128,0.15)' : 'rgba(74,222,128,0.08)', transition: 'background 0.3s' }} data-testid="live-badge">
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#4ade80', animation: 'pulse 2s infinite' }} />
            <span style={{ fontSize: 12, fontWeight: 700, color: '#4ade80', textTransform: 'uppercase', letterSpacing: '0.08em' }}>LIVE</span>
          </div>
          {lastUpdate && <span style={{ fontSize: 11, color: '#475569' }}>Updated {lastUpdate.toLocaleTimeString()}</span>}
        </div>
      </div>

      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 'calc(100vh - 64px)' }}>
          <div style={{ width: 32, height: 32, border: '3px solid #3b82f6', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
        </div>
      ) : (
        <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* KPI Cards — 2 rows of 4 */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }} data-testid="war-room-counters">
            {kpiCards.map((kpi, i) => {
              const Icon = kpi.icon;
              return (
                <div key={`item-${i}`} style={{
                  background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(51,65,85,0.5)',
                  borderRadius: 14, padding: '20px 22px', transition: 'border-color 0.3s',
                }} data-testid={`kpi-${kpi.label.toLowerCase().replace(/\s+/g, '-')}`}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                    <Icon style={{ width: 16, height: 16, color: kpi.color }} />
                    <span style={{ fontSize: 11, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>{kpi.label}</span>
                  </div>
                  <p style={{ fontSize: 36, fontWeight: 800, fontFamily: 'monospace', color: kpi.color, margin: 0, letterSpacing: '-0.02em', lineHeight: 1 }}>
                    <AnimatedCounter value={kpi.value} prefix={kpi.prefix} />
                  </p>
                  <p style={{ fontSize: 12, color: '#475569', margin: '8px 0 0 0' }}>{kpi.sub}</p>
                </div>
              );
            })}
          </div>

          {/* Bottom Section: Activity Feed + Giving Trend */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16 }}>
            {/* Activity Feed */}
            <div style={{ background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(51,65,85,0.5)', borderRadius: 14, padding: '20px 22px' }} data-testid="activity-feed">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                <Activity style={{ width: 16, height: 16, color: '#60a5fa' }} />
                <h3 style={{ fontSize: 12, fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase', letterSpacing: '0.06em', margin: 0 }}>Real-Time Activity</h3>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#4ade80', animation: 'pulse 2s infinite' }} />
              </div>
              <div style={{ maxHeight: 360, overflowY: 'auto' }}>
                {data?.activity_feed?.length > 0 ? (
                  data.activity_feed.map((item, i) => <FeedItem key={`item-${i}`} item={item} />)
                ) : (
                  <p style={{ textAlign: 'center', padding: 40, color: '#475569', fontSize: 14 }}>Waiting for Sunday morning activity...</p>
                )}
              </div>
            </div>

            {/* Giving Momentum */}
            <div style={{ background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(51,65,85,0.5)', borderRadius: 14, padding: '20px 22px' }} data-testid="giving-momentum">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
                <TrendingUp style={{ width: 16, height: 16, color: '#f59e0b' }} />
                <h3 style={{ fontSize: 12, fontWeight: 700, color: '#cbd5e1', textTransform: 'uppercase', letterSpacing: '0.06em', margin: 0 }}>Giving Momentum</h3>
              </div>
              <GivingSparkline data={data?.giving_trend || []} />
              <div style={{ marginTop: 20, padding: '14px 16px', background: 'rgba(51,65,85,0.3)', borderRadius: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase' }}>Goal Progress</span>
                  <span style={{ fontSize: 11, color: '#94a3b8', fontFamily: 'monospace' }}>{data?.capacity?.giving?.pct || 0}%</span>
                </div>
                <div style={{ height: 8, background: 'rgba(51,65,85,0.5)', borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', borderRadius: 4, transition: 'width 1s ease-out',
                    width: `${Math.min(data?.capacity?.giving?.pct || 0, 100)}%`,
                    background: 'linear-gradient(90deg, #f59e0b, #f97316)'
                  }} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
                  <span style={{ fontSize: 11, color: '#94a3b8' }}>${Math.round(c.mtd_giving || 0).toLocaleString()}</span>
                  <span style={{ fontSize: 11, color: '#475569' }}>${(c.giving_goal || 250000).toLocaleString()}</span>
                </div>
              </div>

              {/* Quick Actions */}
              <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <button onClick={() => navigate('/kids-checkin')} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', background: 'rgba(51,65,85,0.3)', border: '1px solid rgba(51,65,85,0.5)', borderRadius: 8, color: '#94a3b8', fontSize: 12, fontWeight: 600, cursor: 'pointer', width: '100%', textAlign: 'left' }} data-testid="action-kids">
                  <Baby style={{ width: 14, height: 14, color: '#4ade80' }} /> View Kids Check-In
                </button>
                <button onClick={() => navigate('/giving')} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', background: 'rgba(51,65,85,0.3)', border: '1px solid rgba(51,65,85,0.5)', borderRadius: 8, color: '#94a3b8', fontSize: 12, fontWeight: 600, cursor: 'pointer', width: '100%', textAlign: 'left' }} data-testid="action-giving">
                  <DollarSign style={{ width: 14, height: 14, color: '#34d399' }} /> View Giving
                </button>
                <button onClick={() => navigate('/communications')} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', background: 'rgba(51,65,85,0.3)', border: '1px solid rgba(51,65,85,0.5)', borderRadius: 8, color: '#94a3b8', fontSize: 12, fontWeight: 600, cursor: 'pointer', width: '100%', textAlign: 'left' }} data-testid="action-comms">
                  <Activity style={{ width: 14, height: 14, color: '#60a5fa' }} /> Send Announcement
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} } @keyframes spin { to{transform:rotate(360deg)} }`}</style>
    </div>
  );
}
