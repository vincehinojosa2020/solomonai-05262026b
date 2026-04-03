import { useState, useEffect } from 'react';
import { API_URL } from '@/lib/utils';
import { Building2, DollarSign, Users, MapPin, TrendingUp, TrendingDown, Activity } from 'lucide-react';

const fmt = (n) => {
  const v = Number(n ?? 0);
  if (isNaN(v)) return '$0';
  return v >= 1e6 ? `$${(v/1e6).toFixed(1)}M` : v >= 1e3 ? `$${(v/1e3).toFixed(0)}K` : `$${v.toFixed(0)}`;
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
    };
  });

  return (
    <div className="space-y-4" data-testid="platform-churches">
      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Total Churches', value: enriched.length, icon: Building2, color: '#2563eb' },
          { label: 'Avg Health Score', value: `${Math.round(Object.values(healthScores).reduce((a, h) => a + (h?.score || 0), 0) / Math.max(Object.keys(healthScores).length, 1))}`, icon: Activity, color: '#059669' },
          { label: 'Total Giving (All Tenants)', value: fmt(enriched.reduce((a, c) => a + (c.giving || 0), 0)), icon: DollarSign, color: '#7c3aed' },
          { label: 'Total Transactions', value: enriched.reduce((a, c) => a + (c.txn_count || 0), 0).toLocaleString(), icon: TrendingUp, color: '#0891b2' },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-xl border border-slate-100 p-4">
            <div className="flex items-center gap-2 mb-1">
              <s.icon className="w-4 h-4" style={{ color: s.color }} />
              <span className="text-xs text-slate-500">{s.label}</span>
            </div>
            <div className="text-2xl font-bold text-slate-900">{s.value}</div>
          </div>
        ))}
      </div>

      {/* Church Portfolio Table */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-semibold text-slate-800">Church Portfolio</h3>
          <span className="text-xs text-slate-400">Click a row to see health breakdown</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid="church-portfolio-table">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Church</th>
                <th className="px-5 py-3 text-right font-medium text-slate-600">Members</th>
                <th className="px-5 py-3 text-right font-medium text-slate-600">All-Time Giving</th>
                <th className="px-5 py-3 text-right font-medium text-slate-600">Fees Earned</th>
                <th className="px-5 py-3 text-right font-medium text-slate-600">Transactions</th>
                <th className="px-5 py-3 text-center font-medium text-slate-600">Health Score</th>
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
                      <td className="px-5 py-3 text-right text-slate-700">{num(c.total_members || c.members || 0)}</td>
                      <td className="px-5 py-3 text-right font-semibold text-slate-900">{fmt(c.giving)}</td>
                      <td className="px-5 py-3 text-right text-emerald-700 font-medium">{fmt(c.fees)}</td>
                      <td className="px-5 py-3 text-right text-slate-700">{(c.txn_count || 0).toLocaleString()}</td>
                      <td className="px-5 py-3 text-center">
                        {health ? (
                          <HealthBadge grade={health.grade} score={health.score} />
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>
                    </tr>
                    {isExpanded && health?.dimensions && (
                      <tr key={`${c.id}-expanded`} className="bg-slate-50/50">
                        <td colSpan={6} className="px-5 py-4">
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
