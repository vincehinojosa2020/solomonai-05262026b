import { useState, useEffect, useCallback } from 'react';
import { API_URL } from '@/lib/utils';
import { ChevronLeft, ChevronRight, Landmark, AlertCircle } from 'lucide-react';

const fmt = (n) => `$${Number(n).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;

export default function PlatformPayouts({ token }) {
  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [church, setChurch] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({ page, limit: 50 });
    if (church) params.set('church', church);
    try {
      const res = await fetch(`${API_URL}/platform/payouts?${params}`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setData(await res.json());
    } finally { setLoading(false); }
  }, [token, page, church]);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (!data) return <div className="p-8 text-slate-400">Loading payouts...</div>;

  return (
    <div className="space-y-4" data-testid="platform-payouts">
      {data.pending_payouts?.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Pending Payouts</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {data.pending_payouts.map(p => (
              <div key={p.tenant_id} className="bg-white rounded-xl border border-amber-200 p-4 hover:shadow-sm transition-shadow" data-testid={`pending-${p.tenant_id}`}>
                <div className="flex items-center gap-2 mb-2">
                  <Landmark className="w-4 h-4 text-amber-600" />
                  <span className="font-semibold text-slate-800">{p.church_name}</span>
                </div>
                <div className="text-2xl font-bold text-slate-900">{fmt(p.available_balance)}</div>
                <div className="text-xs text-slate-500 mt-1">{p.bank_account} &middot; {p.payout_method}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center gap-3 bg-white rounded-xl border border-slate-100 p-4">
        <h3 className="text-sm font-semibold text-slate-700">Payout History</h3>
        <select className="ml-auto border border-slate-200 rounded-lg px-3 py-2 text-sm" value={church} onChange={(e) => { setChurch(e.target.value); setPage(1); }}>
          <option value="">All Churches</option>
          <option value="abundant-east-001">Abundant East</option>
          <option value="abundant-west-001">Abundant West</option>
          <option value="abundant-downtown-001">Abundant Downtown</option>
        </select>
      </div>

      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Date</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Church</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Gross</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Fees</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Net Payout</th>
                <th className="px-4 py-3 text-center font-medium text-slate-600">Txns</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Bank</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {loading ? (
                <tr><td colSpan={8} className="px-4 py-12 text-center text-slate-400">Loading...</td></tr>
              ) : (data.payouts || []).map(p => (
                <tr key={p.id} className="hover:bg-slate-50/50">
                  <td className="px-4 py-3 text-slate-600">{p.payout_date}</td>
                  <td className="px-4 py-3 font-medium text-slate-800">{p.church_name}</td>
                  <td className="px-4 py-3 text-right text-slate-700">{fmt(p.gross_amount)}</td>
                  <td className="px-4 py-3 text-right text-red-500">-{fmt(p.total_fees)}</td>
                  <td className="px-4 py-3 text-right font-semibold text-emerald-700">{fmt(p.net_payout)}</td>
                  <td className="px-4 py-3 text-center text-slate-500">{p.transaction_count?.toLocaleString()}</td>
                  <td className="px-4 py-3"><span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700">{p.status}</span></td>
                  <td className="px-4 py-3 text-xs text-slate-500">{p.bank_account}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100 bg-slate-50/50">
          <span className="text-sm text-slate-500">{data.total?.toLocaleString()} payouts</span>
          <div className="flex items-center gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1} className="p-1.5 rounded hover:bg-slate-200 disabled:opacity-30"><ChevronLeft className="w-4 h-4" /></button>
            <span className="text-sm text-slate-600">Page {page} of {data.pages}</span>
            <button onClick={() => setPage(p => Math.min(data.pages, p + 1))} disabled={page >= data.pages} className="p-1.5 rounded hover:bg-slate-200 disabled:opacity-30"><ChevronRight className="w-4 h-4" /></button>
          </div>
        </div>
      </div>
    </div>
  );
}
