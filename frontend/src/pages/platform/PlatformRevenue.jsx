import { useState, useEffect } from 'react';
import { API_URL } from '@/lib/utils';
import { AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { CreditCard, Landmark } from 'lucide-react';

const fmt = (n) => n >= 1e6 ? `$${(n/1e6).toFixed(1)}M` : n >= 1e3 ? `$${(n/1e3).toFixed(0)}K` : `$${n.toFixed(0)}`;
const COLORS = ['#2563eb', '#7c3aed', '#0891b2', '#059669', '#f59e0b', '#ef4444', '#6366f1', '#ec4899'];

export default function PlatformRevenue({ token }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/platform/revenue`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : null)
      .then(d => d && setData(d));
  }, [token]);

  if (!data) return <div className="p-8 text-slate-400">Loading revenue data...</div>;

  const s = data.summary || {};
  const allVol = s.total_processing_volume || 0;
  const allFees = s.total_fees_earned || 0;
  const allTxns = s.total_transactions || 0;

  // Build by_year lookup from array
  const yearLookup = {};
  (data.by_year || []).forEach(y => { yearLookup[y.year] = y; });

  const periods = [
    { label: 'All Time', vol: allVol, fees: allFees },
    ...Object.keys(yearLookup).sort().reverse().map(yr => ({
      label: yr, vol: yearLookup[yr].total_volume || 0, fees: yearLookup[yr].total_fees || 0,
    })),
  ];

  const churchData = (data.by_church || []).map(c => ({ name: c.name, value: Math.round(c.total_fees) }));
  const trendData = (data.monthly_trend || []).map(m => ({ month: m.month, fees: Math.round(m.fees), volume: Math.round(m.volume) }));

  // Fee breakdown by type (estimated 90% card / 10% ACH)
  const cardVol = Math.round(allVol * 0.90);
  const achVol = Math.round(allVol * 0.10);
  const cardFees = Math.round(cardVol * 0.019 + allTxns * 0.9 * 0.30);
  const achFees = Math.round(achVol * 0.008 + allTxns * 0.1 * 0.30);

  return (
    <div className="space-y-4" data-testid="platform-revenue">
      <div className="bg-white rounded-xl border border-slate-100 p-5">
        <h3 className="text-sm font-semibold text-slate-700 mb-4">Fee Revenue by Period</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Period</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Gross Giving</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Fees Earned</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Fee %</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {periods.map(p => (
                <tr key={p.label} className="hover:bg-slate-50/50">
                  <td className="px-4 py-3 font-medium text-slate-800">{p.label}</td>
                  <td className="px-4 py-3 text-right text-slate-700">{fmt(p.vol)}</td>
                  <td className="px-4 py-3 text-right font-semibold text-emerald-700">{fmt(p.fees)}</td>
                  <td className="px-4 py-3 text-right text-slate-500">{p.vol > 0 ? (p.fees / p.vol * 100).toFixed(2) : 0}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Monthly Revenue Trend</h3>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={trendData}>
              <defs>
                <linearGradient id="gRev" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#059669" stopOpacity={0.15}/><stop offset="95%" stopColor="#059669" stopOpacity={0}/></linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={(v) => fmt(v)} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v) => `$${v.toLocaleString()}`} />
              <Area type="monotone" dataKey="fees" stroke="#059669" fill="url(#gRev)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Revenue by Church</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={churchData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, percent }) => `${name.split(' ').slice(0, 2).join(' ')} ${(percent*100).toFixed(0)}%`} labelLine={false}>
                {churchData.map((_, i) => <Cell key={`rc-${i}`} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={(v) => `$${v.toLocaleString()}`} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Revenue by Church</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-slate-600">Church</th>
                  <th className="px-4 py-2 text-right font-medium text-slate-600">Volume</th>
                  <th className="px-4 py-2 text-right font-medium text-slate-600">Fees</th>
                  <th className="px-4 py-2 text-right font-medium text-slate-600">%</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {(data.by_church || []).map(c => (
                  <tr key={c.tenant_id}>
                    <td className="px-4 py-2 font-medium text-slate-800">{c.name}</td>
                    <td className="px-4 py-2 text-right text-slate-700">{fmt(c.total_volume)}</td>
                    <td className="px-4 py-2 text-right font-semibold text-emerald-700">{fmt(c.total_fees)}</td>
                    <td className="px-4 py-2 text-right text-slate-500">{allFees > 0 ? (c.total_fees / allFees * 100).toFixed(0) : 0}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">Fee Breakdown by Type</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
              <div className="flex items-center gap-2"><CreditCard className="w-5 h-5 text-blue-600" /><span className="font-medium text-slate-800">Card (1.9% + $0.30)</span></div>
              <div className="text-right"><div className="font-bold text-slate-900">{fmt(cardFees)}</div><div className="text-xs text-slate-500">{fmt(cardVol)} volume (90%)</div></div>
            </div>
            <div className="flex justify-between items-center p-3 bg-emerald-50 rounded-lg">
              <div className="flex items-center gap-2"><Landmark className="w-5 h-5 text-emerald-600" /><span className="font-medium text-slate-800">ACH (0.8% + $0.30)</span></div>
              <div className="text-right"><div className="font-bold text-slate-900">{fmt(achFees)}</div><div className="text-xs text-slate-500">{fmt(achVol)} volume (10%)</div></div>
            </div>
            <div className="flex justify-between items-center p-3 bg-slate-100 rounded-lg border-t-2 border-slate-300">
              <span className="font-bold text-slate-900">Total Platform Revenue</span>
              <span className="text-xl font-bold text-emerald-700">{fmt(allFees)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
