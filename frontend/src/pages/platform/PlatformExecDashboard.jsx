import { useState, useEffect, useCallback } from 'react';
import { API_URL } from '@/lib/utils';
import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { DollarSign, TrendingUp, Users, CreditCard, Building2, ArrowUpRight, Activity } from 'lucide-react';

const COLORS = ['#2563eb', '#7c3aed', '#0891b2'];
const fmt = (n) => n >= 1e6 ? `$${(n/1e6).toFixed(1)}M` : n >= 1e3 ? `$${(n/1e3).toFixed(0)}K` : `$${n.toFixed(0)}`;

export default function PlatformExecDashboard({ stats }) {
  if (!stats) return <div className="p-8 text-slate-400">Loading...</div>;
  const { giving, fees, transactions, donors, giving_trend, campus_breakdown, fee_config, platform, churches, members } = stats;

  // Hero KPIs
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
    { label: 'Total Members', value: ((members?.total || platform?.total_members || 0)).toLocaleString(), icon: Users, color: '#2563eb' },
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

      {/* Secondary Metrics Grid */}
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
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Giving by Campus</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`} labelLine={false}>
                {pieData.map((_, i) => <Cell key={`c-${i}`} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={(v) => `$${v.toLocaleString()}`} />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-2 mt-2">
            {(campus_breakdown || []).map((c, i) => (
              <div key={c.tenant_id} className="flex justify-between text-sm">
                <span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full" style={{ background: COLORS[i] }} />{c.name}</span>
                <span className="font-semibold">{fmt(c.giving)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Fees Earned (Last 12 Months)</h3>
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

      <div className="bg-white rounded-xl border border-slate-100 p-5">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">Fee Configuration</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div><span className="text-slate-500">Card Rate:</span> <span className="font-semibold">{fee_config?.card_rate} + {fee_config?.card_flat}</span></div>
          <div><span className="text-slate-500">ACH Rate:</span> <span className="font-semibold">{fee_config?.ach_rate} + {fee_config?.ach_flat}</span></div>
          <div><span className="text-slate-500">Industry:</span> <span className="font-semibold">{fee_config?.industry_rate}</span></div>
          <div><span className="text-slate-500">Savings:</span> <span className="font-bold text-emerald-600">{fee_config?.savings}</span></div>
        </div>
      </div>
    </div>
  );
}
