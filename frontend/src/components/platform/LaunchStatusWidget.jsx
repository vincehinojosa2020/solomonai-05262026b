import { useEffect, useState } from 'react';
import { API_URL, formatCurrency } from '@/lib/utils';
import { CheckCircle2, AlertTriangle, XCircle, Activity, Database, Zap, Clock } from 'lucide-react';

/**
 * God-Mode Launch Status widget — composite health-and-pulse card.
 * Polls /api/health/launch-status every 15s. Surfaces enough signal
 * for the on-call to call Sunday-morning green/yellow/red instantly.
 */
const ICONS = {
  green: <CheckCircle2 className="w-4 h-4 text-emerald-500" />,
  yellow: <AlertTriangle className="w-4 h-4 text-amber-500" />,
  red: <XCircle className="w-4 h-4 text-red-500" />,
};
const BG = {
  green: 'border-emerald-200 bg-emerald-50',
  yellow: 'border-amber-200 bg-amber-50',
  red: 'border-red-200 bg-red-50',
};
const DOT = {
  ok: 'bg-emerald-500',
  configured: 'bg-emerald-500',
  disabled: 'bg-slate-300',
  down: 'bg-red-500',
  degraded: 'bg-amber-500',
};

const fmtAge = (iso) => {
  if (!iso) return 'never';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return 'unknown';
  const s = Math.floor((Date.now() - d.getTime()) / 1000);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s/60)}m ago`;
  if (s < 86400) return `${Math.floor(s/3600)}h ago`;
  return `${Math.floor(s/86400)}d ago`;
};

export default function LaunchStatusWidget() {
  const [s, setS] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const fetchStatus = async () => {
      try {
        const token = sessionStorage.getItem('session_token');
        const res = await fetch(`${API_URL}/health/launch-status`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (cancelled) return;
        if (!res.ok) {
          setError(`HTTP ${res.status}`);
          return;
        }
        const j = await res.json();
        setS(j);
        setError(null);
      } catch (e) {
        if (!cancelled) setError(e?.message || 'network error');
      }
    };
    fetchStatus();
    const id = setInterval(fetchStatus, 15000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  if (error && !s) {
    return (
      <div className="border border-red-200 bg-red-50 rounded-xl p-4 text-sm text-red-700" data-testid="launch-status-error">
        <div className="flex items-center gap-2 font-semibold mb-1"><XCircle className="w-4 h-4" /> Launch Status unavailable</div>
        <div className="text-xs">{error}</div>
      </div>
    );
  }
  if (!s) {
    return <div className="border border-slate-200 bg-white rounded-xl p-4 text-xs text-slate-400" data-testid="launch-status-loading">Loading launch status...</div>;
  }

  const overall = s.overall || 'green';
  const checks = s.checks || {};
  const dn = s.donations || {};

  return (
    <div className={`border rounded-xl p-5 ${BG[overall]}`} data-testid="launch-status-widget">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {ICONS[overall]}
          <h3 className="font-semibold text-slate-900 text-sm tracking-wide uppercase">Launch Status</h3>
        </div>
        <span className="text-xs text-slate-500" data-testid="launch-status-environment">{s.environment} · v{s.version}</span>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs mb-4">
        <Row icon={<Activity className="w-3.5 h-3.5" />} label="API" status="ok" hint={`${checks.api?.latency_ms || 0}ms`} testid="launch-status-api" />
        <Row icon={<Database className="w-3.5 h-3.5" />} label="Mongo" status={checks.mongo?.status} hint={`${checks.mongo?.latency_ms || 0}ms`} testid="launch-status-mongo" />
        <Row icon={<Zap className="w-3.5 h-3.5" />} label="Stripe webhooks" status={checks.stripe_webhooks?.status} hint={`${checks.stripe_webhooks?.received_last_hour || 0}/hr`} testid="launch-status-stripe" />
        <Row icon={<Clock className="w-3.5 h-3.5" />} label="Sentry" status={checks.sentry?.status} hint={checks.sentry?.status === 'configured' ? 'capturing' : 'add DSN'} testid="launch-status-sentry" />
      </div>

      <div className="border-t border-slate-200/60 pt-3 grid grid-cols-3 gap-3 text-xs">
        <Stat label="Last gift" value={dn.last_amount != null ? formatCurrency(dn.last_amount) : '—'} sub={fmtAge(dn.last_at)} testid="launch-status-last-gift" />
        <Stat label="Gifts (1h)" value={dn.last_hour ?? 0} sub={`${dn.last_minute ?? 0} this min`} testid="launch-status-gifts-hour" />
        <Stat label="Uptime" value={`${Math.floor((s.uptime_s || 0) / 60)}m`} sub={`since boot`} testid="launch-status-uptime" />
      </div>
    </div>
  );
}

function Row({ icon, label, status, hint, testid }) {
  return (
    <div className="flex items-center justify-between gap-2 bg-white/70 border border-slate-200/60 rounded-lg px-3 py-2" data-testid={testid}>
      <div className="flex items-center gap-2 text-slate-700">
        {icon}
        <span className="font-medium">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className={`w-1.5 h-1.5 rounded-full ${DOT[status] || 'bg-slate-300'}`} />
        <span className="text-slate-500 tabular-nums">{hint}</span>
      </div>
    </div>
  );
}

function Stat({ label, value, sub, testid }) {
  return (
    <div data-testid={testid}>
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className="text-sm font-semibold text-slate-900 mt-0.5 tabular-nums">{value}</div>
      <div className="text-[10px] text-slate-400 mt-0.5">{sub}</div>
    </div>
  );
}
