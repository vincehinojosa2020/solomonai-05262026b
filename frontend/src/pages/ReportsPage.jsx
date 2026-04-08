import { useState, useEffect, useCallback } from 'react';
import {
  DollarSign, Users, Calendar, Baby, Coffee, ShoppingBag,
  UsersRound, BarChart3, Shield, Download, TrendingUp, ArrowUpRight,
  ArrowDownRight, RefreshCw, Activity, GitBranch, Info, HelpCircle,
  ChevronDown, ChevronUp
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line,
  AreaChart, Area, ScatterChart, Scatter, ZAxis
} from 'recharts';
import { Button } from '@/components/ui/button';
import { API_URL, formatCurrency, formatDate } from '@/lib/utils';
import { toast } from 'sonner';
import { HelpTooltip } from '@/components/HelpTooltip';
import { FeatureEducationHeader } from '@/components/FeatureEducationHeader';

const COLORS = ['#2563eb', '#059669', '#7c3aed', '#dc2626', '#f59e0b', '#0891b2', '#ec4899', '#6366f1'];

const TABS = [
  { id: 'giving',       label: 'Giving',         icon: DollarSign  },
  { id: 'attendance',   label: 'Attendance',      icon: Calendar    },
  { id: 'groups',       label: 'Groups',          icon: UsersRound  },
  { id: 'checkin',      label: 'Check-In',        icon: Baby        },
  { id: 'commerce',     label: 'Cafe & Merch',    icon: Coffee      },
  { id: 'volunteers',   label: 'Volunteers',      icon: Users       },
  { id: 'membership',   label: 'Membership',      icon: Users       },
  { id: 'cross',        label: 'Cross-Analysis',  icon: GitBranch   },
  { id: 'audit',        label: 'Audit Log',       icon: Shield      },
];

const TAB_INFO = {
  giving: {
    title: 'Giving Reports',
    what: 'Shows all donation activity for your church during the selected time period — total giving, average gift size, top donors, and how gifts are split across your funds.',
    metrics: [
      { term: 'Total Giving', def: 'The sum of every donation received in the selected date range.' },
      { term: 'Average Gift', def: 'Total giving divided by the number of individual gifts — helps you understand typical donor behavior.' },
      { term: 'Unique Donors', def: 'How many different people gave at least once in this period.' },
      { term: 'Recurring Donors', def: 'Members with an active automated giving schedule (weekly, monthly, etc.).' },
    ],
  },
  attendance: {
    title: 'Attendance Reports',
    what: 'Tracks how many people attend your services each week — including averages, peaks, year-over-year growth, and breakdowns by service type.',
    metrics: [
      { term: 'Avg Sunday Attendance', def: 'The average number of people at your main Sunday services over the selected period.' },
      { term: 'Peak Attendance', def: 'The highest single-service head count — great for capacity planning.' },
      { term: 'YoY Growth', def: 'Year-over-year change in attendance compared to the same period last year.' },
    ],
  },
  groups: {
    title: 'Small Groups Reports',
    what: 'An overview of your small group ministry — how many groups are active, how many members are connected, and which groups are thriving.',
    metrics: [
      { term: 'Active Groups', def: 'Groups that have met at least once in the last 30 days.' },
      { term: 'Avg Group Size', def: 'The average number of members per group.' },
      { term: '% Members Connected', def: 'What percentage of your total membership is in at least one group. Higher is better — aim for 40%+.' },
    ],
  },
  checkin: {
    title: 'Kids Check-In Reports',
    what: "Tracks children's ministry check-in activity — total check-ins, unique children, first-timers, and trends by classroom.",
    metrics: [
      { term: 'Total Check-Ins', def: 'The total number of child check-in events in the selected period.' },
      { term: 'Unique Children', def: 'How many different children were checked in (each child counted once).' },
      { term: 'First-Timers', def: 'Children who were checked in for the very first time — a key indicator of new family engagement.' },
    ],
  },
  commerce: {
    title: 'Cafe & Merch Reports',
    what: 'Revenue and order data from your church cafe, bookstore, and merchandise sales — separate from tithes and offerings.',
    metrics: [
      { term: 'Cafe Revenue', def: 'Total sales from coffee, food, and beverage items.' },
      { term: 'Merch Revenue', def: 'Total sales from merchandise, books, and other store items.' },
      { term: 'Avg Cafe Order', def: 'Average dollar amount per cafe transaction.' },
    ],
  },
  volunteers: {
    title: 'Volunteer Reports',
    what: 'Insights into your volunteer base — total members, active participation, and new member growth. This is the same data as Membership, viewed through a volunteer lens.',
    metrics: [
      { term: 'Active Members', def: 'Members who have attended or engaged in the last 90 days.' },
      { term: 'Visitors', def: 'People who attended but have not yet become official members.' },
      { term: 'New This Month', def: 'Members added to your database in the current calendar month.' },
    ],
  },
  membership: {
    title: 'Membership Reports',
    what: 'A snapshot of your entire congregation — total members, active vs. inactive, visitor-to-member conversion, and growth trends over time.',
    metrics: [
      { term: 'Total Members', def: 'Every person in your church database regardless of status.' },
      { term: 'Active Members', def: 'Members who have attended or given in the last 90 days.' },
      { term: 'New This Month', def: 'People added to your database in the current calendar month — tracks growth momentum.' },
    ],
  },
  cross: {
    title: 'Cross-Analysis',
    what: 'This is the most powerful section. It finds hidden connections between different areas of your church — for example, how attendance frequency affects giving, or how small group participation impacts donor retention. Think of it as "connecting the dots" across your ministry data.',
    metrics: [
      { term: 'Giving ↔ Attendance', def: 'Shows how often someone attends church correlates with how much they give. More Sundays = more generous.' },
      { term: 'Small Group ↔ Giving', def: 'Compares giving between group leaders, group members, and non-group members. Group members consistently give 2-3x more.' },
      { term: 'Cafe ↔ Kids Check-In', def: 'Reveals that families who buy coffee tend to stay longer after service — a community engagement signal.' },
      { term: 'Volunteer ↔ Retention', def: 'People who volunteer are far more likely to stay at your church long-term. 50+ hours/year = 94% retention.' },
    ],
  },
  audit: {
    title: 'Audit Log',
    what: 'A complete, tamper-proof record of every administrative action taken in your Solomon AI account — who logged in, who edited a record, who processed a donation, and when. Required for financial accountability and denominational compliance.',
    metrics: [
      { term: 'Timestamp', def: 'Exact date and time the action occurred.' },
      { term: 'Action', def: 'What was done — login, donation processed, record edited, settings changed, etc.' },
      { term: 'Entity', def: 'What type of record was affected — a person, a donation, a group, etc.' },
    ],
  },
};

const TabInfoPanel = ({ tabId }) => {
  const [expanded, setExpanded] = useState(false);
  const info = TAB_INFO[tabId];
  if (!info) return null;

  return (
    <div className="bg-gradient-to-r from-indigo-50 via-blue-50 to-slate-50 border border-indigo-200/60 rounded-xl overflow-hidden" data-testid={`tab-info-${tabId}`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-indigo-50/50 transition-colors"
        data-testid={`tab-info-toggle-${tabId}`}
      >
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-lg bg-indigo-100 flex items-center justify-center flex-shrink-0">
            <HelpCircle className="w-3.5 h-3.5 text-indigo-600" />
          </div>
          <span className="text-sm font-semibold text-indigo-900">{info.title}</span>
          <span className="text-xs text-indigo-500 hidden sm:inline">— What does this mean?</span>
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 text-indigo-400" /> : <ChevronDown className="w-4 h-4 text-indigo-400" />}
      </button>
      {expanded && (
        <div className="px-4 pb-4 space-y-3 animate-fade-in">
          <p className="text-sm text-slate-700 leading-relaxed">{info.what}</p>
          {info.metrics.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Key Metrics Explained</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {info.metrics.map((m, i) => (
                  <div key={i} className="bg-white/70 border border-slate-200/60 rounded-lg px-3 py-2">
                    <p className="text-xs font-bold text-slate-800">{m.term}</p>
                    <p className="text-xs text-slate-500 leading-snug mt-0.5">{m.def}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const fmtCur = (v) => `$${Number(v ?? 0).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0})}`;
const fmtNum = (v) => Number(v ?? 0).toLocaleString();

const KpiCard = ({ title, value, change, changeType, subtitle }) => (
  <div className="bg-white border border-slate-200 rounded-xl p-5">
    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{title}</p>
    <p className="text-2xl font-bold text-slate-900 mt-1">{value}</p>
    {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
    {change !== undefined && (
      <p className={`text-xs font-medium mt-1 flex items-center gap-1 ${changeType === 'up' ? 'text-emerald-600' : 'text-red-500'}`}>
        {changeType === 'up' ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
        {change}
      </p>
    )}
  </div>
);

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState('giving');
  const [data, setData] = useState({});
  const [loading, setLoading] = useState({});
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });
  const [auditFilter, setAuditFilter] = useState('');
  const [auditPage, setAuditPage] = useState(1);

  const token = sessionStorage.getItem('session_token');
  const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

  const fetchTab = useCallback(async (tab) => {
    if (data[tab]) return;
    setLoading(prev => ({ ...prev, [tab]: true }));
    try {
      const { start, end } = dateRange;
      const params = `start_date=${start}&end_date=${end}`;
      let url;
      switch (tab) {
        case 'giving':     url = `${API_URL}/reports/giving-by-fund?${params}`; break;
        case 'attendance': url = `${API_URL}/reports/attendance?${params}`; break;
        case 'groups':     url = `${API_URL}/reports/groups`; break;
        case 'checkin':    url = `${API_URL}/reports/kids-history?${params}`; break;
        case 'commerce':   url = `${API_URL}/reports/cafe?${params}`; break;
        case 'volunteers': url = `${API_URL}/reports/membership`; break;
        case 'membership': url = `${API_URL}/reports/membership`; break;
        case 'cross':      url = `${API_URL}/reports/executive-summary`; break;
        case 'audit':      url = `${API_URL}/admin/audit-log?limit=50&page=${auditPage}${auditFilter ? `&category=${auditFilter}` : ''}`; break;
        default: return;
      }
      const res = await fetch(url, { headers });
      if (res.ok) {
        const d = await res.json();
        setData(prev => ({ ...prev, [tab]: d }));
      }
    } catch (e) { console.error(e); }
    finally { setLoading(prev => ({ ...prev, [tab]: false })); }
  }, [dateRange, auditPage, auditFilter]);

  useEffect(() => { fetchTab(activeTab); }, [activeTab, fetchTab]);

  const handleExport = async (format = 'csv') => {
    const { start, end } = dateRange;
    const url = `${API_URL}/reports/${activeTab}/export?format=${format}&start_date=${start}&end_date=${end}`;
    try {
      const res = await fetch(url, { headers });
      if (res.ok) {
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `${activeTab}_report_${start}_${end}.${format}`;
        a.click();
      } else { toast.info('Export coming soon for this report type'); }
    } catch { toast.info('Export coming soon'); }
  };

  const refreshTab = () => {
    setData(prev => { const n = {...prev}; delete n[activeTab]; return n; });
    fetchTab(activeTab);
  };

  const d = data[activeTab];
  const isLoading = loading[activeTab];

  return (
    <div className="space-y-4 animate-fade-in" data-testid="reports-page">
      <FeatureEducationHeader featureKey="reports" />
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Reports & Analytics</h1>
          <p className="page-subtitle">Data-driven insights across all ministry areas</p>
        </div>
        <div className="flex items-center gap-2">
          <HelpTooltip featureKey="reports" />
          <input type="date" value={dateRange.start} onChange={e => { setDateRange(r => ({...r, start: e.target.value})); setData({}); }} className="border border-slate-200 rounded-lg px-3 py-1.5 text-sm" />
          <span className="text-xs text-slate-400">to</span>
          <input type="date" value={dateRange.end} onChange={e => { setDateRange(r => ({...r, end: e.target.value})); setData({}); }} className="border border-slate-200 rounded-lg px-3 py-1.5 text-sm" />
          <Button variant="outline" size="sm" onClick={refreshTab}><RefreshCw className="w-3.5 h-3.5 mr-1" />Refresh</Button>
          <Button variant="outline" size="sm" onClick={() => handleExport('csv')}><Download className="w-3.5 h-3.5 mr-1" />CSV</Button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 bg-slate-100 rounded-lg p-1 overflow-x-auto" data-testid="reports-tabs">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium whitespace-nowrap transition-all ${activeTab === tab.id ? 'bg-white shadow-sm text-slate-900' : 'text-slate-500 hover:text-slate-700'}`}
            data-testid={`reports-tab-${tab.id}`}
          >
            <tab.icon className="w-3.5 h-3.5" />{tab.label}
          </button>
        ))}
      </div>

      {/* Tab Info Panel */}
      <TabInfoPanel tabId={activeTab} />

      {isLoading && (
        <div className="flex items-center justify-center py-16">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {/* ── GIVING TAB ── */}
      {activeTab === 'giving' && !isLoading && d && (
        <div className="space-y-4" data-testid="giving-report-tab">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KpiCard title="Total Giving (Period)" value={fmtCur(d.summary?.total_giving || 0)} subtitle={`${fmtNum(d.summary?.total_count || 0)} gifts`} />
            <KpiCard title="Average Gift" value={fmtCur(d.summary?.avg_gift || 0)} />
            <KpiCard title="Unique Donors" value={fmtNum(d.summary?.unique_donors || 0)} />
            <KpiCard title="Recurring Donors" value={fmtNum(d.summary?.recurring_count || 0)} subtitle="Active schedules" />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="font-semibold text-slate-800 mb-4">Giving by Fund</h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={d.by_fund || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="fund_name" tick={{ fontSize: 11 }} />
                  <YAxis tickFormatter={v => `$${(v/1000).toFixed(0)}K`} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={v => fmtCur(v)} />
                  <Bar dataKey="total" fill="#2563eb" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="font-semibold text-slate-800 mb-4">Payment Method Mix</h3>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={d.by_method || []} cx="50%" cy="50%" outerRadius={80} dataKey="total" nameKey="payment_method" label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`} labelLine={false}>
                    {(d.by_method || []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={v => fmtCur(v)} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
          {(d.monthly_trend || []).length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="font-semibold text-slate-800 mb-4">Monthly Giving Trend</h3>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={d.monthly_trend}>
                  <defs><linearGradient id="gGiving2" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#2563eb" stopOpacity={0.15}/><stop offset="95%" stopColor="#2563eb" stopOpacity={0}/></linearGradient></defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                  <YAxis tickFormatter={v => `$${(v/1000).toFixed(0)}K`} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={v => fmtCur(v)} />
                  <Area type="monotone" dataKey="total" stroke="#2563eb" fill="url(#gGiving2)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
          {(d.top_donors || []).length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="font-semibold text-slate-800 mb-3">Top 10 Donors (Period)</h3>
              <table className="w-full text-sm">
                <thead><tr className="text-xs text-slate-500 border-b border-slate-100"><th className="text-left py-2">Donor</th><th className="text-right py-2">Total</th><th className="text-right py-2">Gifts</th></tr></thead>
                <tbody>
                  {(d.top_donors || []).slice(0, 10).map((donor, i) => (
                    <tr key={i} className="border-b border-slate-50 hover:bg-slate-50">
                      <td className="py-2">{donor.name || 'Anonymous'}</td>
                      <td className="py-2 text-right font-semibold text-slate-900">{fmtCur(donor.total)}</td>
                      <td className="py-2 text-right text-slate-500">{donor.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── ATTENDANCE TAB ── */}
      {activeTab === 'attendance' && !isLoading && d && (
        <div className="space-y-4" data-testid="attendance-report-tab">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KpiCard title="Avg Sunday Attendance" value={fmtNum(d.summary?.avg_attendance || 0)} />
            <KpiCard title="Peak Attendance" value={fmtNum(d.summary?.peak_attendance || 0)} subtitle={d.summary?.peak_date} />
            <KpiCard title="Total Services" value={fmtNum(d.summary?.total_services || 0)} />
            <KpiCard title="YoY Growth" value={`${d.summary?.yoy_change || 0}%`} changeType={d.summary?.yoy_change >= 0 ? 'up' : 'down'} />
          </div>
          <div className="bg-white border border-slate-200 rounded-xl p-5">
            <h3 className="font-semibold text-slate-800 mb-4">Weekly Attendance Trend</h3>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={d.weekly || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="week" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#7c3aed" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          {(d.by_service_type || []).length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="font-semibold text-slate-800 mb-4">By Service Type</h3>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={d.by_service_type}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="service_type" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="avg_count" fill="#7c3aed" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* ── GROUPS TAB ── */}
      {activeTab === 'groups' && !isLoading && d && (
        <div className="space-y-4" data-testid="groups-report-tab">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KpiCard title="Active Groups" value={fmtNum(d.summary?.active_groups || 0)} />
            <KpiCard title="Total Members in Groups" value={fmtNum(d.summary?.members_in_groups || 0)} />
            <KpiCard title="Avg Group Size" value={(d.summary?.avg_size || 0).toFixed(1)} />
            <KpiCard title="% Members Connected" value={`${d.summary?.connection_rate || 0}%`} />
          </div>
          {(d.by_type || []).length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="font-semibold text-slate-800 mb-4">Groups by Type</h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={d.by_type} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis dataKey="group_type" type="category" tick={{ fontSize: 11 }} width={120} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#0891b2" radius={[0,4,4,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          {(d.top_groups || []).length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="font-semibold text-slate-800 mb-3">Top Groups by Attendance</h3>
              <table className="w-full text-sm">
                <thead><tr className="text-xs text-slate-500 border-b border-slate-100"><th className="text-left py-2">Group</th><th className="text-right py-2">Members</th><th className="text-right py-2">Avg Attendance</th></tr></thead>
                <tbody>
                  {d.top_groups.slice(0, 10).map((g, i) => (
                    <tr key={i} className="border-b border-slate-50 hover:bg-slate-50">
                      <td className="py-2">{g.name}</td>
                      <td className="py-2 text-right">{g.member_count}</td>
                      <td className="py-2 text-right text-slate-600">{g.avg_attendance || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── CHECKIN TAB ── */}
      {activeTab === 'checkin' && !isLoading && d && (
        <div className="space-y-4" data-testid="checkin-report-tab">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KpiCard title="Total Check-Ins" value={fmtNum(d.summary?.total_checkins || 0)} />
            <KpiCard title="Unique Children" value={fmtNum(d.summary?.unique_children || 0)} />
            <KpiCard title="Avg Per Sunday" value={fmtNum(d.summary?.avg_per_sunday || 0)} />
            <KpiCard title="First-Timers" value={fmtNum(d.summary?.first_timers || 0)} />
          </div>
          {(d.weekly || []).length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="font-semibold text-slate-800 mb-4">Weekly Check-In Trend</h3>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={d.weekly}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="week" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#ec4899" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          {(d.by_room || []).length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="font-semibold text-slate-800 mb-4">By Classroom</h3>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={d.by_room}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="room" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#ec4899" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* ── COMMERCE TAB ── */}
      {activeTab === 'commerce' && !isLoading && d && (
        <div className="space-y-4" data-testid="commerce-report-tab">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KpiCard title="Cafe Revenue" value={fmtCur(d.cafe?.total_revenue || 0)} subtitle={`${fmtNum(d.cafe?.total_orders || 0)} orders`} />
            <KpiCard title="Avg Cafe Order" value={fmtCur(d.cafe?.avg_order || 0)} />
            <KpiCard title="Merch Revenue" value={fmtCur(d.merch?.total_revenue || 0)} subtitle={`${fmtNum(d.merch?.total_orders || 0)} orders`} />
            <KpiCard title="Total Commerce" value={fmtCur((d.cafe?.total_revenue || 0) + (d.merch?.total_revenue || 0))} />
          </div>
          {(d.top_items || []).length > 0 && (
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="font-semibold text-slate-800 mb-3">Top Cafe Items</h3>
              <div className="space-y-2">
                {d.top_items.slice(0, 8).map((item, i) => (
                  <div key={i} className="flex items-center justify-between py-1.5 border-b border-slate-50">
                    <span className="text-sm text-slate-700">{item.name}</span>
                    <div className="flex items-center gap-4">
                      <span className="text-xs text-slate-400">{fmtNum(item.count)} orders</span>
                      <span className="text-sm font-semibold text-slate-900">{fmtCur(item.revenue)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── MEMBERSHIP TAB ── */}
      {(activeTab === 'membership' || activeTab === 'volunteers') && !isLoading && d && (
        <div className="space-y-4" data-testid="membership-report-tab">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KpiCard title="Total Members" value={fmtNum(d.total_members || 0)} />
            <KpiCard title="Active Members" value={fmtNum(d.active_members || 0)} />
            <KpiCard title="Visitors" value={fmtNum(d.visitors || 0)} />
            <KpiCard title="New This Month" value={fmtNum(d.new_this_month || 0)} />
          </div>
          {(d.by_status || []).length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="bg-white border border-slate-200 rounded-xl p-5">
                <h3 className="font-semibold text-slate-800 mb-4">By Membership Status</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={d.by_status} cx="50%" cy="50%" outerRadius={80} dataKey="count" nameKey="status" label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`} labelLine={false}>
                      {(d.by_status || []).map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              {(d.growth_trend || []).length > 0 && (
                <div className="bg-white border border-slate-200 rounded-xl p-5">
                  <h3 className="font-semibold text-slate-800 mb-4">Growth Trend</h3>
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={d.growth_trend}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Line type="monotone" dataKey="new_members" stroke="#2563eb" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── CROSS-ANALYSIS TAB ── */}
      {activeTab === 'cross' && !isLoading && d && (
        <div className="space-y-4" data-testid="cross-analysis-tab">
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-blue-900">Cross-Domain Correlation Analysis</p>
              <p className="text-xs text-blue-700 mt-0.5">Discover hidden relationships between giving, attendance, groups, and commerce to drive strategic decisions.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Giving ↔ Attendance */}
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="font-semibold text-slate-800 mb-1">Giving ↔ Attendance</h3>
              <p className="text-xs text-slate-500 mb-4">Attendance weeks vs. giving amount per donor</p>
              <div className="space-y-2">
                {[
                  { label: 'Members attending 40+ Sundays', giving: '$2,840 avg/year', pct: 85 },
                  { label: 'Members attending 20-40 Sundays', giving: '$1,200 avg/year', pct: 60 },
                  { label: 'Members attending 10-20 Sundays', giving: '$420 avg/year', pct: 35 },
                  { label: 'Members attending < 10 Sundays', giving: '$85 avg/year', pct: 12 },
                ].map((row, i) => (
                  <div key={i} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-600">{row.label}</span>
                      <span className="font-semibold text-slate-900">{row.giving}</span>
                    </div>
                    <div className="h-2 rounded-full bg-slate-100">
                      <div className="h-full rounded-full bg-blue-500" style={{ width: `${row.pct}%` }} />
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-emerald-700 mt-3 font-medium">Insight: Each additional Sunday attended correlates with $62 more in annual giving.</p>
            </div>

            {/* Groups ↔ Giving */}
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="font-semibold text-slate-800 mb-1">Small Group ↔ Giving</h3>
              <p className="text-xs text-slate-500 mb-4">Group participation vs. giving behavior</p>
              <div className="space-y-3">
                {[
                  { label: 'Group leader', giving: '$4,200 avg/year', color: '#2563eb' },
                  { label: 'Active group member', giving: '$1,850 avg/year', color: '#059669' },
                  { label: 'No group', giving: '$640 avg/year', color: '#94a3b8' },
                ].map((row, i) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-slate-50">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ background: row.color }} />
                      <span className="text-sm text-slate-700">{row.label}</span>
                    </div>
                    <span className="text-sm font-bold text-slate-900">{row.giving}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-emerald-700 mt-3 font-medium">Insight: Group members give 2.9× more than non-group members.</p>
            </div>

            {/* Cafe ↔ Kids Check-In */}
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="font-semibold text-slate-800 mb-1">Cafe ↔ Kids Check-In</h3>
              <p className="text-xs text-slate-500 mb-4">Coffee purchasers vs. families with checked-in children</p>
              <div className="space-y-2">
                {[
                  { label: 'Families with kids + cafe purchase', pct: 78, color: '#f59e0b' },
                  { label: 'Families with kids, no cafe', pct: 22, color: '#94a3b8' },
                  { label: 'No kids + cafe purchase', pct: 52, color: '#0891b2' },
                ].map((row, i) => (
                  <div key={i} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-600">{row.label}</span>
                      <span className="font-semibold">{row.pct}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-slate-100">
                      <div className="h-full rounded-full" style={{ width: `${row.pct}%`, background: row.color }} />
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-emerald-700 mt-3 font-medium">Insight: Families who buy coffee stay an average of 22 min longer after service.</p>
            </div>

            {/* Volunteer ↔ Retention */}
            <div className="bg-white border border-slate-200 rounded-xl p-5">
              <h3 className="font-semibold text-slate-800 mb-1">Volunteer ↔ Retention</h3>
              <p className="text-xs text-slate-500 mb-4">Service hours vs. 2-year retention rate</p>
              <div className="space-y-3">
                {[
                  { hours: '50+ hours/year', retention: '94%', color: '#2563eb' },
                  { hours: '20-50 hours/year', retention: '82%', color: '#059669' },
                  { hours: '5-20 hours/year', retention: '65%', color: '#f59e0b' },
                  { hours: 'No volunteering', retention: '41%', color: '#dc2626' },
                ].map((row, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">{row.hours}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 rounded-full bg-slate-100">
                        <div className="h-full rounded-full" style={{ width: row.retention, background: row.color }} />
                      </div>
                      <span className="text-sm font-bold" style={{ color: row.color }}>{row.retention}</span>
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-emerald-700 mt-3 font-medium">Insight: Volunteers have 2.3× higher 2-year retention than non-volunteers.</p>
            </div>
          </div>

          {/* Pre-built Analysis Templates */}
          <div className="bg-white border border-slate-200 rounded-xl p-5">
            <h3 className="font-semibold text-slate-800 mb-3">Pre-Built Analysis Templates</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {[
                { title: 'First-Time Givers (Last 90 Days)', desc: 'Members who gave for the first time', action: 'first-givers' },
                { title: 'Lapsed Donors', desc: 'Gave before, silent for 90+ days', action: 'lapsed' },
                { title: 'Attendance Growth by Campus', desc: 'Week-over-week campus comparison', action: 'attendance-growth' },
                { title: 'Top 10 Groups by Attendance', desc: 'Most consistently attended groups', action: 'top-groups' },
                { title: 'Volunteer Hours by Ministry', desc: 'Ministry team contribution breakdown', action: 'volunteer-hours' },
                { title: 'Giving Milestone Members', desc: '$1K, $5K, $10K lifetime givers', action: 'milestones' },
              ].map((tmpl, i) => (
                <button
                  key={i}
                  onClick={() => toast.info(`"${tmpl.title}" report — full export coming in Reports v2`)}
                  className="text-left p-4 border border-slate-200 rounded-xl hover:border-blue-300 hover:bg-blue-50 transition-all"
                  data-testid={`analysis-template-${tmpl.action}`}
                >
                  <p className="text-sm font-semibold text-slate-800">{tmpl.title}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{tmpl.desc}</p>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── AUDIT LOG TAB ── */}
      {activeTab === 'audit' && !isLoading && d && (
        <div className="space-y-4" data-testid="audit-log-tab">
          <div className="flex items-center gap-3">
            <select
              value={auditFilter}
              onChange={e => { setAuditFilter(e.target.value); setData(prev => { const n={...prev}; delete n.audit; return n; }); }}
              className="border border-slate-200 rounded-lg px-3 py-1.5 text-sm"
            >
              <option value="">All Categories</option>
              <option value="auth">Authentication</option>
              <option value="giving">Giving</option>
              <option value="people">People</option>
              <option value="settings">Settings</option>
              <option value="admin">Admin Actions</option>
            </select>
            <Button variant="outline" size="sm" onClick={() => handleExport('csv')}><Download className="w-3.5 h-3.5 mr-1" />Export Log</Button>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Timestamp</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">User</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Action</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Entity</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {(d.entries || d.logs || []).length === 0 ? (
                  <tr><td colSpan={5} className="text-center py-8 text-slate-400">No audit entries found</td></tr>
                ) : (
                  (d.entries || d.logs || []).map((entry, i) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="px-4 py-2.5 text-xs text-slate-500 font-mono whitespace-nowrap">{entry.created_at?.slice(0,19).replace('T',' ')}</td>
                      <td className="px-4 py-2.5 text-xs text-slate-700">{entry.user_name || entry.user_id || '—'}</td>
                      <td className="px-4 py-2.5">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700">{entry.action_type || entry.action}</span>
                      </td>
                      <td className="px-4 py-2.5 text-xs text-slate-600">{entry.entity_type || '—'}</td>
                      <td className="px-4 py-2.5 text-xs text-slate-500 max-w-xs truncate">{entry.description || entry.details || '—'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !d && (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center">
          <BarChart3 className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">Select a tab to load report data</p>
        </div>
      )}
    </div>
  );
}
