import { useState, useEffect, useCallback } from 'react';
import { Shield, Download, ChevronDown, ChevronUp, Filter, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

const ACTION_FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'login', label: 'Logins' },
  { key: 'role_change', label: 'Role Changes' },
  { key: 'kids_checkin', label: 'Kids Check-In' },
  { key: 'donation_processed', label: 'Giving' },
  { key: 'export_report', label: 'Exports' },
  { key: 'church_created', label: 'Onboarding' },
  { key: 'permissions_change', label: 'Permissions' },
];

const getActionColor = (action) => {
  const map = {
    login: 'bg-blue-100 text-blue-700',
    role_change: 'bg-purple-100 text-purple-700',
    permissions_change: 'bg-purple-100 text-purple-700',
    kids_checkin: 'bg-green-100 text-green-700',
    kid_checkin: 'bg-green-100 text-green-700',
    kid_checkout: 'bg-emerald-100 text-emerald-700',
    donation_processed: 'bg-amber-100 text-amber-700',
    export_report: 'bg-slate-100 text-slate-700',
    church_created: 'bg-indigo-100 text-indigo-700',
    service_checkin: 'bg-cyan-100 text-cyan-700',
  };
  return map[action] || 'bg-slate-100 text-slate-600';
};

const getActionLabel = (action) => {
  return (action || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
};

const timeAgo = (ts) => {
  if (!ts) return '';
  const diff = (Date.now() - new Date(ts).getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return new Date(ts).toLocaleDateString();
};

export default function AuditLogPage() {
  const [entries, setEntries] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');
  const [searchText, setSearchText] = useState('');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });

  const fetchLog = useCallback(async () => {
    setLoading(true);
    try {
      const token = sessionStorage.getItem('session_token');
      const params = new URLSearchParams({ page: page.toString(), limit: '30' });
      if (activeFilter !== 'all') params.set('action', activeFilter);
      if (dateRange.start) params.set('start_date', dateRange.start);
      if (dateRange.end) params.set('end_date', dateRange.end);

      const res = await fetch(`${API_URL}/admin/audit-log?${params}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        setEntries(data.entries || []);
        setTotal(data.total || 0);
        setPages(data.pages || 1);
      }
    } catch (err) {
      toast.error('Failed to load audit log');
    } finally {
      setLoading(false);
    }
  }, [page, activeFilter, dateRange]);

  useEffect(() => { fetchLog(); }, [fetchLog]);

  const handleExport = async () => {
    try {
      const token = sessionStorage.getItem('session_token');
      const params = new URLSearchParams();
      if (activeFilter !== 'all') params.set('action', activeFilter);
      if (dateRange.start) params.set('start_date', dateRange.start);
      if (dateRange.end) params.set('end_date', dateRange.end);
      params.set('limit', '5000');

      const res = await fetch(`${API_URL}/admin/audit-log?${params}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();

      const csv = [
        ['Timestamp', 'User', 'Action', 'Entity Type', 'Entity ID', 'IP Address'].join(','),
        ...data.entries.map(e => [
          e.timestamp, `"${e.performed_by_name || ''}"`, e.action, e.entity_type, e.entity_id, e.ip_address || ''
        ].join(','))
      ].join('\n');

      const blob = new Blob([csv], { type: 'text/csv' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `audit-log-${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      toast.success('Audit log exported');
    } catch (err) {
      toast.error('Export failed');
    }
  };

  const filtered = searchText
    ? entries.filter(e => (e.performed_by_name || '').toLowerCase().includes(searchText.toLowerCase()) || (e.action || '').includes(searchText.toLowerCase()))
    : entries;

  return (
    <div className="space-y-5 animate-fade-in" data-testid="audit-log-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Audit Log</h1>
          <p className="page-subtitle">{total} events recorded</p>
        </div>
        <Button variant="outline" size="sm" onClick={handleExport} data-testid="audit-export-csv">
          <Download className="w-4 h-4 mr-2" /> Export CSV
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1 flex-wrap">
          {ACTION_FILTERS.map(f => (
            <button
              key={f.key}
              onClick={() => { setActiveFilter(f.key); setPage(1); }}
              className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${activeFilter === f.key ? 'bg-slate-900 text-white' : 'bg-white text-slate-600 border border-slate-200 hover:border-slate-300'}`}
              data-testid={`filter-${f.key}`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 ml-auto">
          <Input type="date" value={dateRange.start} onChange={e => { setDateRange(d => ({ ...d, start: e.target.value })); setPage(1); }} className="w-36 h-8 text-xs" data-testid="audit-date-start" />
          <span className="text-xs text-slate-400">to</span>
          <Input type="date" value={dateRange.end} onChange={e => { setDateRange(d => ({ ...d, end: e.target.value })); setPage(1); }} className="w-36 h-8 text-xs" data-testid="audit-date-end" />
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-slate-400" />
            <Input value={searchText} onChange={e => setSearchText(e.target.value)} placeholder="Search..." className="pl-8 w-44 h-8 text-xs" data-testid="audit-search" />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden" data-testid="audit-table">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16 text-slate-400">No audit entries found</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50">
                <th className="text-left p-3 text-slate-500 font-medium text-xs">User</th>
                <th className="text-left p-3 text-slate-500 font-medium text-xs">Action</th>
                <th className="text-left p-3 text-slate-500 font-medium text-xs">Entity</th>
                <th className="text-left p-3 text-slate-500 font-medium text-xs">Time</th>
                <th className="text-left p-3 text-slate-500 font-medium text-xs">IP</th>
                <th className="w-10"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((entry, i) => {
                const isExpanded = expandedId === i;
                return (
                  <tr key={i} className="border-b border-slate-100 last:border-0 group" data-testid={`audit-row-${i}`}>
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center text-xs font-bold text-blue-700">
                          {(entry.performed_by_name || '?')[0]?.toUpperCase()}
                        </div>
                        <span className="font-medium text-slate-800">{entry.performed_by_name || 'System'}</span>
                      </div>
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getActionColor(entry.action)}`}>
                        {getActionLabel(entry.action)}
                      </span>
                    </td>
                    <td className="p-3 text-slate-600 text-xs">{entry.entity_type || '-'}</td>
                    <td className="p-3 text-slate-500 text-xs" title={entry.timestamp}>{timeAgo(entry.timestamp)}</td>
                    <td className="p-3 text-slate-400 text-xs font-mono">{entry.ip_address || '-'}</td>
                    <td className="p-3">
                      <button
                        onClick={() => setExpandedId(isExpanded ? null : i)}
                        className="p-1 hover:bg-slate-100 rounded transition-colors"
                        data-testid={`audit-expand-${i}`}
                      >
                        {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                      </button>
                    </td>
                    {isExpanded && (
                      <td colSpan={6} className="p-0">
                        <div className="bg-slate-50 px-6 py-4 border-t border-slate-200" data-testid={`audit-detail-${i}`}>
                          <div className="grid grid-cols-2 gap-4 text-xs">
                            <div>
                              <p className="font-semibold text-slate-500 mb-1">Before</p>
                              <pre className="bg-white p-2 rounded border text-slate-600 overflow-x-auto max-h-32">
                                {JSON.stringify(entry.old_values || entry.before_value || {}, null, 2)}
                              </pre>
                            </div>
                            <div>
                              <p className="font-semibold text-slate-500 mb-1">After</p>
                              <pre className="bg-white p-2 rounded border text-slate-600 overflow-x-auto max-h-32">
                                {JSON.stringify(entry.new_values || entry.after_value || {}, null, 2)}
                              </pre>
                            </div>
                          </div>
                          <p className="text-xs text-slate-400 mt-2">
                            Session: {entry.session_id || '-'} | Entity ID: {entry.entity_id || '-'} | Full timestamp: {entry.timestamp}
                          </p>
                        </div>
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-between" data-testid="audit-pagination">
          <span className="text-xs text-slate-500">Page {page} of {pages} ({total} total)</span>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</Button>
            <Button variant="outline" size="sm" disabled={page >= pages} onClick={() => setPage(p => p + 1)}>Next</Button>
          </div>
        </div>
      )}
    </div>
  );
}
