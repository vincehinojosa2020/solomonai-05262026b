import { useState, useEffect, useCallback } from 'react';
import { API_URL } from '@/lib/utils';
import { Pin, PinOff, Search, Sparkles, RefreshCw, Building2, MapPin, Users, X, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';

const MAX_PINS = 5;

function compactNum(n) {
  const v = Number(n || 0);
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(0)}K`;
  return `${v}`;
}

/**
 * God-Mode Competitive Intel page.
 * Lets the platform CEO pin up to 5 target churches from the Top-200 catalog
 * and generate a Claude-written "what changed" sales brief for each.
 */
export default function CompetitiveIntel({ token }) {
  const [catalog, setCatalog] = useState([]);
  const [total, setTotal] = useState(0);
  const [vendors, setVendors] = useState([]);
  const [pins, setPins] = useState([]);
  const [query, setQuery] = useState('');
  const [vendorFilter, setVendorFilter] = useState('');
  const [seedLoading, setSeedLoading] = useState(false);
  const [digestLoading, setDigestLoading] = useState({});
  const [expandedPin, setExpandedPin] = useState(null);

  const headers = () => ({ Authorization: `Bearer ${token}` });

  const fetchCatalog = useCallback(async () => {
    const params = new URLSearchParams({ limit: '50' });
    if (query) params.set('q', query);
    if (vendorFilter) params.set('vendor', vendorFilter);
    try {
      const res = await fetch(`${API_URL}/admin/competitive/top-churches?${params}`, { headers: headers() });
      if (!res.ok) return;
      const data = await res.json();
      setCatalog(data.churches || []);
      setTotal(data.total || 0);
      setVendors(data.vendors || []);
    } catch (e) { console.error('[CompetitiveIntel] catalog', e); }
  }, [token, query, vendorFilter]);

  const fetchPins = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/admin/competitive/pins`, { headers: headers() });
      if (!res.ok) return;
      const data = await res.json();
      setPins(data.pins || []);
    } catch (e) { console.error('[CompetitiveIntel] pins', e); }
  }, [token]);

  useEffect(() => { fetchCatalog(); }, [fetchCatalog]);
  useEffect(() => { fetchPins(); }, [fetchPins]);

  const runSeed = async () => {
    setSeedLoading(true);
    try {
      const res = await fetch(`${API_URL}/admin/competitive/seed`, { method: 'POST', headers: headers() });
      if (res.ok) {
        const d = await res.json();
        toast.success(`Catalog seeded (${d.total_in_catalog} churches)`);
        fetchCatalog();
      } else {
        toast.error('Seed failed');
      }
    } finally { setSeedLoading(false); }
  };

  const pinChurch = async (rank) => {
    const res = await fetch(`${API_URL}/admin/competitive/pins`, {
      method: 'POST',
      headers: { ...headers(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ rank }),
    });
    if (res.ok) {
      toast.success('Pinned to watchlist');
      fetchPins();
    } else {
      const err = await res.json().catch(() => ({}));
      toast.error(err.detail || 'Pin failed');
    }
  };

  const unpinChurch = async (rank) => {
    const res = await fetch(`${API_URL}/admin/competitive/pins/${rank}`, { method: 'DELETE', headers: headers() });
    if (res.ok) {
      toast.success('Removed from watchlist');
      fetchPins();
      if (expandedPin === rank) setExpandedPin(null);
    }
  };

  const generateDigest = async (rank) => {
    setDigestLoading((s) => ({ ...s, [rank]: true }));
    try {
      const res = await fetch(`${API_URL}/admin/competitive/digest`, {
        method: 'POST',
        headers: { ...headers(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ rank }),
      });
      if (res.ok) {
        toast.success('Claude digest generated');
        fetchPins();
        setExpandedPin(rank);
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Digest failed');
      }
    } finally {
      setDigestLoading((s) => ({ ...s, [rank]: false }));
    }
  };

  const pinnedRanks = new Set(pins.map((p) => p.rank));

  if (catalog.length === 0 && total === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-100 p-8 text-center" data-testid="competitive-empty">
        <Sparkles className="w-10 h-10 text-indigo-400 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-slate-900">Seed the Top Churches Catalog</h3>
        <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
          Parse the Top-200 research list into the database so you can pin acquisition targets and watch them in God Mode.
        </p>
        <button
          onClick={runSeed}
          disabled={seedLoading}
          className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
          data-testid="seed-catalog-btn"
        >
          {seedLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          {seedLoading ? 'Seeding…' : 'Seed Catalog'}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="competitive-intel">
      {/* ── Watchlist ─────────────────────────────────────────────────── */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-base font-bold text-slate-900">Watchlist</h2>
            <p className="text-xs text-slate-500">Up to {MAX_PINS} pinned targets · Claude digest on demand</p>
          </div>
          <span className="text-xs font-semibold text-slate-500" data-testid="pin-counter">
            {pins.length} / {MAX_PINS}
          </span>
        </div>

        {pins.length === 0 ? (
          <div className="bg-white rounded-xl border border-dashed border-slate-200 p-6 text-center" data-testid="watchlist-empty">
            <Pin className="w-6 h-6 text-slate-300 mx-auto mb-2" />
            <p className="text-sm text-slate-500">No targets pinned yet. Pin a church from the catalog below to start tracking.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3" data-testid="watchlist-grid">
            {pins.map((p) => (
              <PinnedCard
                key={p.id}
                pin={p}
                onUnpin={() => unpinChurch(p.rank)}
                onDigest={() => generateDigest(p.rank)}
                onExpand={() => setExpandedPin(expandedPin === p.rank ? null : p.rank)}
                expanded={expandedPin === p.rank}
                digestLoading={!!digestLoading[p.rank]}
              />
            ))}
          </div>
        )}
      </div>

      {/* ── Catalog ───────────────────────────────────────────────────── */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-base font-bold text-slate-900">Top Churches Catalog</h2>
            <p className="text-xs text-slate-500">{total} churches · parsed from your McKinsey research</p>
          </div>
          <button
            onClick={runSeed}
            disabled={seedLoading}
            className="text-xs text-slate-500 hover:text-slate-900 flex items-center gap-1"
            data-testid="reseed-btn"
          >
            <RefreshCw className={`w-3 h-3 ${seedLoading ? 'animate-spin' : ''}`} />
            Re-seed
          </button>
        </div>

        <div className="bg-white rounded-xl border border-slate-100 p-4 flex flex-wrap gap-2 items-center">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search church name, city, state…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm"
              data-testid="catalog-search"
            />
          </div>
          <select
            value={vendorFilter}
            onChange={(e) => setVendorFilter(e.target.value)}
            className="border border-slate-200 rounded-lg px-3 py-2 text-sm"
            data-testid="catalog-vendor-filter"
          >
            <option value="">All vendors ({vendors.reduce((a, v) => a + v.count, 0)})</option>
            {vendors.map((v) => (
              <option key={v.name} value={v.name}>{v.name} ({v.count})</option>
            ))}
          </select>
          {(query || vendorFilter) && (
            <button
              onClick={() => { setQuery(''); setVendorFilter(''); }}
              className="text-sm text-slate-500 hover:text-red-500 flex items-center gap-1"
              data-testid="catalog-clear"
            >
              <X className="w-3 h-3" /> Clear
            </button>
          )}
        </div>

        <div className="mt-3 bg-white rounded-xl border border-slate-100 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600 w-12">#</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Church</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Location</th>
                <th className="px-4 py-3 text-right font-medium text-slate-600">Attendance</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Current Vendor</th>
                <th className="px-4 py-3 text-center font-medium text-slate-600 w-20">Pin</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {catalog.length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-400">No churches match those filters.</td></tr>
              ) : (
                catalog.map((c) => {
                  const pinned = pinnedRanks.has(c.rank);
                  return (
                    <tr key={c.rank} className="hover:bg-slate-50/50" data-testid={`catalog-row-${c.rank}`}>
                      <td className="px-4 py-3 text-slate-500 font-mono text-xs">#{c.rank}</td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-slate-800">{c.name}</div>
                        {c.denomination && <div className="text-[11px] text-slate-400">{c.denomination}</div>}
                      </td>
                      <td className="px-4 py-3 text-slate-600 text-xs">
                        <MapPin className="inline w-3 h-3 mr-1 text-slate-400" />
                        {c.city}, {c.state}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-700 font-mono">{compactNum(c.attendance)}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                          c.vendor === 'Pushpay' ? 'bg-red-50 text-red-700' :
                          c.vendor === 'Tithe.ly' ? 'bg-amber-50 text-amber-700' :
                          c.vendor === 'Vanco' ? 'bg-slate-100 text-slate-700' :
                          c.vendor === 'Planning Center' ? 'bg-indigo-50 text-indigo-700' :
                          'bg-slate-50 text-slate-600'
                        }`}>{c.vendor || 'Unknown'}</span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        {pinned ? (
                          <button
                            onClick={() => unpinChurch(c.rank)}
                            className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium text-slate-500 hover:text-red-600"
                            data-testid={`unpin-btn-${c.rank}`}
                          >
                            <PinOff className="w-3 h-3" /> Unpin
                          </button>
                        ) : (
                          <button
                            onClick={() => pinChurch(c.rank)}
                            disabled={pins.length >= MAX_PINS}
                            className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border border-slate-200 hover:border-indigo-500 hover:bg-indigo-50 hover:text-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                            data-testid={`pin-btn-${c.rank}`}
                            title={pins.length >= MAX_PINS ? `Max ${MAX_PINS} pins — unpin one first` : 'Add to watchlist'}
                          >
                            <Pin className="w-3 h-3" /> Pin
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function PinnedCard({ pin, onUnpin, onDigest, onExpand, expanded, digestLoading }) {
  const c = pin.church || {};
  return (
    <div className="bg-white rounded-xl border border-slate-100 hover:shadow-md transition-all overflow-hidden" data-testid={`pinned-card-${pin.rank}`}>
      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 mb-1">
              <span className="text-[10px] font-mono font-bold text-slate-400">#{c.rank}</span>
              <Building2 className="w-3.5 h-3.5 text-indigo-500" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 truncate">{c.name}</h3>
            <p className="text-[11px] text-slate-500">{c.city}, {c.state}</p>
          </div>
          <button
            onClick={onUnpin}
            className="text-slate-400 hover:text-red-500 transition-colors"
            title="Unpin"
            data-testid={`card-unpin-${pin.rank}`}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-2 mt-3">
          <div className="bg-slate-50 rounded-lg p-2">
            <div className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-slate-500 font-semibold">
              <Users className="w-3 h-3" /> Attendance
            </div>
            <div className="text-sm font-bold text-slate-900 mt-0.5">{compactNum(c.attendance)}</div>
          </div>
          <div className="bg-slate-50 rounded-lg p-2">
            <div className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">Vendor</div>
            <div className="text-sm font-bold text-slate-900 mt-0.5 truncate">{c.vendor || '—'}</div>
          </div>
        </div>

        {c.notes && (
          <p className="text-[11px] text-slate-500 italic mt-2 line-clamp-2">{c.notes}</p>
        )}
      </div>

      <div className="border-t border-slate-100 bg-slate-50/50 px-4 py-2 flex items-center gap-2">
        <button
          onClick={onDigest}
          disabled={digestLoading}
          className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800 disabled:opacity-50"
          data-testid={`card-digest-${pin.rank}`}
        >
          {digestLoading ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
          {pin.last_digest ? 'Regenerate' : 'Generate'} digest
        </button>
        {pin.last_digest && (
          <button
            onClick={onExpand}
            className="inline-flex items-center gap-1 text-xs text-slate-600 hover:text-slate-900 px-2 py-1.5"
            data-testid={`card-toggle-${pin.rank}`}
          >
            {expanded ? 'Hide' : 'View'}
            <ChevronRight className={`w-3 h-3 transition-transform ${expanded ? 'rotate-90' : ''}`} />
          </button>
        )}
      </div>

      {expanded && pin.last_digest && (
        <div className="border-t border-slate-100 px-4 py-3 bg-indigo-50/40" data-testid={`card-digest-body-${pin.rank}`}>
          <div className="text-[10px] uppercase tracking-wider text-indigo-600 font-bold mb-2">Claude Digest</div>
          <div className="text-xs text-slate-700 whitespace-pre-wrap font-sans leading-relaxed">{pin.last_digest}</div>
          {pin.last_digest_at && (
            <div className="text-[10px] text-slate-400 mt-2">Generated {new Date(pin.last_digest_at).toLocaleString()}</div>
          )}
        </div>
      )}
    </div>
  );
}
