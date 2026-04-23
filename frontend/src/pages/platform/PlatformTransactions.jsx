import { useState, useEffect, useCallback } from 'react';
import { API_URL } from '@/lib/utils';
import { Search, Download, ChevronLeft, ChevronRight, X, Zap } from 'lucide-react';

const fmt = (n) => `$${Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const cents = (c) => `$${((Number(c) || 0) / 100).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

/**
 * Platform God-Mode transaction feed.
 *
 * Two data sources selectable via the top-right toggle:
 *   • Live (Stripe)  — /api/platform/stripe/transactions, queried directly from
 *                      the Stripe platform account (every connected church).
 *   • Demo (Mongo)   — /api/platform/transactions, the existing seeded data.
 *
 * Summary cards are always driven by /api/platform/stripe/transactions/stats
 * so the CEO view surfaces real payment volume at a glance.
 */
export default function PlatformTransactions({ token }) {
  const [source, setSource] = useState('live');           // 'live' | 'demo'
  const [txns, setTxns] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(0);
  const [page, setPage] = useState(1);
  const [cursor, setCursor] = useState(null);           // Stripe pagination cursor
  const [cursorHistory, setCursorHistory] = useState([]);
  const [hasMore, setHasMore] = useState(false);
  const [stats, setStats] = useState(null);
  const [churches, setChurches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({ church: '', status: '', method: '', fund: '', search: '', start_date: '', end_date: '' });

  const headers = () => ({ Authorization: `Bearer ${token}` });

  // Load stats (always live / Stripe) + church list for filter dropdown
  useEffect(() => {
    (async () => {
      try {
        const [sRes, cRes] = await Promise.all([
          fetch(`${API_URL}/platform/stripe/transactions/stats`, { headers: headers() }),
          fetch(`${API_URL}/platform/churches`, { headers: headers() }),
        ]);
        if (sRes.ok) setStats(await sRes.json());
        if (cRes.ok) {
          const data = await cRes.json();
          setChurches(data.churches || []);
        }
      } catch (e) { /* non-fatal */ }
    })();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      if (source === 'live') {
        // Stripe cursor-based pagination
        const params = new URLSearchParams({ limit: 50 });
        if (cursor) params.set('starting_after', cursor);
        if (filters.church) params.set('church_id', filters.church);
        if (filters.status) params.set('status', filters.status);
        if (filters.start_date) params.set('date_from', filters.start_date);
        if (filters.end_date) params.set('date_to', filters.end_date);

        const res = await fetch(`${API_URL}/platform/stripe/transactions?${params}`, { headers: headers() });
        if (res.ok) {
          const d = await res.json();
          setTxns(d.data || []);
          setHasMore(!!d.has_more);
        }
      } else {
        // Legacy Mongo-backed demo feed
        const params = new URLSearchParams({ page, limit: 50 });
        Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v); });
        const res = await fetch(`${API_URL}/platform/transactions?${params}`, { headers: headers() });
        if (res.ok) {
          const d = await res.json();
          setTxns(d.transactions || []);
          setTotal(d.total || 0);
          setPages(d.pages || 0);
        }
      }
    } finally { setLoading(false); }
  }, [source, token, page, cursor, filters]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const switchSource = (newSource) => {
    if (newSource === source) return;
    setSource(newSource);
    setPage(1); setCursor(null); setCursorHistory([]); setTxns([]);
  };

  const nextPage = () => {
    if (source === 'live') {
      if (!hasMore || txns.length === 0) return;
      setCursorHistory((h) => [...h, cursor]);
      setCursor(txns[txns.length - 1].id);
    } else {
      setPage((p) => Math.min(pages, p + 1));
    }
  };

  const prevPage = () => {
    if (source === 'live') {
      if (cursorHistory.length === 0) { setCursor(null); return; }
      const newHist = [...cursorHistory];
      const prev = newHist.pop();
      setCursorHistory(newHist);
      setCursor(prev ?? null);
    } else {
      setPage((p) => Math.max(1, p - 1));
    }
  };

  const handleExport = () => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v); });
    // Export always hits the existing Mongo CSV endpoint — covers both
    // sources since Stripe donations are mirrored to Mongo on confirm.
    window.open(`${API_URL}/platform/transactions/export?${params}`, '_blank');
  };

  const clearFilters = () => {
    setFilters({ church: '', status: '', method: '', fund: '', search: '', start_date: '', end_date: '' });
    setPage(1); setCursor(null); setCursorHistory([]);
  };

  return (
    <div className="space-y-4" data-testid="platform-transactions">
      {/* ── CEO view: summary cards (always Stripe-live) ─────────────────── */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="platform-stats-cards">
          <StatCard label="Today TPV" primary={cents(stats.today.total_amount)} secondary={`${stats.today.count} gifts`} />
          <StatCard label="This Month TPV" primary={cents(stats.this_month.total_amount)} secondary={`${stats.this_month.count} gifts`} />
          <StatCard label="Solomon Revenue (MTD)" primary={cents(stats.this_month.solomon_revenue)} secondary="0.35% of TPV" accent />
          <StatCard label="Active Churches" primary={String(stats.active_churches)} secondary={`${stats.total_donors} donors`} />
        </div>
      )}

      {/* ── Source toggle ─────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-600 tracking-wide uppercase">Transactions</h2>
        <div className="inline-flex rounded-lg border border-slate-200 bg-white p-0.5" data-testid="platform-txn-source-toggle">
          <button
            onClick={() => switchSource('live')}
            data-testid="platform-txn-source-live"
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${source === 'live' ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-50'}`}
          >
            <Zap className="w-3 h-3" /> Live (Stripe)
          </button>
          <button
            onClick={() => switchSource('demo')}
            data-testid="platform-txn-source-demo"
            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${source === 'demo' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-50'}`}
          >
            Demo
          </button>
        </div>
      </div>

      {/* ── Filters ───────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-2 items-center bg-white rounded-xl border border-slate-100 p-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search donor name or email..."
            className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm"
            value={filters.search}
            onChange={(e) => { setFilters((f) => ({ ...f, search: e.target.value })); setPage(1); setCursor(null); }}
            data-testid="txn-search"
          />
        </div>
        <select
          className="border border-slate-200 rounded-lg px-3 py-2 text-sm"
          value={filters.church}
          onChange={(e) => { setFilters((f) => ({ ...f, church: e.target.value })); setPage(1); setCursor(null); setCursorHistory([]); }}
          data-testid="txn-filter-church"
        >
          <option value="">All Churches</option>
          {churches.map((c) => (<option key={c.id} value={c.id}>{c.name}</option>))}
        </select>
        <select className="border border-slate-200 rounded-lg px-3 py-2 text-sm" value={filters.status} onChange={(e) => { setFilters((f) => ({ ...f, status: e.target.value })); setPage(1); setCursor(null); }}>
          <option value="">All Statuses</option>
          <option value="succeeded">Succeeded</option>
          <option value="pending">Pending</option>
          <option value="failed">Failed</option>
          <option value="requires_payment_method">Incomplete</option>
        </select>
        <input type="date" className="border border-slate-200 rounded-lg px-3 py-2 text-sm" value={filters.start_date} onChange={(e) => { setFilters((f) => ({ ...f, start_date: e.target.value })); setPage(1); setCursor(null); }} />
        <input type="date" className="border border-slate-200 rounded-lg px-3 py-2 text-sm" value={filters.end_date} onChange={(e) => { setFilters((f) => ({ ...f, end_date: e.target.value })); setPage(1); setCursor(null); }} />
        {Object.values(filters).some(Boolean) && (
          <button onClick={clearFilters} className="text-sm text-slate-500 hover:text-red-500 flex items-center gap-1"><X className="w-3 h-3" />Clear</button>
        )}
        <button onClick={handleExport} className="ml-auto bg-slate-900 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 hover:bg-slate-800" data-testid="txn-export">
          <Download className="w-4 h-4" />Export CSV
        </button>
      </div>

      {/* ── Table ─────────────────────────────────────────────────────────── */}
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
                <th className="px-4 py-3 text-right font-medium text-slate-600">Stripe Fee</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Solomon Fee</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Church Net</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Card</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {loading ? (
                <tr><td colSpan={10} className="px-4 py-12 text-center text-slate-400">Loading transactions…</td></tr>
              ) : txns.length === 0 ? (
                <tr><td colSpan={10} className="px-4 py-12 text-center text-slate-400">No transactions found</td></tr>
              ) : txns.map((t, i) => source === 'live' ? (
                <tr key={t.id} className="hover:bg-slate-50/50" data-testid={`platform-live-row-${i}`}>
                  <td className="px-4 py-3 text-slate-600 whitespace-nowrap">{(t.created_at || '').slice(0, 10)}</td>
                  <td className="px-4 py-3 text-slate-700 font-medium whitespace-nowrap">{t.church_name}</td>
                  <td className="px-4 py-3"><div className="font-medium text-slate-800">{t.donor_name}</div><div className="text-xs text-slate-400">{t.donor_email}</div></td>
                  <td className="px-4 py-3 text-right font-semibold text-slate-900">{cents(t.amount)}</td>
                  <td className="px-4 py-3 text-slate-600">{t.fund}</td>
                  <td className="px-4 py-3 text-right text-slate-500">{cents(t.stripe_fee)}</td>
                  <td className="px-4 py-3 text-right text-indigo-600 font-medium">{cents(t.solomon_fee)}</td>
                  <td className="px-4 py-3 text-right text-emerald-700 font-semibold">{cents(t.church_net)}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${t.status === 'succeeded' ? 'bg-emerald-50 text-emerald-700' : t.status === 'pending' ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-700'}`}>
                      {t.status}
                    </span>
                    {t.test_mode && <span className="ml-1 text-[10px] font-bold text-indigo-600 tracking-wider">· TEST</span>}
                  </td>
                  <td className="px-4 py-3 text-slate-500 text-xs whitespace-nowrap capitalize">
                    {t.card_brand ? `${t.card_brand} ••••${t.card_last4}` : t.payment_method_type}
                  </td>
                </tr>
              ) : (
                <tr key={t.id || t.transaction_id} className="hover:bg-slate-50/50">
                  <td className="px-4 py-3 text-slate-600 whitespace-nowrap">{t.donation_date}</td>
                  <td className="px-4 py-3 text-slate-700 font-medium whitespace-nowrap">{t.church_name}</td>
                  <td className="px-4 py-3"><div className="font-medium text-slate-800">{t.person_name}</div><div className="text-xs text-slate-400">{t.person_email}</div></td>
                  <td className="px-4 py-3 text-right font-semibold text-slate-900">{fmt(t.amount)}</td>
                  <td className="px-4 py-3 text-slate-600">{t.fund_name}</td>
                  <td className="px-4 py-3 text-right text-slate-500" colSpan={2}>{fmt(t.fee_amount || 0)}</td>
                  <td className="px-4 py-3 text-right text-emerald-700 font-medium">{fmt(t.net_amount || (t.amount - (t.fee_amount || 0)))}</td>
                  <td className="px-4 py-3"><span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${t.status === 'completed' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>{t.status}</span></td>
                  <td className="px-4 py-3 text-slate-500 text-xs whitespace-nowrap">{t.card_label || t.payment_method}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100 bg-slate-50/50">
          <span className="text-sm text-slate-500">
            {source === 'live'
              ? `${txns.length} transactions (page)`
              : `${total.toLocaleString()} total transactions`}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={prevPage}
              disabled={source === 'live' ? cursorHistory.length === 0 && cursor === null : page <= 1}
              className="p-1.5 rounded hover:bg-slate-200 disabled:opacity-30"
              data-testid="txn-prev-page"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm text-slate-600">
              {source === 'live' ? `Page ${cursorHistory.length + 1}` : `Page ${page} of ${pages.toLocaleString()}`}
            </span>
            <button
              onClick={nextPage}
              disabled={source === 'live' ? !hasMore : page >= pages}
              className="p-1.5 rounded hover:bg-slate-200 disabled:opacity-30"
              data-testid="txn-next-page"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, primary, secondary, accent = false }) {
  return (
    <div className={`bg-white rounded-xl border p-4 ${accent ? 'border-indigo-100 bg-indigo-50/30' : 'border-slate-100'}`}>
      <div className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">{label}</div>
      <div className={`mt-1 text-2xl font-mono font-semibold ${accent ? 'text-indigo-700' : 'text-slate-900'}`}>{primary}</div>
      <div className="text-xs text-slate-400 mt-0.5">{secondary}</div>
    </div>
  );
}
