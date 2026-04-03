import { useState, useEffect } from 'react';
import { API_URL } from '@/lib/utils';
import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { DollarSign, TrendingUp, Users, CreditCard, Building2, ArrowUpRight, Activity, AlertTriangle, ChevronRight } from 'lucide-react';

const COLORS = ['#2563eb', '#7c3aed', '#0891b2', '#059669', '#dc2626', '#f59e0b', '#0891b2'];
const fmt = (n) => {
  const v = Number(n ?? 0);
  if (isNaN(v)) return '$0';
  return v >= 1e6 ? `$${(v/1e6).toFixed(1)}M` : v >= 1e3 ? `$${(v/1e3).toFixed(0)}K` : `$${v.toFixed(0)}`;
};

function AttentionRequired({ token }) {
  const [flagged, setFlagged] = useState([]);

  useEffect(() => {
    if (!token) return;
    fetch(`${API_URL}/platform/health-scores`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) return;
        const churches = (data.churches || data || []);
        const atRisk = churches
          .filter(c => {
            const grade = c.health?.grade;
            return grade && ['C', 'D', 'F'].includes(grade.charAt(0));
          })
          .slice(0, 5)
          .map(c => {
            const dims = c.health?.dimensions || {};
            // Find the weakest dimension
            const weakest = Object.values(dims).sort((a, b) => a.score - b.score)[0];
            let metric = 'Needs attention';
            if (weakest) {
              if (weakest.label.includes('Giving')) metric = `Giving per member below target (${weakest.value}$/mo)`;
              else if (weakest.label.includes('Engagement')) metric = `Engagement rate low (${weakest.value}%)`;
              else if (weakest.label.includes('Attendance')) metric = `Attendance rate at ${weakest.value}%`;
              else if (weakest.label.includes('Recurring')) metric = `Recurring donors at ${weakest.value}%`;
              else if (weakest.label.includes('Groups')) metric = `Group participation low (${weakest.value}/100)`;
            }
            return { ...c, metric };
          });
        setFlagged(atRisk);
      })
      .catch(() => {});
  }, [token]);

  if (flagged.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-100 p-5" data-testid="attention-required">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-7 h-7 rounded-lg bg-emerald-50 flex items-center justify-center">
            <Activity className="w-4 h-4 text-emerald-600" />
          </div>
          <h3 className="text-sm font-semibold text-slate-700">Portfolio Health</h3>
        </div>
        <div className="text-center py-6">
          <div className="w-12 h-12 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-2">
            <Activity className="w-6 h-6 text-emerald-500" />
          </div>
          <p className="text-sm font-medium text-emerald-700">All churches healthy</p>
          <p className="text-xs text-slate-400 mt-0.5">No churches currently need attention</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-red-200 p-5" data-testid="attention-required">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-7 h-7 rounded-lg bg-red-50 flex items-center justify-center">
          <AlertTriangle className="w-4 h-4 text-red-600" />
        </div>
        <h3 className="text-sm font-semibold text-slate-700">Attention Required</h3>
        <span className="ml-auto text-xs font-semibold bg-red-100 text-red-700 px-2 py-0.5 rounded-full">{flagged.length}</span>
      </div>
      <div className="space-y-2">
        {flagged.map(c => {
          const grade = c.health?.grade || '?';
          const score = c.health?.score || 0;
          const isRed = ['D', 'F'].includes(grade.charAt(0));
          return (
            <div
              key={c.tenant_id}
              className="flex items-center gap-3 p-3 rounded-xl border transition-all hover:shadow-sm cursor-pointer"
              style={{ borderColor: isRed ? '#fca5a5' : '#fde68a', background: isRed ? '#fff5f5' : '#fffbeb' }}
              data-testid={`attention-church-${c.tenant_id}`}
            >
              <div
                className="w-9 h-9 rounded-lg flex items-center justify-center font-bold text-sm flex-shrink-0"
                style={{ background: isRed ? '#fee2e2' : '#fef3c7', color: isRed ? '#dc2626' : '#d97706' }}
              >
                {grade}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-slate-900 truncate">{c.name}</p>
                <p className="text-xs text-slate-500 truncate">{c.metric}</p>
              </div>
              <div className="flex items-center gap-1 text-xs font-medium flex-shrink-0" style={{ color: isRed ? '#dc2626' : '#d97706' }}>
                {score}
                <ChevronRight className="w-3.5 h-3.5" />
              </div>
            </div>
          );
        })}
      </div>
      <p className="text-xs text-slate-400 mt-3">Click a church to view detailed health breakdown in the Churches tab.</p>
    </div>
  );
}

export default function PlatformExecDashboard({ stats, token }) {
  if (!stats) return <div className="p-8 text-slate-400">Loading...</div>;
  const { giving, fees, transactions, donors, giving_trend, campus_breakdown, fee_config, platform, churches, members } = stats;

  const heroKPIs = [
    { label: 'Platform GMV (All Time)', value: fmt(giving?.all_time || 0), sub: 'Total giving processed', color: '#2563eb' },
    { label: 'Platform Revenue (All Time)', value: fmt(fees?.all_time || 0), sub: 'Solomon Pay fees earned', color: '#059669' },
    { label: 'MRR', value: fmt(platform?.total_mrr || 0), sub: 'Monthly recurring revenue', color: '#7c3aed' },
    { label: 'ARR', value: fmt(platform?.arr || 0), sub: 'Annual recurring revenue', color: '#0891b2' },
  ];

  const metrics = [
    { label: 'YTD Giving', value: fmt(giving?.ytd || 0), sub: `${giving?.yoy_change > 0 ? '+' : ''}${giving?.yoy_change || 0}% YoY`, icon: ArrowUpRight, color: '#7c3aed' },
    { label: 'YTD Revenue', value: fmt(fees?.ytd || 0), icon: TrendingUp, color: '#059669' },
    { label: 'This Month', value: fmt(giving?.mtd || 0), icon: Activity, color: '#0891b2' },
    { label: 'MTD Revenue', value: fmt(fees?.mtd || 0), icon: CreditCard, color: '#059669' },
    { label: 'Total Transactions', value: (transactions?.total || 0).toLocaleString(), icon: CreditCard, color: '#6366f1' },
    { label: 'Total Donors', value: (donors?.total || 0).toLocaleString(), icon: Users, color: '#0891b2' },
    { label: 'Active Churches', value: churches?.active || 0, icon: Building2, color: '#7c3aed' },
    { label: 'Total Members', value: (members?.total || platform?.total_members || 0).toLocaleString(), icon: Users, color: '#2563eb' },
    { label: 'Avg Transaction', value: `$${transactions?.avg_amount || 0}`, icon: DollarSign, color: '#f59e0b' },
    { label: 'Today Giving', value: fmt(giving?.today || 0), icon: DollarSign, color: '#2563eb' },
    { label: 'Today Revenue', value: fmt(fees?.today || 0), icon: TrendingUp, color: '#059669' },
    { label: 'This Week', value: fmt(giving?.wtd || 0), icon: Activity, color: '#0891b2' },
  ];

  const trendData = (giving_trend || []).map(m => ({
    month: m.month,
    giving: Math.round(m.total_giving || 0),
    fees: Math.round(m.total_fees || 0),
    txns: m.txn_count || 0,
    ...Object.fromEntries(Object.entries(m.by_campus || {}).map(([k, v]) => [k, Math.round(v || 0)])),
  }));

  const pieData = (campus_breakdown || []).map(c => ({ name: c.name, value: Math.round(c.giving || 0) }));

  return (
    <div className="space-y-6">
      {/* Hero KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4" data-testid="hero-kpis">
        {heroKPIs.map((k, i) => (
          <div key={k.label} className="bg-white rounded-xl border border-slate-100 p-5 hover:shadow-md transition-shadow" data-testid={`hero-kpi-${i}`}>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">{k.label}</p>
            <p className="text-3xl font-bold tracking-tight" style={{ color: k.color }}>{k.value}</p>
            <p className="text-xs text-slate-400 mt-1">{k.sub}</p>
          </div>
        ))}
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3" data-testid="exec-metrics-grid">
        {metrics.map((m, i) => (
          <div key={m.label} className="bg-white rounded-xl border border-slate-100 p-4 hover:shadow-md transition-shadow" data-testid={`metric-${i}`}>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${m.color}15` }}>
                <m.icon className="w-4 h-4" style={{ color: m.color }} />
              </div>
            </div>
            <div className="text-xl font-bold text-slate-900">{m.value}</div>
            <div className="text-xs text-slate-500 mt-0.5">{m.label}</div>
            {m.sub && <div className="text-xs font-semibold mt-1" style={{ color: (giving?.yoy_change || 0) >= 0 ? '#059669' : '#dc2626' }}>{m.sub}</div>}
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Giving Trend (Last 12 Months)</h3>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={trendData}>
              <defs>
                <linearGradient id="gGiving" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#2563eb" stopOpacity={0.15}/><stop offset="95%" stopColor="#2563eb" stopOpacity={0}/></linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={(v) => fmt(v)} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => `$${v.toLocaleString()}`} />
              <Area type="monotone" dataKey="giving" stroke="#2563eb" fill="url(#gGiving)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Giving by Church</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, percent }) => `${name.split(' ')[0]} ${(percent*100).toFixed(0)}%`} labelLine={false}>
                {pieData.map((_, i) => <Cell key={`c-${i}`} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={(v) => `$${v.toLocaleString()}`} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Secondary Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Revenue Trend (Last 12 Months)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={trendData}>
              <defs>
                <linearGradient id="gFees" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#059669" stopOpacity={0.15}/><stop offset="95%" stopColor="#059669" stopOpacity={0}/></linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={(v) => fmt(v)} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => `$${v.toLocaleString()}`} />
              <Area type="monotone" dataKey="fees" stroke="#059669" fill="url(#gFees)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Transaction Volume</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => v.toLocaleString()} />
              <Bar dataKey="txns" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row 4: Activity Feed + Attention Required */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Church Portfolio Summary</h3>
          {(campus_breakdown || []).length === 0 ? (
            <p className="text-sm text-slate-400 py-4 text-center">No activity</p>
          ) : (
            <div className="space-y-2">
              {(campus_breakdown || []).slice(0, 6).map((c, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-slate-50">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-xs font-bold text-blue-700">{c.name?.charAt(0)}</div>
                    <div>
                      <p className="text-sm font-medium text-slate-800">{c.name}</p>
                      <p className="text-xs text-slate-400">{(c.txn_count || 0).toLocaleString()} txns</p>
                    </div>
                  </div>
                  <span className="text-sm font-semibold text-slate-900">{fmt(c.giving)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
        <AttentionRequired token={token} />
      </div>

      {/* Fee Config */}
      <div className="bg-white rounded-xl border border-slate-100 p-5">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">Solomon Pay Fee Configuration</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div><span className="text-slate-500">Card Rate:</span> <span className="font-semibold">{fee_config?.card_rate} + {fee_config?.card_flat}</span></div>
          <div><span className="text-slate-500">ACH Rate:</span> <span className="font-semibold">{fee_config?.ach_rate} + {fee_config?.ach_flat}</span></div>
          <div><span className="text-slate-500">Industry Avg:</span> <span className="font-semibold">{fee_config?.industry_rate}</span></div>
          <div><span className="text-slate-500">Our Advantage:</span> <span className="font-bold text-emerald-600">{fee_config?.savings}</span></div>
        </div>
      </div>
    </div>
  );
}
