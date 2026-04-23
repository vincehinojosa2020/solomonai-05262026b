import { useState, useEffect } from 'react';
import { X, ExternalLink, Zap, Users, DollarSign, TrendingUp, CheckCircle2, Clock, XCircle } from 'lucide-react';
import { API_URL } from '@/lib/utils';

const cents = (c) => `$${((Number(c) || 0) / 100).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const fmtMoney = (n) => `$${Number(n || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;

const STATUS_META = {
  connected:     { label: 'Connected',     icon: CheckCircle2, bg: 'bg-emerald-50',  text: 'text-emerald-700', dot: 'bg-emerald-500' },
  pending:       { label: 'Pending',       icon: Clock,        bg: 'bg-amber-50',    text: 'text-amber-700',   dot: 'bg-amber-500' },
  not_connected: { label: 'Not Connected', icon: XCircle,      bg: 'bg-slate-100',   text: 'text-slate-600',   dot: 'bg-slate-400' },
};

function StripeStatusBadge({ status }) {
  const meta = STATUS_META[status] || STATUS_META.not_connected;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${meta.bg} ${meta.text}`}
      data-testid={`stripe-status-${status}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />
      {meta.label}
    </span>
  );
}

/**
 * God-Mode drill-down drawer for a single church. Shows Stripe status,
 * lifetime processed, transactions count, and the 5 most recent Stripe
 * PaymentIntents for this tenant. Mini-dashboard pattern — no new route,
 * no full page load.
 */
export default function ChurchStripeDrawer({ church, token, onClose }) {
  const [recent, setRecent] = useState(null);

  useEffect(() => {
    if (!church?.id || !token) return;
    const params = new URLSearchParams({ church_id: church.id, limit: '5' });
    fetch(`${API_URL}/platform/stripe/transactions?${params}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : null)
      .then(data => setRecent(data?.data || []))
      .catch(() => setRecent([]));
  }, [church?.id, token]);

  if (!church) return null;

  const status = church.stripe_status || 'not_connected';
  const kpis = [
    { label: 'Stripe Processed', value: cents(church.stripe_total_processed || 0), icon: Zap, color: '#6366f1' },
    { label: 'All-Time Giving', value: fmtMoney(church.giving || 0), icon: DollarSign, color: '#10b981' },
    { label: 'Members', value: Number(church.total_members || 0).toLocaleString(), icon: Users, color: '#0891b2' },
    { label: 'Transactions', value: Number(church.txn_count || 0).toLocaleString(), icon: TrendingUp, color: '#7c3aed' },
  ];

  return (
    <div
      className="fixed inset-0 z-[60] flex justify-end"
      data-testid="church-stripe-drawer"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" />

      {/* Panel */}
      <div
        className="relative w-full max-w-lg h-full bg-white shadow-2xl overflow-y-auto animate-in slide-in-from-right duration-300"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 bg-white border-b border-slate-100 px-6 py-4 flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <h2 className="text-lg font-bold text-slate-900 truncate" data-testid="drawer-church-name">{church.name}</h2>
            <div className="flex items-center gap-2 mt-1">
              {church.city && <span className="text-xs text-slate-500">{church.city}{church.state ? `, ${church.state}` : ''}</span>}
              <StripeStatusBadge status={status} />
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
            data-testid="drawer-close"
          >
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        {/* KPI Grid */}
        <div className="px-6 py-5 grid grid-cols-2 gap-3">
          {kpis.map((k, i) => (
            <div key={k.label} className="bg-slate-50 rounded-lg p-3" data-testid={`drawer-kpi-${i}`}>
              <div className="flex items-center gap-1.5 mb-1">
                <k.icon className="w-3.5 h-3.5" style={{ color: k.color }} />
                <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{k.label}</span>
              </div>
              <div className="text-lg font-bold text-slate-900">{k.value}</div>
            </div>
          ))}
        </div>

        {/* Recent Stripe transactions */}
        <div className="px-6 pb-5">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Recent Stripe Activity</h3>
          {recent === null ? (
            <div className="space-y-2">
              {[0, 1, 2].map(i => <div key={i} className="h-12 bg-slate-100 rounded animate-pulse" />)}
            </div>
          ) : recent.length === 0 ? (
            <p className="text-sm text-slate-400 py-6 text-center">No Stripe payments yet for this church.</p>
          ) : (
            <div className="divide-y divide-slate-100">
              {recent.map((t, i) => (
                <div key={t.id} className="py-3 flex items-center gap-3" data-testid={`drawer-txn-${i}`}>
                  <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center flex-shrink-0">
                    <span className="text-xs font-bold text-indigo-700">{(t.donor_name || 'G').charAt(0).toUpperCase()}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-800 truncate">{t.donor_name}</p>
                    <p className="text-xs text-slate-400 truncate">{t.fund} · {t.card_brand ? `${t.card_brand} ••••${t.card_last4}` : t.payment_method_type}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-sm font-bold text-slate-900">{cents(t.amount)}</p>
                    <p className="text-[10px] text-slate-400 capitalize">{t.status}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="sticky bottom-0 bg-white border-t border-slate-100 px-6 py-4 flex gap-2">
          {church.slug || church.subdomain ? (
            <a
              href={`/give/${church.slug || church.subdomain}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg border border-slate-200 text-sm font-medium text-slate-700 hover:bg-slate-50"
              data-testid="drawer-open-give-page"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Public Give Page
            </a>
          ) : null}
          <a
            href={`/platform/transactions?church_id=${church.id}`}
            className="flex-1 inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-medium hover:bg-slate-800"
            data-testid="drawer-view-transactions"
          >
            All Transactions
          </a>
        </div>
      </div>
    </div>
  );
}
