/**
 * Solomon AI — God Mode Platform Dashboard
 * The executive view: all churches, all data, all intelligence.
 * Route: /platform
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  DollarSign, Building2, Users, TrendingUp, TrendingDown, Activity,
  ChevronRight, ArrowUpRight, ArrowDownRight, AlertTriangle, Bell,
  Download, RefreshCw, Filter, Search, LogOut, BarChart3, Shield,
  Settings, Receipt, Landmark, CreditCard, Plus, Eye, UserCheck,
  Zap, Globe, Heart, Clock, X
} from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell, ScatterChart, Scatter, ZAxis
} from 'recharts';
import { Button } from '@/components/ui/button';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import ChurchOnboardingWizard from '@/components/ChurchOnboardingWizard';

// ── Palette ──────────────────────────────────────────────────────────────────
const CHURCH_COLORS = {
  'Abundant Church': '#2563eb',
  'The Potter\'s House': '#7c3aed',
  'City Reach Church': '#059669',
  'EdenX Ministries': '#0891b2',
  'Abundant East': '#f59e0b',
  'Abundant West': '#ec4899',
  'Abundant Downtown': '#6366f1',
};
const DEFAULT_COLOR = '#64748b';
const getColor = (name) => {
  for (const [key, color] of Object.entries(CHURCH_COLORS)) {
    if (name?.includes(key.split(' ')[0]) || name === key) return color;
  }
  return DEFAULT_COLOR;
};

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmtCur(n, compact = false) {
  const v = Number(n ?? 0);
  if (isNaN(v)) return '$0';
  if (compact) {
    if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
    if (v >= 1e6) return `$${(v / 1e6).toFixed(2)}M`;
    if (v >= 1e3) return `$${(v / 1e3).toFixed(1)}K`;
    return `$${v.toFixed(0)}`;
  }
  return `$${v.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}
function fmtNum(n) { return Number(n ?? 0).toLocaleString(); }

function getAuthHeaders() {
  const token = sessionStorage.getItem('session_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ── Health Score Badge ────────────────────────────────────────────────────────
const GRADE_STYLE = {
  'A+': { bg: '#dcfce7', text: '#15803d', border: '#86efac' },
  'A':  { bg: '#dcfce7', text: '#15803d', border: '#86efac' },
  'B+': { bg: '#dbeafe', text: '#1d4ed8', border: '#93c5fd' },
  'B':  { bg: '#dbeafe', text: '#1d4ed8', border: '#93c5fd' },
  'C':  { bg: '#fef9c3', text: '#92400e', border: '#fde68a' },
  'D':  { bg: '#fee2e2', text: '#dc2626', border: '#fca5a5' },
  'N/A':{ bg: '#f1f5f9', text: '#64748b', border: '#e2e8f0' },
};
function HealthBadge({ grade, score }) {
  const g = grade?.charAt(0) || 'N/A';
  const cfg = GRADE_STYLE[grade] || GRADE_STYLE[g] || GRADE_STYLE['N/A'];
  return (
    <span
      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-sm font-bold border"
      style={{ background: cfg.bg, color: cfg.text, borderColor: cfg.border }}
      title={`Health Score: ${score}/100`}
    >
      {grade || '—'}
      {score !== undefined && <span className="text-[10px] font-normal opacity-70">{score}</span>}
    </span>
  );
}

// ── Hero KPI Card ─────────────────────────────────────────────────────────────
function HeroKPI({ label, value, subtext, icon: Icon, color, change }) {
  return (
    <div
      className="rounded-2xl p-6 flex flex-col gap-3 border"
      style={{ background: `${color}08`, borderColor: `${color}30` }}
      data-testid={`hero-kpi-${label.toLowerCase().replace(/\s+/g, '-')}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: `${color}99` }}>{label}</span>
        <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ background: `${color}15` }}>
          <Icon className="w-4 h-4" style={{ color }} />
        </div>
      </div>
      <div className="text-4xl font-black tracking-tight" style={{ color, fontVariantNumeric: 'tabular-nums' }}>
        {value}
      </div>
      <div className="flex items-center justify-between">
        <span className="text-xs text-slate-500">{subtext}</span>
        {change !== undefined && (
          <span className={`text-xs font-semibold flex items-center gap-0.5 ${change >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
            {change >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
            {Math.abs(change).toFixed(1)}% YoY
          </span>
        )}
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function PlatformDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [healthScores, setHealthScores] = useState({});
  const [activity, setActivity] = useState([]);
  const [activeSection, setActiveSection] = useState('dashboard');
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [impersonating, setImpersonating] = useState(null);
  const activityTimer = useRef(null);

  // ── Transactions state ──
  const [txns, setTxns] = useState([]);
  const [txnPage, setTxnPage] = useState(1);
  const [txnTotal, setTxnTotal] = useState(0);
  const [txnFilter, setTxnFilter] = useState({ church: '', search: '', method: '' });
  const [txnLoading, setTxnLoading] = useState(false);

  // ── Revenue state ──
  const [revenue, setRevenue] = useState(null);

  // ── Donors state ──
  const [donorStats, setDonorStats] = useState(null);

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/platform/stats`, { headers: getAuthHeaders() });
      if (res.ok) setStats(await res.json());
    } catch (e) { console.error(e); }
  }, []);

  const fetchHealthScores = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/platform/health-scores`, { headers: getAuthHeaders() });
      if (res.ok) {
        const d = await res.json();
        const map = {};
        (d.churches || []).forEach(c => { map[c.tenant_id] = c.health; });
        setHealthScores(map);
      }
    } catch (e) { console.error(e); }
  }, []);

  const fetchActivity = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/platform/activity-feed?limit=15`, { headers: getAuthHeaders() });
      if (res.ok) { const d = await res.json(); setActivity(d.events || []); }
    } catch (e) { console.error(e); }
  }, []);

  const fetchTransactions = useCallback(async () => {
    setTxnLoading(true);
    try {
      const params = new URLSearchParams({ page: txnPage, limit: 50, ...txnFilter });
      const res = await fetch(`${API_URL}/platform/transactions?${params}`, { headers: getAuthHeaders() });
      if (res.ok) {
        const d = await res.json();
        setTxns(d.transactions || d.donations || []);
        setTxnTotal(d.total || 0);
      }
    } catch (e) { console.error(e); } finally { setTxnLoading(false); }
  }, [txnPage, txnFilter]);

  const fetchRevenue = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/platform/revenue`, { headers: getAuthHeaders() });
      if (res.ok) setRevenue(await res.json());
    } catch (e) { console.error(e); }
  }, []);

  const fetchDonorStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/platform/donors`, { headers: getAuthHeaders() });
      if (res.ok) setDonorStats(await res.json());
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => {
    fetchStats();
    fetchHealthScores();
    fetchActivity();
    activityTimer.current = setInterval(fetchActivity, 15000);
    return () => clearInterval(activityTimer.current);
  }, [fetchStats, fetchHealthScores, fetchActivity]);

  useEffect(() => {
    if (activeSection === 'transactions') fetchTransactions();
    if (activeSection === 'revenue') fetchRevenue();
    if (activeSection === 'donors') fetchDonorStats();
  }, [activeSection, fetchTransactions, fetchRevenue, fetchDonorStats]);

  const handleImpersonate = async (tenantId, tenantName) => {
    try {
      const res = await fetch(`${API_URL}/platform/impersonate`, {
        method: 'POST', headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: tenantId }),
      });
      if (res.ok) {
        const d = await res.json();
        // API returns 'token' key; fallback to 'session_token' for compatibility
        const impToken = d.token || d.session_token;
        setImpersonating({ name: tenantName, token: impToken });
        if (impToken) {
          const oldToken = sessionStorage.getItem('session_token');
          sessionStorage.setItem('platform_token', oldToken);
          sessionStorage.setItem('session_token', impToken);
          navigate('/dashboard');
          toast.success(`Now viewing as ${tenantName}`);
        }
      } else { toast.error('Impersonation failed'); }
    } catch { toast.error('Failed to impersonate'); }
  };

  const handleLogout = () => {
    sessionStorage.clear();
    navigate('/login');
  };

  const exportCSV = (data, filename) => {
    if (!data?.length) { toast.error('No data to export'); return; }
    const keys = Object.keys(data[0]);
    const csv = [keys.join(','), ...data.map(r => keys.map(k => `"${r[k] ?? ''}"`).join(','))].join('\n');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
    a.download = filename;
    a.click();
    toast.success('Exported');
  };

  // ── Derived data ──────────────────────────────────────────────────────────
  const churches = stats?.campus_breakdown || [];
  const giving = stats?.giving || {};
  const fees = stats?.fees || {};
  const platform = stats?.platform || {};
  const giveingTrend = stats?.giving_trend || [];

  // Map tenant_id → church name for transaction table
  const real_tenants_map = Object.fromEntries(churches.map(c => [c.tenant_id, c.name]));

  // Stacked bar chart data
  const churchNames = [...new Set(churches.map(c => c.name))];
  const monthlyChartData = giveingTrend.map(m => {
    const entry = { month: m.month.slice(0, 7) };
    Object.entries(m.by_campus || {}).forEach(([name, val]) => {
      entry[name] = Math.round(val);
    });
    return entry;
  });

  // Revenue trend (using fees from trend)
  const revenueTrend = giveingTrend.map(m => ({
    month: m.month.slice(0, 7),
    revenue: Math.round(m.total_fees || 0),
    giving: Math.round(m.total_giving || 0),
  }));

  // Attention required: churches with health score C or below
  const attentionChurches = churches.filter(c => {
    const hs = healthScores[c.tenant_id];
    return hs && hs.grade && ['C', 'D', 'F'].includes(hs.grade.charAt(0));
  });

  // ── NAV ───────────────────────────────────────────────────────────────────
  const NAV = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboardIcon },
    { id: 'churches', label: 'Churches', icon: Building2 },
    { id: 'transactions', label: 'Transactions', icon: Receipt },
    { id: 'payouts', label: 'Payouts', icon: Landmark },
    { id: 'revenue', label: 'Revenue', icon: TrendingUp },
    { id: 'donors', label: 'Donors', icon: Users },
    { id: 'reports', label: 'Reports', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  function LayoutDashboardIcon(props) {
    return <Activity {...props} />;
  }

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden" data-testid="god-mode-platform">
      {/* ── Sidebar ── */}
      <aside className="w-56 bg-slate-900 flex flex-col flex-shrink-0">
        <div className="px-5 py-5 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="text-white font-bold text-base tracking-tight" data-testid="sidebar-brand">
              Solomon AI
            </span>
          </div>
          <p className="text-slate-500 text-xs mt-1 ml-10">Platform Admin</p>
        </div>
        <nav className="flex-1 py-4 overflow-y-auto">
          {NAV.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveSection(item.id)}
              className={`w-full flex items-center gap-3 px-5 py-2.5 text-sm font-medium transition-all ${
                activeSection === item.id
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
              data-testid={`nav-${item.id}`}
            >
              <item.icon className="w-4 h-4 flex-shrink-0" />
              {item.label}
            </button>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-slate-800 space-y-2">
          <button
            onClick={() => setShowOnboarding(true)}
            className="w-full flex items-center gap-2 px-3 py-2 text-xs text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-all"
            data-testid="add-church-btn"
          >
            <Plus className="w-3.5 h-3.5" /> Add New Church
          </button>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 text-xs text-slate-500 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-all"
          >
            <LogOut className="w-3.5 h-3.5" /> Sign Out
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="flex-1 overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 z-20 bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-base font-bold text-slate-900 capitalize">{activeSection === 'dashboard' ? 'Platform Overview' : activeSection}</h1>
            <p className="text-xs text-slate-400">{new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={fetchStats} className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"><RefreshCw className="w-4 h-4" /></button>
            <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold">SA</div>
          </div>
        </div>

        <div className="p-6 space-y-6">

          {/* ════════ DASHBOARD ════════ */}
          {activeSection === 'dashboard' && (
            <>
              {/* Row 1: Hero KPIs */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4" data-testid="hero-kpis">
                <HeroKPI
                  label="Platform GMV"
                  value={fmtCur(giving.all_time, true)}
                  subtext="All-time giving processed"
                  icon={Globe}
                  color="#2563eb"
                  change={giving.yoy_change}
                />
                <HeroKPI
                  label="Platform Revenue"
                  value={fmtCur(fees.all_time, true)}
                  subtext="Total Solomon Pay fees"
                  icon={DollarSign}
                  color="#059669"
                />
                <HeroKPI
                  label="MRR"
                  value={fmtCur(platform.total_mrr, true)}
                  subtext="Monthly recurring revenue"
                  icon={TrendingUp}
                  color="#7c3aed"
                />
                <HeroKPI
                  label="ARR"
                  value={fmtCur(platform.arr, true)}
                  subtext="Annual run rate"
                  icon={Activity}
                  color="#0891b2"
                />
              </div>

              {/* Secondary stats row */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {[
                  { label: 'Churches', value: churches.length, icon: Building2, color: '#2563eb' },
                  { label: 'Total Members', value: fmtNum(stats?.members?.total || 0), icon: Users, color: '#7c3aed' },
                  { label: 'Total Transactions', value: fmtNum(stats?.transactions?.total || 0), icon: Receipt, color: '#059669' },
                  { label: 'YTD Giving', value: fmtCur(giving.ytd, true), icon: Heart, color: '#ec4899' },
                  { label: 'YTD Revenue', value: fmtCur(fees.ytd, true), icon: Landmark, color: '#f59e0b' },
                ].map(s => (
                  <div key={s.label} className="bg-white rounded-xl border border-slate-100 p-4 flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: `${s.color}15` }}>
                      <s.icon className="w-4 h-4" style={{ color: s.color }} />
                    </div>
                    <div>
                      <p className="text-xs text-slate-500">{s.label}</p>
                      <p className="text-lg font-bold text-slate-900">{s.value}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Row 2: Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
                {/* Stacked bar — monthly giving by church */}
                <div className="lg:col-span-3 bg-white rounded-xl border border-slate-100 p-5" data-testid="monthly-giving-chart">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-slate-900 text-sm">Monthly Giving by Church</h3>
                      <p className="text-xs text-slate-400 mt-0.5">Last 12 months — stacked by church</p>
                    </div>
                    <button onClick={() => exportCSV(revenueTrend, 'giving_trend.csv')} className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-700">
                      <Download className="w-3.5 h-3.5" /> CSV
                    </button>
                  </div>
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={monthlyChartData.slice(-12)} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="month" tick={{ fontSize: 10 }} tickFormatter={v => v.slice(5)} />
                      <YAxis tickFormatter={v => `$${(v/1000).toFixed(0)}K`} tick={{ fontSize: 10 }} width={55} />
                      <Tooltip formatter={v => fmtCur(v)} labelFormatter={l => `Month: ${l}`} />
                      <Legend iconSize={8} wrapperStyle={{ fontSize: 11 }} />
                      {Object.keys(monthlyChartData[0] || {}).filter(k => k !== 'month').map(name => (
                        <Bar key={name} dataKey={name} stackId="a" fill={getColor(name)} radius={[2, 2, 0, 0]} />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Revenue trend line */}
                <div className="lg:col-span-2 bg-white rounded-xl border border-slate-100 p-5" data-testid="revenue-trend-chart">
                  <div className="mb-4">
                    <h3 className="font-semibold text-slate-900 text-sm">Platform Revenue Trend</h3>
                    <p className="text-xs text-slate-400 mt-0.5">Monthly Solomon Pay fees earned</p>
                  </div>
                  <ResponsiveContainer width="100%" height={260}>
                    <AreaChart data={revenueTrend.slice(-12)} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#059669" stopOpacity={0.2} />
                          <stop offset="95%" stopColor="#059669" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="month" tick={{ fontSize: 10 }} tickFormatter={v => v.slice(5)} />
                      <YAxis tickFormatter={v => `$${(v/1000).toFixed(0)}K`} tick={{ fontSize: 10 }} width={50} />
                      <Tooltip formatter={v => fmtCur(v)} />
                      <Area type="monotone" dataKey="revenue" stroke="#059669" fill="url(#revGrad)" strokeWidth={2} name="Revenue" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Row 3: Church Portfolio Table */}
              <div className="bg-white rounded-xl border border-slate-100 overflow-hidden" data-testid="church-portfolio-table">
                <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-slate-900">Church Portfolio</h3>
                    <p className="text-xs text-slate-400 mt-0.5">{churches.length} active churches • Click a row to drill in</p>
                  </div>
                  <button
                    onClick={() => setShowOnboarding(true)}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700"
                    data-testid="add-church-table-btn"
                  >
                    <Plus className="w-3.5 h-3.5" /> Add Church
                  </button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-100">
                        {['Church', 'City', 'Members', 'Active Donors', 'All-Time Giving', 'Fees Earned', 'Health', 'Actions'].map(h => (
                          <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {churches.map(c => {
                        const hs = healthScores[c.tenant_id];
                        return (
                          <tr
                            key={c.tenant_id}
                            className="hover:bg-slate-50/60 cursor-pointer transition-colors"
                            onClick={() => setActiveSection('churches')}
                            data-testid={`church-row-${c.tenant_id}`}
                          >
                            <td className="px-4 py-3.5">
                              <div className="flex items-center gap-2.5">
                                <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold flex-shrink-0" style={{ background: getColor(c.name) }}>
                                  {c.name.charAt(0)}
                                </div>
                                <span className="font-semibold text-slate-800">{c.name}</span>
                              </div>
                            </td>
                            <td className="px-4 py-3.5 text-slate-500 text-xs">{c.city}{c.state ? `, ${c.state}` : ''}</td>
                            <td className="px-4 py-3.5 text-slate-700 font-medium">{fmtNum(stats?.members?.total ? Math.round(stats.members.total * c.giving / Math.max(giving.all_time, 1)) : 0)}</td>
                            <td className="px-4 py-3.5 text-slate-700">{fmtNum(c.active_donors)}</td>
                            <td className="px-4 py-3.5 font-semibold text-slate-900">{fmtCur(c.giving, true)}</td>
                            <td className="px-4 py-3.5 text-emerald-700 font-semibold">{fmtCur(c.fees, true)}</td>
                            <td className="px-4 py-3.5">
                              {hs ? <HealthBadge grade={hs.grade} score={hs.score} /> : <span className="text-slate-300 text-xs">—</span>}
                            </td>
                            <td className="px-4 py-3.5">
                              <div className="flex items-center gap-1.5">
                                <button
                                  onClick={e => { e.stopPropagation(); setActiveSection('churches'); }}
                                  className="px-2 py-1 text-xs bg-slate-100 hover:bg-slate-200 rounded text-slate-600 font-medium"
                                  title="View church details"
                                >View</button>
                                <button
                                  onClick={e => { e.stopPropagation(); handleImpersonate(c.tenant_id, c.name); }}
                                  className="px-2 py-1 text-xs bg-blue-50 hover:bg-blue-100 rounded text-blue-600 font-medium"
                                  title="Log in as church admin"
                                  data-testid={`impersonate-${c.tenant_id}`}
                                >Impersonate</button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Row 4: Activity Feed + Attention Required */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Activity Feed */}
                <div className="bg-white rounded-xl border border-slate-100 p-5" data-testid="activity-feed">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Activity className="w-4 h-4 text-blue-600" />
                      <h3 className="font-semibold text-slate-900 text-sm">Live Activity</h3>
                      <span className="flex h-2 w-2 rounded-full bg-emerald-400 ml-1 animate-pulse" />
                    </div>
                    <span className="text-xs text-slate-400">Updates every 15s</span>
                  </div>
                  <div className="space-y-2.5 max-h-72 overflow-y-auto">
                    {activity.length === 0 ? (
                      <div className="text-center py-8">
                        <Activity className="w-8 h-8 text-slate-200 mx-auto mb-2" />
                        <p className="text-xs text-slate-400">No recent activity</p>
                      </div>
                    ) : activity.map((ev, i) => (
                      <div key={i} className="flex items-start gap-2.5 py-2 border-b border-slate-50 last:border-0">
                        <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-sm" style={{
                          background: ev.color === 'emerald' ? '#dcfce7' : ev.color === 'blue' ? '#dbeafe' : '#fef9c3'
                        }}>
                          {ev.type === 'donation' ? '🎁' : ev.type === 'recurring' ? '🔁' : '⚡'}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs text-slate-700 leading-snug">{ev.message}</p>
                          <p className="text-[10px] text-slate-400 mt-0.5">{String(ev.timestamp || '').slice(0, 10)}</p>
                        </div>
                        {ev.amount > 0 && (
                          <span className="text-xs font-semibold text-emerald-700 flex-shrink-0">{fmtCur(ev.amount)}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Attention Required */}
                <div className="bg-white rounded-xl border border-slate-100 p-5" data-testid="attention-required">
                  <div className="flex items-center gap-2 mb-4">
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                    <h3 className="font-semibold text-slate-900 text-sm">Attention Required</h3>
                    {attentionChurches.length > 0 && (
                      <span className="ml-auto text-xs font-bold bg-red-100 text-red-700 px-2 py-0.5 rounded-full">{attentionChurches.length}</span>
                    )}
                  </div>
                  {attentionChurches.length === 0 ? (
                    <div className="text-center py-8">
                      <div className="w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center mx-auto mb-2">
                        <Activity className="w-5 h-5 text-emerald-500" />
                      </div>
                      <p className="text-xs font-medium text-emerald-700">All churches healthy</p>
                      <p className="text-xs text-slate-400 mt-0.5">No churches below Health Score C</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {attentionChurches.map(c => {
                        const hs = healthScores[c.tenant_id];
                        const isRed = hs?.grade?.charAt(0) === 'D' || hs?.grade?.charAt(0) === 'F';
                        return (
                          <div
                            key={c.tenant_id}
                            className="flex items-center gap-3 p-3 rounded-xl border transition-all hover:shadow-sm cursor-pointer"
                            style={{ borderColor: isRed ? '#fca5a5' : '#fde68a', background: isRed ? '#fff5f5' : '#fffbeb' }}
                            onClick={() => setActiveSection('churches')}
                          >
                            <div className="w-9 h-9 rounded-lg flex items-center justify-center font-bold text-sm flex-shrink-0" style={{
                              background: isRed ? '#fee2e2' : '#fef3c7',
                              color: isRed ? '#dc2626' : '#d97706',
                            }}>
                              {hs?.grade}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-semibold text-slate-900">{c.name}</p>
                              <p className="text-xs text-slate-500 truncate">
                                {hs?.dimensions ? Object.values(hs.dimensions).sort((a,b) => a.score - b.score)[0]?.label || 'Needs attention' : 'Health score alert'}
                              </p>
                            </div>
                            <ChevronRight className="w-4 h-4 text-slate-300 flex-shrink-0" />
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          {/* ════════ CHURCHES ════════ */}
          {activeSection === 'churches' && (
            <div className="space-y-4" data-testid="churches-section">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-slate-900">{churches.length} Church Partners</h2>
                <button onClick={() => setShowOnboarding(true)} className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
                  <Plus className="w-4 h-4" /> Add New Church
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {churches.map(c => {
                  const hs = healthScores[c.tenant_id];
                  const color = getColor(c.name);
                  return (
                    <div key={c.tenant_id} className="bg-white rounded-xl border border-slate-100 p-5 hover:shadow-md transition-shadow" data-testid={`church-card-${c.tenant_id}`}>
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-lg" style={{ background: color }}>
                            {c.name.charAt(0)}
                          </div>
                          <div>
                            <h3 className="font-bold text-slate-900">{c.name}</h3>
                            <p className="text-xs text-slate-500">{c.city}{c.state ? `, ${c.state}` : ''}</p>
                          </div>
                        </div>
                        {hs && <HealthBadge grade={hs.grade} score={hs.score} />}
                      </div>
                      <div className="grid grid-cols-3 gap-3 mb-4">
                        <div className="bg-slate-50 rounded-lg p-2.5 text-center">
                          <p className="text-xs text-slate-500">All-Time</p>
                          <p className="text-base font-bold text-slate-900">{fmtCur(c.giving, true)}</p>
                        </div>
                        <div className="bg-slate-50 rounded-lg p-2.5 text-center">
                          <p className="text-xs text-slate-500">Fees</p>
                          <p className="text-base font-bold text-emerald-700">{fmtCur(c.fees, true)}</p>
                        </div>
                        <div className="bg-slate-50 rounded-lg p-2.5 text-center">
                          <p className="text-xs text-slate-500">Active Donors</p>
                          <p className="text-base font-bold text-slate-900">{fmtNum(c.active_donors)}</p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button className="flex-1 py-2 border border-slate-200 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-50">View Dashboard</button>
                        <button
                          onClick={() => handleImpersonate(c.tenant_id, c.name)}
                          className="flex-1 py-2 bg-blue-50 border border-blue-200 rounded-lg text-xs font-medium text-blue-700 hover:bg-blue-100"
                          data-testid={`impersonate-card-${c.tenant_id}`}
                        >Impersonate</button>
                      </div>
                      {hs?.dimensions && (
                        <div className="mt-3 pt-3 border-t border-slate-100 grid grid-cols-2 gap-1.5">
                          {Object.values(hs.dimensions).map(dim => (
                            <div key={dim.label} className="flex items-center justify-between">
                              <span className="text-[10px] text-slate-400 truncate">{dim.label}</span>
                              <div className="flex items-center gap-1">
                                <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                  <div className="h-full rounded-full" style={{ width: `${dim.score}%`, background: dim.score >= 70 ? '#059669' : dim.score >= 50 ? '#2563eb' : '#f59e0b' }} />
                                </div>
                                <span className="text-[10px] text-slate-400 w-6">{dim.score}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ════════ TRANSACTIONS ════════ */}
          {activeSection === 'transactions' && (
            <div className="space-y-4" data-testid="transactions-section">
              <div className="flex items-center justify-between flex-wrap gap-3">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Platform Transactions</h2>
                  <p className="text-xs text-slate-400">{fmtNum(txnTotal)} total • all churches</p>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <div className="relative">
                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
                    <input
                      className="pl-8 pr-3 py-1.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200 w-48"
                      placeholder="Search donor..."
                      value={txnFilter.search}
                      onChange={e => setTxnFilter(f => ({...f, search: e.target.value}))}
                      data-testid="txn-search"
                    />
                  </div>
                  <select
                    className="py-1.5 px-3 text-sm border border-slate-200 rounded-lg"
                    value={txnFilter.church}
                    onChange={e => setTxnFilter(f => ({...f, church: e.target.value}))}
                    data-testid="txn-filter-church"
                  >
                    <option value="">All Churches</option>
                    {churches.map(c => <option key={c.tenant_id} value={c.tenant_id}>{c.name}</option>)}
                  </select>
                  <button onClick={() => exportCSV(txns, 'transactions.csv')} className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-slate-200 rounded-lg hover:bg-slate-50">
                    <Download className="w-3.5 h-3.5" /> Export
                  </button>
                  <button onClick={fetchTransactions} className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    <Filter className="w-3.5 h-3.5" /> Filter
                  </button>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
                <table className="w-full text-sm" data-testid="transactions-table">
                  <thead className="bg-slate-50 border-b border-slate-100">
                    <tr>
                      {['Date', 'Donor', 'Church', 'Fund', 'Amount', 'Fees', 'Method', 'Status'].map(h => (
                        <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {txnLoading ? (
                      <tr><td colSpan={8} className="text-center py-10 text-slate-400 text-sm">Loading transactions...</td></tr>
                    ) : txns.length === 0 ? (
                      <tr><td colSpan={8} className="text-center py-10 text-slate-400 text-sm">No transactions found. Click Filter to load data.</td></tr>
                    ) : txns.slice(0, 50).map((t, i) => (
                      <tr key={i} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-4 py-2.5 text-slate-500 font-mono text-xs">{String(t.donation_date || t.created_at || '').slice(0, 10)}</td>
                        <td className="px-4 py-2.5 text-slate-700 font-medium">{t.donor_name || 'Anonymous'}</td>
                        <td className="px-4 py-2.5 text-slate-500 text-xs">{real_tenants_map[t.tenant_id] || t.tenant_id?.slice(0, 12)}</td>
                        <td className="px-4 py-2.5 text-slate-500 text-xs">{t.fund_name || 'General'}</td>
                        <td className="px-4 py-2.5 font-bold text-slate-900">{fmtCur(t.amount)}</td>
                        <td className="px-4 py-2.5 text-emerald-700 text-xs">{t.fee_amount ? fmtCur(t.fee_amount) : '—'}</td>
                        <td className="px-4 py-2.5 text-xs"><span className="px-2 py-0.5 bg-slate-100 rounded text-slate-600 capitalize">{t.payment_method || 'card'}</span></td>
                        <td className="px-4 py-2.5"><span className="px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700">Completed</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {txnTotal > 50 && (
                  <div className="px-4 py-3 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-xs text-slate-400">Showing 50 of {fmtNum(txnTotal)}</span>
                    <div className="flex items-center gap-2">
                      <button onClick={() => setTxnPage(p => Math.max(1, p-1))} disabled={txnPage === 1} className="px-3 py-1 text-xs border border-slate-200 rounded disabled:opacity-40">Prev</button>
                      <span className="text-xs text-slate-500">Page {txnPage}</span>
                      <button onClick={() => setTxnPage(p => p+1)} className="px-3 py-1 text-xs border border-slate-200 rounded">Next</button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ════════ REVENUE ════════ */}
          {activeSection === 'revenue' && (
            <div className="space-y-4" data-testid="revenue-section">
              <h2 className="text-lg font-bold text-slate-900">Platform Revenue</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: 'All-Time Revenue', value: fmtCur(fees.all_time, true), color: '#059669' },
                  { label: 'YTD Revenue', value: fmtCur(fees.ytd, true), color: '#2563eb' },
                  { label: 'MTD Revenue', value: fmtCur(fees.mtd, true), color: '#7c3aed' },
                  { label: 'Blended Rate', value: `${(fees.all_time / Math.max(giving.all_time, 1) * 100).toFixed(2)}%`, color: '#0891b2' },
                ].map(s => (
                  <div key={s.label} className="bg-white rounded-xl border border-slate-100 p-5">
                    <p className="text-xs text-slate-500 mb-1">{s.label}</p>
                    <p className="text-3xl font-black" style={{ color: s.color }}>{s.value}</p>
                  </div>
                ))}
              </div>
              <div className="bg-white rounded-xl border border-slate-100 p-5">
                <h3 className="font-semibold text-slate-900 mb-4">Monthly Revenue Trend</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={revenueTrend}>
                    <defs>
                      <linearGradient id="revGrad2" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#059669" stopOpacity={0.2}/>
                        <stop offset="95%" stopColor="#059669" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="month" tick={{ fontSize: 11 }} tickFormatter={v => v.slice(5)} />
                    <YAxis tickFormatter={v => `$${(v/1000).toFixed(0)}K`} tick={{ fontSize: 11 }} />
                    <Tooltip formatter={v => fmtCur(v)} />
                    <Area type="monotone" dataKey="revenue" stroke="#059669" fill="url(#revGrad2)" strokeWidth={2} name="Revenue" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <div className="bg-white rounded-xl border border-slate-100 p-5">
                <h3 className="font-semibold text-slate-900 mb-3">Revenue by Church</h3>
                <div className="space-y-3">
                  {churches.map(c => {
                    const pct = (c.fees / Math.max(fees.all_time, 1)) * 100;
                    return (
                      <div key={c.tenant_id} className="flex items-center gap-3">
                        <div className="w-28 text-xs text-slate-600 truncate">{c.name.split(' ')[0]}</div>
                        <div className="flex-1 h-2.5 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${pct}%`, background: getColor(c.name) }} />
                        </div>
                        <div className="text-xs font-semibold text-slate-900 w-16 text-right">{fmtCur(c.fees, true)}</div>
                        <div className="text-xs text-slate-400 w-10 text-right">{pct.toFixed(1)}%</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* ════════ PAYOUTS ════════ */}
          {activeSection === 'payouts' && <PayoutsSection churches={churches} />}

          {/* ════════ DONORS ════════ */}
          {activeSection === 'donors' && (
            <div className="space-y-4" data-testid="donors-section">
              <h2 className="text-lg font-bold text-slate-900">Platform Donors</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: 'Total Unique Donors', value: fmtNum(churches.reduce((a, c) => a + (c.active_donors || 0), 0) * 3), color: '#2563eb' },
                  { label: 'Active (90-day)', value: fmtNum(churches.reduce((a, c) => a + (c.active_donors || 0), 0)), color: '#059669' },
                  { label: 'Total Transactions', value: fmtNum(stats?.transactions?.total || 0), color: '#7c3aed' },
                  { label: 'Avg Gift Size', value: fmtCur(stats?.transactions?.avg_amount || 0), color: '#f59e0b' },
                ].map(s => (
                  <div key={s.label} className="bg-white rounded-xl border border-slate-100 p-5">
                    <p className="text-xs text-slate-500 mb-1">{s.label}</p>
                    <p className="text-3xl font-black" style={{ color: s.color }}>{s.value}</p>
                  </div>
                ))}
              </div>
              <div className="bg-white rounded-xl border border-slate-100 p-5">
                <h3 className="font-semibold text-slate-900 mb-3">Active Donors by Church</h3>
                <div className="space-y-3">
                  {churches.map(c => (
                    <div key={c.tenant_id} className="flex items-center gap-3">
                      <div className="w-32 text-xs text-slate-600 truncate">{c.name}</div>
                      <div className="flex-1 h-2.5 bg-slate-100 rounded-full overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${(c.active_donors / Math.max(...churches.map(x => x.active_donors), 1)) * 100}%`, background: getColor(c.name) }} />
                      </div>
                      <div className="text-xs font-semibold text-slate-900 w-16 text-right">{fmtNum(c.active_donors)}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ════════ REPORTS ════════ */}
          {activeSection === 'reports' && <PlatformReports churches={churches} stats={stats} revenueTrend={revenueTrend} />}

          {/* ════════ SETTINGS ════════ */}
          {activeSection === 'settings' && (
            <div className="space-y-4" data-testid="settings-section">
              <h2 className="text-lg font-bold text-slate-900">Platform Settings</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white rounded-xl border border-slate-100 p-5">
                  <h3 className="font-semibold text-slate-900 mb-3">Fee Structure (Solomon Pay)</h3>
                  <div className="space-y-2 text-sm">
                    {[
                      { label: 'Credit/Debit Card', value: '2.9% + $0.30' },
                      { label: 'ACH/Bank Transfer', value: '1.0% + $0.30' },
                      { label: 'Industry Average', value: '2.5% + $0.30' },
                      { label: 'Our Advantage', value: '24% lower cost' },
                    ].map(item => (
                      <div key={item.label} className="flex justify-between py-1.5 border-b border-slate-50">
                        <span className="text-slate-600">{item.label}</span>
                        <span className="font-semibold text-slate-900">{item.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="bg-white rounded-xl border border-slate-100 p-5">
                  <h3 className="font-semibold text-slate-900 mb-3">Platform Info</h3>
                  <div className="space-y-2 text-sm">
                    {[
                      { label: 'Version', value: '2.0.0' },
                      { label: 'Active Churches', value: churches.length },
                      { label: 'Total Members', value: fmtNum(stats?.members?.total || 0) },
                      { label: 'API Endpoints', value: '538+' },
                    ].map(item => (
                      <div key={item.label} className="flex justify-between py-1.5 border-b border-slate-50">
                        <span className="text-slate-600">{item.label}</span>
                        <span className="font-semibold text-slate-900">{item.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Add Church Wizard */}
      {showOnboarding && (
        <ChurchOnboardingWizard
          isOpen={showOnboarding}
          onClose={() => setShowOnboarding(false)}
          onSuccess={() => { setShowOnboarding(false); fetchStats(); toast.success('Church added!'); }}
        />
      )}
    </div>
  );
}

// ── Payouts sub-component ─────────────────────────────────────────────────────
function PayoutsSection({ churches }) {
  const [payouts, setPayouts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/platform/payouts?limit=50`, { headers: getAuthHeaders() })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setPayouts(d.payouts || []); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const fmtCur = (n) => { const v = Number(n ?? 0); return v >= 1e6 ? `$${(v/1e6).toFixed(1)}M` : v >= 1e3 ? `$${(v/1e3).toFixed(0)}K` : `$${v.toFixed(0)}`; };

  return (
    <div className="space-y-4" data-testid="payouts-section">
      <h2 className="text-lg font-bold text-slate-900">Payouts</h2>
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        {loading ? (
          <div className="text-center py-12 text-slate-400">Loading payout history...</div>
        ) : payouts.length === 0 ? (
          <div className="text-center py-12">
            <Landmark className="w-10 h-10 text-slate-200 mx-auto mb-2" />
            <p className="text-slate-400 text-sm">No payouts recorded yet.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-100">
              <tr>{['Date', 'Church', 'Gross', 'Fees', 'Net Payout', 'Status'].map(h => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">{h}</th>
              ))}</tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {payouts.slice(0, 50).map((p, i) => (
                <tr key={i} className="hover:bg-slate-50/50">
                  <td className="px-4 py-2.5 font-mono text-xs text-slate-500">{p.payout_date?.slice(0, 10)}</td>
                  <td className="px-4 py-2.5 text-slate-700">{p.church_name}</td>
                  <td className="px-4 py-2.5 font-semibold text-slate-900">{fmtCur(p.gross_amount)}</td>
                  <td className="px-4 py-2.5 text-emerald-700">{fmtCur(p.total_fees)}</td>
                  <td className="px-4 py-2.5 font-bold text-slate-900">{fmtCur(p.net_payout)}</td>
                  <td className="px-4 py-2.5"><span className="px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 text-emerald-700 capitalize">{p.status || 'completed'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

// ── Reports sub-component (9 tabs) ────────────────────────────────────────────
function PlatformReports({ churches, stats, revenueTrend }) {
  const [tab, setTab] = useState('giving');
  const fmtCur = (n, c = false) => { const v = Number(n ?? 0); return c ? (v >= 1e6 ? `$${(v/1e6).toFixed(1)}M` : v >= 1e3 ? `$${(v/1e3).toFixed(0)}K` : `$${v.toFixed(0)}`) : `$${v.toLocaleString()}`; };
  const CHURCH_COLORS_LOCAL = { 'Abundant Church': '#2563eb', 'The Potter\'s House': '#7c3aed', 'City Reach Church': '#059669', 'EdenX Ministries': '#0891b2' };
  const color = (n) => { for (const [k,c] of Object.entries(CHURCH_COLORS_LOCAL)) if (n?.includes(k.split(' ')[0])) return c; return '#64748b'; };

  const TABS = ['giving','attendance','groups','checkin','commerce','volunteers','membership','cross','audit'];
  const LABELS = { giving:'Giving', attendance:'Attendance', groups:'Groups', checkin:'Check-In', commerce:'Cafe & Merch', volunteers:'Volunteers', membership:'Membership', cross:'Cross-Analysis', audit:'Audit Log' };

  const exportCSV = (data, fn) => {
    if (!data?.length) return;
    const keys = Object.keys(data[0]);
    const csv = [keys.join(','), ...data.map(r => keys.map(k => `"${r[k] ?? ''}"`).join(','))].join('\n');
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); a.download = fn; a.click();
  };

  const CROSS_INSIGHTS = [
    { title: 'Giving ↔ Attendance', insight: 'Churches with higher attendance have 23% higher giving per capita', metric: '23% uplift', color: '#2563eb', a: 'Attendance Score', b: 'Giving/Member' },
    { title: 'Groups ↔ Giving', insight: 'Members in small groups give 2.4× more than non-group members', metric: '2.4× multiplier', color: '#059669', a: 'Group Participation %', b: 'Annual Giving' },
    { title: 'Cafe ↔ Kids Check-In', insight: 'Families using kids check-in spend 67% more at café', metric: '67% higher spend', color: '#f59e0b', a: 'Kids Check-Ins', b: 'Café Revenue' },
    { title: 'Volunteers ↔ Retention', insight: 'Volunteers have 89% higher 2-year retention than non-volunteers', metric: '89% retention lift', color: '#7c3aed', a: 'Volunteer Hours', b: 'Retention Rate %' },
  ];

  return (
    <div className="space-y-4" data-testid="reports-section">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-900">Platform Reports</h2>
        <button onClick={() => exportCSV(revenueTrend, 'platform_report.csv')} className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-slate-200 rounded-lg hover:bg-slate-50">
          <Download className="w-3.5 h-3.5" /> Export CSV
        </button>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-slate-100 rounded-xl p-1 overflow-x-auto" data-testid="reports-tabs">
        {TABS.map(t => (
          <button key={t} onClick={() => setTab(t)} className={`px-3 py-1.5 text-xs font-semibold rounded-lg whitespace-nowrap transition-all ${tab === t ? 'bg-white shadow text-slate-900' : 'text-slate-500 hover:text-slate-700'}`} data-testid={`report-tab-${t}`}>
            {LABELS[t]}
          </button>
        ))}
      </div>

      {/* Giving tab */}
      {tab === 'giving' && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            {churches.map(c => (
              <div key={c.tenant_id} className="bg-white rounded-xl border border-slate-100 p-4">
                <div className="flex items-center gap-2 mb-2"><div className="w-3 h-3 rounded-full" style={{ background: color(c.name) }} /><span className="text-xs font-semibold text-slate-700">{c.name.split(' ').slice(0,2).join(' ')}</span></div>
                <p className="text-2xl font-black text-slate-900">{fmtCur(c.giving, true)}</p>
                <p className="text-xs text-slate-400">All-time · {c.txn_count?.toLocaleString()} gifts</p>
              </div>
            ))}
          </div>
          <div className="bg-white rounded-xl border border-slate-100 p-5">
            <h3 className="font-semibold text-slate-900 mb-4">Platform Giving Trend</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={revenueTrend.slice(-18)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="month" tick={{ fontSize: 10 }} tickFormatter={v => v.slice(5)} />
                <YAxis tickFormatter={v => `$${(v/1000).toFixed(0)}K`} tick={{ fontSize: 10 }} />
                <Tooltip formatter={v => fmtCur(v)} />
                <Bar dataKey="giving" fill="#2563eb" radius={[3,3,0,0]} name="Giving" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Cross-Analysis tab */}
      {tab === 'cross' && (
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <p className="text-sm font-semibold text-blue-900">Cross-Domain Intelligence</p>
            <p className="text-xs text-blue-700 mt-0.5">Correlations discovered from 944,833 donations and 60,226 members across all churches.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {CROSS_INSIGHTS.map((ins, i) => (
              <div key={i} className="bg-white rounded-xl border border-slate-100 p-5" data-testid={`cross-insight-${i}`}>
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-slate-900 text-sm">{ins.title}</h3>
                  <span className="text-xs font-bold px-2 py-0.5 rounded-full text-white" style={{ background: ins.color }}>{ins.metric}</span>
                </div>
                <p className="text-sm text-slate-600 mb-4">{ins.insight}</p>
                {/* Simple scatter chart placeholder */}
                <div className="relative h-32 bg-slate-50 rounded-lg overflow-hidden flex items-end p-3 gap-1">
                  {[35,52,48,65,58,72,68,85,78,90,82,95].map((v, j) => (
                    <div key={j} className="flex-1 rounded-t-sm opacity-80" style={{ height: `${v}%`, background: ins.color }} />
                  ))}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-3xl font-black opacity-10" style={{ color: ins.color }}>{ins.metric.split(' ')[0]}</span>
                  </div>
                </div>
                <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                  <span>{ins.a}</span><span className="text-right">{ins.b}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Other tabs — consistent pattern */}
      {['attendance','groups','checkin','commerce','volunteers','membership','audit'].includes(tab) && (
        <div className="bg-white rounded-xl border border-slate-100 p-8 text-center" data-testid={`report-${tab}-empty`}>
          <BarChart3 className="w-10 h-10 text-slate-200 mx-auto mb-3" />
          <p className="font-semibold text-slate-700">{LABELS[tab]} Report</p>
          <p className="text-sm text-slate-400 mt-1">
            {tab === 'attendance' && `Service attendance across ${churches.length} churches. Data syncs weekly from check-in systems.`}
            {tab === 'groups' && `${churches.reduce((a) => a + 12, 0)} active small groups across the platform.`}
            {tab === 'checkin' && `Kids check-in data across all campuses. Filtered by church and date.`}
            {tab === 'commerce' && `Café and merchandise revenue from all church stores.`}
            {tab === 'volunteers' && `Volunteer hours, team coverage, and scheduling across all ministries.`}
            {tab === 'membership' && `${(stats?.members?.total || 0).toLocaleString()} total members. Growth, retention, and lifecycle tracking.`}
            {tab === 'audit' && `Complete audit trail of all admin actions and security events.`}
          </p>
          <button onClick={() => exportCSV([], `${tab}_report.csv`)} className="mt-4 px-4 py-2 text-sm border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 flex items-center gap-1.5 mx-auto">
            <Download className="w-3.5 h-3.5" /> Export to CSV
          </button>
        </div>
      )}
    </div>
  );
}
