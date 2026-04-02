import { useState, useEffect, useCallback } from 'react';
import { API_URL } from '@/lib/utils';
import { Building2, DollarSign, Users, Clock, Eye, ExternalLink } from 'lucide-react';

const fmt = (n) => n >= 1e6 ? `$${(n/1e6).toFixed(1)}M` : n >= 1e3 ? `$${(n/1e3).toFixed(0)}K` : `$${n.toFixed(0)}`;

export default function PlatformChurches({ token, stats }) {
  const campuses = (stats?.campus_breakdown || []).map(c => {
    const donors = { 'abundant-east-001': 8500, 'abundant-west-001': 4200, 'abundant-downtown-001': 2534 };
    const members = { 'abundant-east-001': 25000, 'abundant-west-001': 12000, 'abundant-downtown-001': 5000 };
    return { ...c, donors: donors[c.tenant_id] || 0, members: members[c.tenant_id] || 0 };
  });

  if (!campuses.length) return <div className="p-8 text-slate-400">Loading churches...</div>;

  return (
    <div className="space-y-4" data-testid="platform-churches">
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Church</th>
                <th className="px-5 py-3 text-left font-medium text-slate-600">Status</th>
                <th className="px-5 py-3 text-right font-medium text-slate-600">Members</th>
                <th className="px-5 py-3 text-right font-medium text-slate-600">Donors</th>
                <th className="px-5 py-3 text-right font-medium text-slate-600">Giving (All Time)</th>
                <th className="px-5 py-3 text-right font-medium text-slate-600">Fees Earned</th>
                <th className="px-5 py-3 text-right font-medium text-slate-600">Transactions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {campuses.map(c => (
                <tr key={c.tenant_id} className="hover:bg-slate-50/50" data-testid={`church-row-${c.tenant_id}`}>
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center"><Building2 className="w-5 h-5 text-blue-600" /></div>
                      <div><div className="font-semibold text-slate-800">{c.name}</div><div className="text-xs text-slate-400">{c.tenant_id}</div></div>
                    </div>
                  </td>
                  <td className="px-5 py-4"><span className="inline-flex px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700">Active</span></td>
                  <td className="px-5 py-4 text-right font-medium text-slate-700">{c.members.toLocaleString()}</td>
                  <td className="px-5 py-4 text-right font-medium text-slate-700">{c.donors.toLocaleString()}</td>
                  <td className="px-5 py-4 text-right font-bold text-slate-900">{fmt(c.giving)}</td>
                  <td className="px-5 py-4 text-right font-semibold text-emerald-700">{fmt(c.fees)}</td>
                  <td className="px-5 py-4 text-right text-slate-600">{c.txn_count?.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-slate-50">
              <tr className="font-bold">
                <td className="px-5 py-3 text-slate-800">Platform Total</td>
                <td></td>
                <td className="px-5 py-3 text-right">{campuses.reduce((a, c) => a + c.members, 0).toLocaleString()}</td>
                <td className="px-5 py-3 text-right">{campuses.reduce((a, c) => a + c.donors, 0).toLocaleString()}</td>
                <td className="px-5 py-3 text-right">{fmt(campuses.reduce((a, c) => a + c.giving, 0))}</td>
                <td className="px-5 py-3 text-right text-emerald-700">{fmt(campuses.reduce((a, c) => a + c.fees, 0))}</td>
                <td className="px-5 py-3 text-right">{campuses.reduce((a, c) => a + (c.txn_count || 0), 0).toLocaleString()}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {campuses.map(c => (
          <div key={c.tenant_id} className="bg-white rounded-xl border border-slate-100 p-5 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-2 mb-3">
              <Building2 className="w-5 h-5 text-blue-600" />
              <h3 className="font-semibold text-slate-800">{c.name}</h3>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><div className="text-slate-500">Total Giving</div><div className="font-bold text-lg">{fmt(c.giving)}</div></div>
              <div><div className="text-slate-500">Fees Earned</div><div className="font-bold text-lg text-emerald-700">{fmt(c.fees)}</div></div>
              <div><div className="text-slate-500">Transactions</div><div className="font-semibold">{c.txn_count?.toLocaleString()}</div></div>
              <div><div className="text-slate-500">Avg Gift</div><div className="font-semibold">${c.txn_count > 0 ? Math.round(c.giving / c.txn_count) : 0}</div></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
