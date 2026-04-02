import { useState, useEffect } from 'react';
import { API_URL } from '@/lib/utils';
import { Users, UserCheck, Repeat, UserPlus, UserMinus, DollarSign, TrendingUp, BarChart3 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function PlatformDonors({ token }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/platform/donors/stats`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : null)
      .then(d => d && setData(d));
  }, [token]);

  if (!data) return <div className="p-8 text-slate-400">Loading donor analytics...</div>;

  const metrics = [
    { label: 'Total Donors', value: data.total_donors?.toLocaleString(), icon: Users, color: '#2563eb' },
    { label: 'Active (90d)', value: data.active_donors?.toLocaleString(), icon: UserCheck, color: '#059669' },
    { label: 'Recurring', value: data.recurring_donors?.toLocaleString(), icon: Repeat, color: '#7c3aed' },
    { label: 'First-Time (30d)', value: data.first_time_donors_30d?.toLocaleString(), icon: UserPlus, color: '#f59e0b' },
    { label: 'Lapsed (90d+)', value: data.lapsed_donors?.toLocaleString(), icon: UserMinus, color: '#ef4444' },
    { label: 'Avg Gift', value: `$${data.avg_gift}`, icon: DollarSign, color: '#0891b2' },
    { label: 'Avg LTV', value: `$${Math.round(data.avg_lifetime_value).toLocaleString()}`, icon: TrendingUp, color: '#059669' },
    { label: 'Retention (YoY)', value: `${data.retention_rate_yoy}%`, icon: BarChart3, color: '#6366f1' },
  ];

  const stageData = Object.entries(data.donor_stages || {}).map(([k, v]) => ({
    name: k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    count: v,
  }));

  const COLORS = { 'First Time': '#3b82f6', 'Occasional': '#f59e0b', 'Regular': '#8b5cf6', 'Recurring': '#059669', 'At Risk': '#f97316', 'Lapsed': '#ef4444' };

  return (
    <div className="space-y-4" data-testid="platform-donors">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {metrics.map(m => (
          <div key={m.label} className="bg-white rounded-xl border border-slate-100 p-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${m.color}15` }}>
                <m.icon className="w-4 h-4" style={{ color: m.color }} />
              </div>
            </div>
            <div className="text-xl font-bold text-slate-900">{m.value}</div>
            <div className="text-xs text-slate-500">{m.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">DonorIQ Stage Distribution</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={stageData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} width={100} />
              <Tooltip formatter={(v) => v.toLocaleString()} />
              <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                {stageData.map((entry) => (
                  <BarChart key={entry.name}>
                    <Bar fill={COLORS[entry.name] || '#94a3b8'} />
                  </BarChart>
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Donors by Campus</h3>
          <div className="space-y-4">
            {Object.entries(data.by_campus || {}).sort(([,a],[,b]) => b - a).map(([tid, count]) => {
              const names = { 'abundant-east-001': 'Abundant East', 'abundant-west-001': 'Abundant West', 'abundant-downtown-001': 'Abundant Downtown' };
              const pct = Math.round(count / Math.max(data.total_donors, 1) * 100);
              return (
                <div key={tid}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium text-slate-700">{names[tid] || tid}</span>
                    <span className="text-slate-500">{count.toLocaleString()} ({pct}%)</span>
                  </div>
                  <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-6 p-4 bg-slate-50 rounded-lg">
            <h4 className="text-sm font-semibold text-slate-700 mb-2">Key Insights</h4>
            <ul className="space-y-1 text-sm text-slate-600">
              <li>Donor retention rate: <strong>{data.retention_rate_yoy}%</strong> year-over-year</li>
              <li>Average donor gives <strong>${data.avg_gift}</strong> per transaction</li>
              <li>Lifetime value per donor: <strong>${Math.round(data.avg_lifetime_value).toLocaleString()}</strong></li>
              <li>{data.recurring_donors?.toLocaleString()} donors on recurring giving</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
