import { useState, useEffect } from 'react';
import { RefreshCw, Loader2, Play, Pause, X, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { API_URL, formatCurrency, formatDate } from '@/lib/utils';
import { toast } from 'sonner';

const STATUS_BADGE = {
  active: 'bg-emerald-50 text-emerald-700',
  paused: 'bg-amber-50 text-amber-700',
  cancelled: 'bg-slate-100 text-slate-400',
};

const FREQ_LABELS = {
  weekly: 'Weekly',
  biweekly: 'Bi-weekly',
  monthly: 'Monthly',
  annually: 'Annual',
};

export default function AdminRecurringGiving() {
  const [schedules, setSchedules] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const perPage = 20;

  useEffect(() => {
    fetchData();
  }, [filter, page]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = sessionStorage.getItem('session_token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const statusParam = filter !== 'all' ? `&status=${filter}` : '';
      const res = await fetch(
        `${API_URL}/admin/recurring-giving?page=${page}&per_page=${perPage}${statusParam}`,
        { headers }
      );
      if (res.ok) {
        const data = await res.json();
        setSchedules(data.schedules || []);
        setTotal(data.total || 0);
        setStats(data.stats);
      }
    } catch (err) {
      console.error('Failed to fetch recurring giving:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (id, newStatus) => {
    const label = newStatus === 'cancelled' ? 'cancel' : newStatus === 'paused' ? 'pause' : 'activate';
    if (newStatus === 'cancelled' && !window.confirm(`Are you sure you want to ${label} this schedule?`)) return;

    try {
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/admin/recurring-giving/${id}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        toast.success(`Schedule ${newStatus}`);
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to update');
      }
    } catch {
      toast.error('Failed to update status');
    }
  };

  const totalPages = Math.ceil(total / perPage);
  const activeTotal = stats?.active?.total_amount || 0;
  const activeCount = stats?.active?.count || 0;
  const pausedCount = stats?.paused?.count || 0;

  return (
    <div className="bento-card" data-testid="admin-recurring-giving">
      <div className="card-header mb-4">
        <div className="flex items-center gap-2">
          <RefreshCw className="w-4 h-4 text-slate-500" />
          <h3 className="card-title">Recurring Giving Schedules</h3>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 bg-emerald-500 rounded-full" />
            {activeCount} active ({formatCurrency(activeTotal)}/mo est.)
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 bg-amber-400 rounded-full" />
            {pausedCount} paused
          </span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-1 mb-4 bg-slate-50 p-1 rounded-lg w-fit">
        {[
          { key: 'all', label: 'All' },
          { key: 'active', label: 'Active' },
          { key: 'paused', label: 'Paused' },
          { key: 'cancelled', label: 'Cancelled' },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => { setFilter(key); setPage(1); }}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
              filter === key ? 'bg-white shadow-sm text-slate-800' : 'text-slate-500 hover:text-slate-700'
            }`}
            data-testid={`filter-${key}`}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
        </div>
      ) : schedules.length === 0 ? (
        <div className="text-center py-8 text-slate-400 text-sm" data-testid="no-admin-recurring">
          No recurring schedules found
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Donor</th>
                <th>Amount</th>
                <th>Frequency</th>
                <th>Fund</th>
                <th>Next Charge</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {schedules.map((s) => (
                <tr key={s.id} data-testid={`admin-recurring-row-${s.id}`}>
                  <td>
                    <div>
                      <span className="font-medium text-slate-700">{s.person_name || 'Unknown'}</span>
                      <span className="block text-[11px] text-slate-400">{s.person_email}</span>
                    </div>
                  </td>
                  <td className="font-mono font-semibold text-slate-900">{formatCurrency(s.amount)}</td>
                  <td className="text-slate-600">{FREQ_LABELS[s.frequency] || s.frequency}</td>
                  <td className="text-slate-600">{s.fund_name || 'General'}</td>
                  <td className="font-mono text-xs">
                    {s.status === 'active' ? s.next_charge_date || '—' : '—'}
                  </td>
                  <td>
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold ${STATUS_BADGE[s.status] || STATUS_BADGE.cancelled}`}>
                      {s.status?.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    <div className="flex items-center gap-1">
                      {s.status === 'active' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0"
                          onClick={() => handleStatusChange(s.id, 'paused')}
                          title="Pause"
                          data-testid={`admin-pause-${s.id}`}
                        >
                          <Pause className="w-3 h-3" />
                        </Button>
                      )}
                      {s.status === 'paused' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0"
                          onClick={() => handleStatusChange(s.id, 'active')}
                          title="Resume"
                          data-testid={`admin-resume-${s.id}`}
                        >
                          <Play className="w-3 h-3" />
                        </Button>
                      )}
                      {s.status !== 'cancelled' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0 text-red-500 hover:text-red-700"
                          onClick={() => handleStatusChange(s.id, 'cancelled')}
                          title="Cancel"
                          data-testid={`admin-cancel-${s.id}`}
                        >
                          <X className="w-3 h-3" />
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {total > perPage && (
        <div className="pagination mt-3">
          <div className="pagination-info">
            {((page - 1) * perPage) + 1}–{Math.min(page * perPage, total)} of {total}
          </div>
          <div className="pagination-controls">
            <button className="pagination-btn" disabled={page === 1} onClick={() => setPage(p => p - 1)}>
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-xs text-slate-500 px-2">{page} / {totalPages}</span>
            <button className="pagination-btn" disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
