import { useState, useEffect } from 'react';
import { API_URL } from '@/lib/utils';
import { Building2, DollarSign, Users, MapPin, TrendingUp, TrendingDown, Activity, Eye, CheckCircle2, Clock, XCircle } from 'lucide-react';
import ChurchStripeDrawer from './ChurchStripeDrawer';

const STATUS_META = {
  connected:     { label: 'Connected',     icon: CheckCircle2, bg: 'bg-emerald-50',  text: 'text-emerald-700', dot: 'bg-emerald-500' },
  pending:       { label: 'Pending',       icon: Clock,        bg: 'bg-amber-50',    text: 'text-amber-700',   dot: 'bg-amber-500' },
  not_connected: { label: 'Not Connected', icon: XCircle,      bg: 'bg-slate-100',   text: 'text-slate-600',   dot: 'bg-slate-400' },
};

function StripeStatusBadge({ status }) {
  const meta = STATUS_META[status] || STATUS_META.not_connected;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${meta.bg} ${meta.text}`}
      data-testid={`stripe-status-${status}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />
      {meta.label}
    </span>
  );
}

const fmt = (n) => {
  const v = Number(n ?? 0);
  if (isNaN(v)) return '$0';
  return v >= 1e6 ? `$${(v/1e6).toFixed(1)}M` : v >= 1e3 ? `$${(v/1e3).toFixed(0)}K` : `$${v.toFixed(0)}`;
};
const fmtCents = (c) => {
  const v = Number(c ?? 0) / 100;
  if (v >= 1e6) return `$${(v/1e6).toFixed(1)}M`;
  if (v >= 1e3) return `$${(v/1e3).toFixed(0)}K`;
  return `$${v.toFixed(0)}`;
};
const num = (n) => { const v = Number(n ?? 0); return v >= 1e3 ? `${(v/1e3).toFixed(1)}K` : `${v}`; };

const GRADE_CONFIG = {
  'A+': { bg: '#dcfce7', text: '#15803d', border: '#86efac' },
  'A':  { bg: '#dcfce7', text: '#15803d', border: '#86efac' },
  'B+': { bg: '#dbeafe', text: '#1d4ed8', border: '#93c5fd' },
  'B':  { bg: '#dbeafe', text: '#1d4ed8', border: '#93c5fd' },
  'C':  { bg: '#fef9c3', text: '#92400e', border: '#fde68a' },
  'D':  { bg: '#fee2e2', text: '#dc2626', border: '#fca5a5' },
  'F':  { bg: '#fee2e2', text: '#dc2626', border: '#fca5a5' },
  'N/A':{ bg: '#f1f5f9', text: '#64748b', border: '#e2e8f0' },
};

function HealthBadge({ grade, score }) {
  const cfg = GRADE_CONFIG[grade] || GRADE_CONFIG['N/A'];
  return (
    <div
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-bold text-sm border"
      style={{ background: cfg.bg, color: cfg.text, borderColor: cfg.border }}
      title={`Health Score: ${score}/100`}
    >
      {grade} <span className="font-normal text-xs opacity-70">{score}</span>
    </div>
  );
}

function ScoreDimension({ label, value, unit, score }) {
  return (
    <div className="space-y-0.5">
      <div className="flex justify-between text-xs">
        <span className="text-slate-500">{label}</span>
        <span className="font-medium text-slate-700">{value}{unit}</span>
      </div>
      <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${score}%`, background: score >= 70 ? '#16a34a' : score >= 50 ? '#2563eb' : score >= 30 ? '#f59e0b' : '#dc2626' }}
        />
      </div>
    </div>
  );
}

export default function PlatformChurches({ token, stats }) {
  const [healthScores, setHealthScores] = useState({});
  const [expandedChurch, setExpandedChurch] = useState(null);
  const [allChurches, setAllChurches] = useState([]);
  const [drawerChurch, setDrawerChurch] = useState(null);
  const campuses = stats?.campus_breakdown || [];

  useEffect(() => {
    fetchHealthScores();
    fetchAllChurches();
  }, [token]);

  const fetchHealthScores = async () => {
    try {
      const res = await fetch(`${API_URL}/platform/health-scores`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const map = {};
        (data.churches || []).forEach(c => { map[c.tenant_id] = c.health; });
        setHealthScores(map);
      }
    } catch (e) { console.error(e); }
  };

  const fetchAllChurches = async () => {
    try {
      const res = await fetch(`${API_URL}/platform/churches`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAllChurches(data.churches || []);
      }
    } catch (e) {
      // Fallback to campus_breakdown
      setAllChurches(campuses.map(c => ({ ...c, id: c.tenant_id })));
    }
  };

  const churches = allChurches.length > 0 ? allChurches : campuses.map(c => ({ ...c, id: c.tenant_id }));

  if (!campuses.length && !churches.length) return <div className="p-8 text-slate-400">Loading churches...</div>;

  // Merge campus giving data with church list
  const enriched = churches.map(c => {
    const giving_data = campuses.find(cp => cp.tenant_id === (c.id || c.tenant_id));
    return {
      ...c,
      id: c.id || c.tenant_id,
      giving: giving_data?.giving || c.giving || 0,
      fees: giving_data?.fees || c.fees || 0,
      txn_count: giving_data?.txn_count || c.txn_count || 0,
      health: healthScores[c.id || c.tenant_id],
      stripe_status: c.stripe_status || 'not_connected',
      stripe_total_processed: c.stripe_total_processed || 0,
      stripe_txn_count: c.stripe_txn_count || 0,
    };
  });

  // Stripe status summary for header
  const statusCounts = enriched.reduce((acc, c) => {
    acc[c.stripe_status] = (acc[c.stripe_status] || 0) + 1;
    return acc;
  }, {});
  const totalStripeProcessed = enriched.reduce((a, c) => a + (c.stripe_total_processed || 0), 0);

  return (
    <div className="space-y-4" data-testid="platform-churches">
      {drawerChurch && (
        <ChurchStripeDrawer church={drawerChurch} token={token} onClose={() => setDrawerChurch(null)} />
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Total Churches', value: enriched.length, icon: Building2, color: '#2563eb' },
          { label: 'Stripe Connected', value: `${statusCounts.connected || 0}/${enriched.length}`, icon: Activity, color: '#10b981', sub: `${statusCounts.pending || 0} pending · ${statusCounts.not_connected || 0} offline` },
          { label: 'Stripe Processed', value: fmtCents(totalStripeProcessed), icon: DollarSign, color: '#6366f1', sub: 'Lifetime real-card volume' },
          { label: 'All-Time Giving', value: fmt(enriched.reduce((a, c) => a + (c.giving || 0), 0)), icon: TrendingUp, color: '#7c3aed' },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-xl border border-slate-100 p-4" data-testid={`churches-summary-${s.label.toLowerCase().replace(/\s+/g, '-')}`}>
            <div className="flex items-center gap-2 mb-1">
              <s.icon className="w-4 h-4" style={{ color: s.color }} />
              <span className="text-xs text-slate-500">{s.label}</span>
            </div>
            <div className="text-2xl font-bold text-slate-900">{s.value}</div>
            {s.sub && <div className="text-[10px] text-slate-400 mt-0.5">{s.sub}</div>}
          </div>
        ))}
      </div>

      {/* Church Portfolio Table */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-semibold text-slate-800">Church Portfolio</h3>
          <span className="text-xs text-slate-400">Click a row to see health breakdown · eye icon for Stripe details</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid="church-portfolio-table">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Church</th>
                <th className="px-5 py-3 text-center font-medium text-slate-600">Stripe</th>
                <th className="px-5 py-3 text-right font-medium text-slate-600">Stripe Processed</th>
                <th className="px-5 py-3 text-right font-medium text-slate-600">Members</th>
                <th className="px-5 py-3 text-right font-medium text-slate-600">All-Time Giving</th>
                <th className="px-5 py-3 text-right font-medium text-slate-600">Transactions</th>
                <th className="px-5 py-3 text-center font-medium text-slate-600">Health</th>
                <th className="px-5 py-3 text-center font-medium text-slate-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {enriched.map(c => {
                const health = c.health;
                const isExpanded = expandedChurch === c.id;
                return (
                  <>
                    <tr
                      key={c.id}
                      className="hover:bg-slate-50/50 cursor-pointer"
                      onClick={() => setExpandedChurch(isExpanded ? null : c.id)}
                      data-testid={`church-row-${c.id}`}
                    >
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-blue-600 flex-shrink-0" />
                          <div>
                            <div className="font-medium text-slate-800">{c.name}</div>
                            {c.city && <div className="text-xs text-slate-400">{c.city}, {c.state}</div>}
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-3 text-center">
                        <StripeStatusBadge status={c.stripe_status} />
                      </td>
                      <td className="px-5 py-3 text-right font-semibold text-indigo-700">{fmtCents(c.stripe_total_processed)}</td>
                      <td className="px-5 py-3 text-right text-slate-700">{num(c.total_members || c.members || 0)}</td>
                      <td className="px-5 py-3 text-right font-semibold text-slate-900">{fmt(c.giving)}</td>
                      <td className="px-5 py-3 text-right text-slate-700">{(c.txn_count || 0).toLocaleString()}</td>
                      <td className="px-5 py-3 text-center">
                        {health ? (
                          <HealthBadge grade={health.grade} score={health.score} />
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-center">
                        <button
                          onClick={(e) => { e.stopPropagation(); setDrawerChurch(c); }}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md border border-slate-200 hover:border-slate-900 hover:bg-slate-900 hover:text-white transition-colors text-xs font-medium text-slate-600"
                          data-testid={`church-view-${c.id}`}
                        >
                          <Eye className="w-3 h-3" />
                          View
                        </button>
                      </td>
                    </tr>
                    {isExpanded && health?.dimensions && (
                      <tr key={`${c.id}-expanded`} className="bg-slate-50/50">
                        <td colSpan={8} className="px-5 py-4">
                          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 max-w-3xl">
                            {Object.values(health.dimensions).map(dim => (
                              <ScoreDimension
                                key={dim.label}
                                label={dim.label}
                                value={dim.value}
                                unit={dim.unit}
                                score={dim.score}
                              />
                            ))}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
