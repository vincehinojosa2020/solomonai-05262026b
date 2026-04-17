import { useState, useEffect, useCallback } from 'react';
import { API_URL } from '@/lib/utils';
import { Search, Download, ChevronLeft, ChevronRight, Filter, X } from 'lucide-react';

const fmt = (n) => `$${Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export default function PlatformTransactions({ token }) {
  const [txns, setTxns] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({ church: '', status: '', method: '', fund: '', search: '', start_date: '', end_date: '' });

  const fetchData = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({ page, limit: 50 });
    Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v); });
    try {
      const res = await fetch(`${API_URL}/platform/transactions?${params}`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const data = await res.json();
        setTxns(data.transactions || []);
        setTotal(data.total);
        setPages(data.pages);
      }
    } finally { setLoading(false); }
  }, [token, page, filters]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleExport = () => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v); });
    window.open(`${API_URL}/platform/transactions/export?${params}`, '_blank');
  };

  const clearFilters = () => { setFilters({ church: '', status: '', method: '', fund: '', search: '', start_date: '', end_date: '' }); setPage(1); };

  return (
    <div className="space-y-4" data-testid="platform-transactions">
      <div className="flex flex-wrap gap-2 items-center bg-white rounded-xl border border-slate-100 p-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input type="text" placeholder="Search donor name or email..." className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm" value={filters.search} onChange={(e) => { setFilters(f => ({ ...f, search: e.target.value })); setPage(1); }} data-testid="txn-search" />
        </div>
        <select className="border border-slate-200 rounded-lg px-3 py-2 text-sm" value={filters.church} onChange={(e) => { setFilters(f => ({ ...f, church: e.target.value })); setPage(1); }} data-testid="txn-filter-church">
          <option value="">All Churches</option>
          <option value="abundant-east-001">Abundant East</option>
          <option value="abundant-west-001">Abundant West</option>
          <option value="abundant-downtown-001">Abundant Downtown</option>
        </select>
        <select className="border border-slate-200 rounded-lg px-3 py-2 text-sm" value={filters.method} onChange={(e) => { setFilters(f => ({ ...f, method: e.target.value })); setPage(1); }}>
          <option value="">All Methods</option>
          <option value="credit_card">Credit Card</option>
          <option value="debit_card">Debit Card</option>
          <option value="ach">ACH</option>
        </select>
        <select className="border border-slate-200 rounded-lg px-3 py-2 text-sm" value={filters.fund} onChange={(e) => { setFilters(f => ({ ...f, fund: e.target.value })); setPage(1); }}>
          <option value="">All Funds</option>
          <option value="General Fund">General Fund</option>
          <option value="Building Fund">Building Fund</option>
          <option value="Missions">Missions</option>
          <option value="Benevolence">Benevolence</option>
        </select>
        <input type="date" className="border border-slate-200 rounded-lg px-3 py-2 text-sm" value={filters.start_date} onChange={(e) => { setFilters(f => ({ ...f, start_date: e.target.value })); setPage(1); }} />
        <input type="date" className="border border-slate-200 rounded-lg px-3 py-2 text-sm" value={filters.end_date} onChange={(e) => { setFilters(f => ({ ...f, end_date: e.target.value })); setPage(1); }} />
        {Object.values(filters).some(Boolean) && <button onClick={clearFilters} className="text-sm text-slate-500 hover:text-red-500 flex items-center gap-1"><X className="w-3 h-3" />Clear</button>}
        <button onClick={handleExport} className="ml-auto bg-slate-900 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:bg-slate-800" data-testid="txn-export"><Download className="w-4 h-4" />Export CSV</button>
      </div>

      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Date</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Church</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Donor</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Amount</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Fund</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Fee</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Net</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Method</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {loading ? (
                <tr><td colSpan={9} className="px-4 py-12 text-center text-slate-400">Loading transactions...</td></tr>
              ) : txns.length === 0 ? (
                <tr><td colSpan={9} className="px-4 py-12 text-center text-slate-400">No transactions found</td></tr>
              ) : txns.map((t) => (
                <tr key={t.id || t.transaction_id} className="hover:bg-slate-50/50">
                  <td className="px-4 py-3 text-slate-600 whitespace-nowrap">{t.donation_date}</td>
                  <td className="px-4 py-3 text-slate-700 font-medium whitespace-nowrap">{t.church_name}</td>
                  <td className="px-4 py-3"><div className="font-medium text-slate-800">{t.person_name}</div><div className="text-xs text-slate-400">{t.person_email}</div></td>
                  <td className="px-4 py-3 text-right font-semibold text-slate-900">{fmt(t.amount)}</td>
                  <td className="px-4 py-3 text-slate-600">{t.fund_name}</td>
                  <td className="px-4 py-3 text-right text-slate-500">{fmt(t.fee_amount || t.solomon_fee || t.processing_fee || 0)}</td>
                  <td className="px-4 py-3 text-right text-emerald-700 font-medium">{fmt(t.net_amount || (t.amount - (t.fee_amount || t.solomon_fee || 0)))}</td>
                  <td className="px-4 py-3"><span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${t.status === 'completed' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>{t.status}</span></td>
                  <td className="px-4 py-3 text-slate-500 text-xs whitespace-nowrap">{t.card_label || t.payment_method}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100 bg-slate-50/50">
          <span className="text-sm text-slate-500">{total.toLocaleString()} total transactions</span>
          <div className="flex items-center gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1} className="p-1.5 rounded hover:bg-slate-200 disabled:opacity-30"><ChevronLeft className="w-4 h-4" /></button>
            <span className="text-sm text-slate-600">Page {page} of {pages.toLocaleString()}</span>
            <button onClick={() => setPage(p => Math.min(pages, p + 1))} disabled={page >= pages} className="p-1.5 rounded hover:bg-slate-200 disabled:opacity-30"><ChevronRight className="w-4 h-4" /></button>
          </div>
        </div>
      </div>
    </div>
  );
}
