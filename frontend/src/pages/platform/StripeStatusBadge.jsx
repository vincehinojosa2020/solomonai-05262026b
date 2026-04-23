import { CheckCircle2, Clock, XCircle } from 'lucide-react';

const STATUS_META = {
  connected:     { label: 'Connected',     icon: CheckCircle2, bg: 'bg-emerald-50',  text: 'text-emerald-700', dot: 'bg-emerald-500' },
  pending:       { label: 'Pending',       icon: Clock,        bg: 'bg-amber-50',    text: 'text-amber-700',   dot: 'bg-amber-500' },
  not_connected: { label: 'Not Connected', icon: XCircle,      bg: 'bg-slate-100',   text: 'text-slate-600',   dot: 'bg-slate-400' },
};

export default function StripeStatusBadge({ status, compact = false }) {
  const meta = STATUS_META[status] || STATUS_META.not_connected;
  const Icon = meta.icon;
  if (compact) {
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
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold ${meta.bg} ${meta.text}`}
      data-testid={`stripe-status-${status}`}
    >
      <Icon className="w-3.5 h-3.5" />
      {meta.label}
    </span>
  );
}
