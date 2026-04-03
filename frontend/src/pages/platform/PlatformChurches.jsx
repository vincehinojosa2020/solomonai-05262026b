import { API_URL } from '@/lib/utils';
import { Building2, DollarSign, Users, MapPin } from 'lucide-react';

const fmt = (n) => n >= 1e6 ? `$${(n/1e6).toFixed(1)}M` : n >= 1e3 ? `$${(n/1e3).toFixed(0)}K` : `$${n.toFixed(0)}`;
const num = (n) => n >= 1e3 ? `${(n/1e3).toFixed(1)}K` : `${n}`;

export default function PlatformChurches({ token, stats }) {
  const campuses = stats?.campus_breakdown || [];

  if (!campuses.length) return <div className="p-8 text-slate-400">Loading churches...</div>;

  return (
    <div className="space-y-4" data-testid="platform-churches">
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Church</th>
                <th className="px-5 py-3 text-right font-medium text-slate-600">Giving (All Time)</th>
                <th className="px-5 py-3 text-right font-medium text-slate-600">Fees Earned</th>
                <th className="px-5 py-3 text-right font-medium text-slate-600">Transactions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {campuses.map(c => (
                <tr key={c.tenant_id} className="hover:bg-slate-50/50">
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <Building2 className="w-4 h-4 text-blue-600" />
                      <span className="font-medium text-slate-800">{c.name}</span>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-right font-semibold text-slate-900">{fmt(c.giving)}</td>
                  <td className="px-5 py-3 text-right text-emerald-700 font-medium">{fmt(c.fees)}</td>
                  <td className="px-5 py-3 text-right text-slate-700">{(c.txn_count || 0).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {campuses.map(c => (
          <div key={c.tenant_id} className="bg-white rounded-xl border border-slate-100 p-5">
            <div className="flex items-center gap-2 mb-3">
              <MapPin className="w-4 h-4 text-violet-600" />
              <span className="font-semibold text-slate-800">{c.name}</span>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Giving Volume</span>
                <span className="font-medium text-slate-900">{fmt(c.giving)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Platform Revenue</span>
                <span className="font-medium text-emerald-700">{fmt(c.fees)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Transactions</span>
                <span className="font-medium text-slate-700">{(c.txn_count || 0).toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Avg Transaction</span>
                <span className="font-medium text-slate-700">${c.txn_count ? (c.giving / c.txn_count).toFixed(2) : '0'}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
