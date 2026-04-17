import { useState, useEffect } from 'react';
import { API_URL } from '@/lib/utils';
import { ArrowLeft, Building2, Users, DollarSign, CreditCard, Activity, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const fmt = (n) => {
  const v = Number(n ?? 0);
  return v >= 1e6 ? `$${(v/1e6).toFixed(1)}M` : v >= 1e3 ? `$${(v/1e3).toFixed(1)}K` : `$${v.toFixed(0)}`;
};

const GRADE_COLORS = {
  'A+': '#16a34a', 'A': '#16a34a', 'B+': '#2563eb', 'B': '#2563eb',
  'C': '#f59e0b', 'D': '#dc2626', 'F': '#dc2626', 'N/A': '#94a3b8',
};

export default function ChurchDetail({ token, tenantId, onBack }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tenantId) return;
    setLoading(true);
    fetch(`${API_URL}/platform/churches/${tenantId}/detail`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setData(d); })
      .finally(() => setLoading(false));
  }, [tenantId, token]);

  if (loading) return <div className="p-8 text-slate-400" data-testid="church-detail-loading">Loading church detail...</div>;
  if (!data) return <div className="p-8 text-red-500">Failed to load church data</div>;

  const { church, health, summary, monthly_giving, top_donors, recent_transactions, members } = data;
  const grade = health?.grade || 'N/A';
  const gradeColor = GRADE_COLORS[grade] || '#94a3b8';

  return (
    <div className="space-y-4" data-testid="church-detail-page">
      {/* Back button + header */}
      <div className="flex items-center gap-4">
        <button onClick={onBack} className="p-2 rounded-lg hover:bg-slate-100 transition-colors" data-testid="church-detail-back">
          <ArrowLeft className="w-5 h-5 text-slate-600" />
        </button>
        <div className="flex-1">
          <h2 className="text-xl font-bold text-slate-900">{church.name}</h2>
          {church.city && <p className="text-sm text-slate-500">{church.address || `${church.city}, ${church.state}`} · {church.plan} plan</p>}
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-xl border" style={{ borderColor: gradeColor + '40', background: gradeColor + '10' }}>
          <Activity className="w-5 h-5" style={{ color: gradeColor }} />
          <span className="text-2xl font-bold" style={{ color: gradeColor }}>{grade}</span>
          <span className="text-sm text-slate-500">{health?.score || 0}/100</span>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Total Members', value: (summary.total_members || 0).toLocaleString(), icon: Users, color: '#2563eb' },
          { label: 'Total Giving', value: fmt(summary.total_giving), icon: DollarSign, color: '#059669' },
          { label: 'Transactions', value: (summary.total_transactions || 0).toLocaleString(), icon: CreditCard, color: '#7c3aed' },
          { label: 'Active Donors (90d)', value: (summary.active_donors_90d || 0).toLocaleString(), icon: TrendingUp, color: '#f59e0b' },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-xl border border-slate-100 p-4">
            <div className="flex items-center gap-2 mb-1">
              <s.icon className="w-4 h-4" style={{ color: s.color }} />
              <span className="text-xs text-slate-500">{s.label}</span>
            </div>
            <div className="text-xl font-bold text-slate-900">{s.value}</div>
          </div>
        ))}
      </div>

      {/* Health dimensions */}
      {health?.dimensions && (
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Health Score Breakdown</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.values(health.dimensions).map(dim => (
              <div key={dim.label} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">{dim.label}</span>
                  <span className="font-medium text-slate-700">{dim.value}{dim.unit}</span>
                </div>
                <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div className="h-full rounded-full transition-all" style={{ width: `${dim.score}%`, background: dim.score >= 70 ? '#16a34a' : dim.score >= 50 ? '#2563eb' : dim.score >= 30 ? '#f59e0b' : '#dc2626' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 12-month giving chart */}
      <div className="bg-white rounded-xl border border-slate-100 p-5">
        <h3 className="text-sm font-semibold text-slate-700 mb-4">12-Month Giving Trend</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={monthly_giving}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="month" tick={{ fontSize: 11 }} tickFormatter={m => m?.slice(5)} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={v => v >= 1e6 ? `$${(v/1e6).toFixed(1)}M` : `$${(v/1e3).toFixed(0)}K`} />
            <Tooltip formatter={(v) => `$${Number(v).toLocaleString()}`} />
            <Bar dataKey="total" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Top Donors */}
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Top Donors (All-Time)</h3>
          <div className="space-y-2">
            {(top_donors || []).map((d, i) => (
              <div key={d.person_id || i} className="flex items-center justify-between py-1.5 border-b border-slate-50 last:border-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 w-5">{i + 1}</span>
                  <span className="text-sm font-medium text-slate-800">{d.name?.trim() || 'Member'}</span>
                </div>
                <div className="text-right">
                  <span className="text-sm font-bold text-emerald-700">{fmt(d.total)}</span>
                  <span className="text-xs text-slate-400 ml-1">({d.count} gifts)</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Member Roster */}
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Top Members (by Giving)</h3>
          <div className="space-y-2 max-h-[320px] overflow-y-auto">
            {(members || []).map((m, i) => (
              <div key={m.id || i} className="flex items-center justify-between py-1.5 border-b border-slate-50 last:border-0">
                <div>
                  <div className="text-sm font-medium text-slate-800">{m.first_name} {m.last_name}</div>
                  <div className="text-xs text-slate-400">{m.email}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold text-slate-700">{fmt(m.lifetime_giving || 0)}</div>
                  <div className="text-xs text-slate-400">{m.membership_status}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100">
          <h3 className="text-sm font-semibold text-slate-700">Recent Transactions</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid="church-detail-transactions">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-slate-600">Date</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-slate-600">Donor</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-slate-600">Amount</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-slate-600">Fund</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-slate-600">Method</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-slate-600">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {(recent_transactions || []).map((t, i) => (
                <tr key={i} className="hover:bg-slate-50/50">
                  <td className="px-4 py-2 text-slate-600">{t.donation_date}</td>
                  <td className="px-4 py-2 font-medium text-slate-800">{t.person_name}</td>
                  <td className="px-4 py-2 text-right font-semibold text-slate-900">${Number(t.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                  <td className="px-4 py-2 text-slate-600">{t.fund_name}</td>
                  <td className="px-4 py-2 text-slate-500 capitalize">{t.payment_method}</td>
                  <td className="px-4 py-2"><span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700">{t.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
