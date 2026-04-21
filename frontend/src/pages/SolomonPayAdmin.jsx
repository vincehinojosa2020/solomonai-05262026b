import { useState, useEffect, useCallback } from 'react';
import { usePolling } from '@/hooks/usePolling';
import { DollarSign, TrendingUp, RefreshCw, Users, FileText, Download, Search, ChevronLeft, ChevronRight, ArrowUpRight, ArrowDownRight, Building2, CreditCard, Settings, Clock, Filter, Eye, Zap, Archive, Plus, Pencil, X, QrCode, RotateCcw, Terminal, PieChart, PlayCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, PieChart as RPieChart, Pie, Cell } from 'recharts';
import { Button } from '@/components/ui/button';
import { API_URL, formatCurrency, formatDate } from '@/lib/utils';
import { toast } from 'sonner';
import AdminRecurringGiving from '@/components/AdminRecurringGiving';
import { HelpTooltip } from '@/components/HelpTooltip';
import { FeatureEducationHeader } from '@/components/FeatureEducationHeader';

const TABS = [
  { id: 'dashboard', label: 'Dashboard', icon: TrendingUp },
  { id: 'transactions', label: 'Transactions', icon: FileText },
  { id: 'payouts', label: 'Payouts', icon: Building2 },
  { id: 'funds', label: 'Funds', icon: DollarSign },
  { id: 'recurring', label: 'Recurring', icon: RefreshCw },
  { id: 'donors', label: 'Donors', icon: Users },
  { id: 'statements', label: 'Statements', icon: FileText },
  { id: 'settings', label: 'Settings', icon: Settings },
];

const StatCard = ({ title, value, subtitle, trend }) => (
  <div className="bg-white border border-slate-200 rounded-xl p-5" data-testid={`stat-${title.toLowerCase().replace(/\s/g,'-')}`}>
    <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{title}</p>
    <p className="text-2xl font-bold text-slate-900 mt-1">{value}</p>
    {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
    {trend && <p className={`text-xs mt-1 flex items-center gap-1 ${trend > 0 ? 'text-green-600' : 'text-red-500'}`}>{trend > 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}{Math.abs(trend)}% vs last month</p>}
  </div>
);

export default function SolomonPayAdmin() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashData, setDashData] = useState(null);
  const [sourceFilter, setSourceFilter] = useState('all'); // all | stripe | demo
  const [transactions, setTransactions] = useState({ data: [], total: 0 });
  const [txPage, setTxPage] = useState(1);
  const [txSearch, setTxSearch] = useState('');
  const [txFund, setTxFund] = useState('');
  const [txDateFrom, setTxDateFrom] = useState('');
  const [txDateTo, setTxDateTo] = useState('');
  const [payouts, setPayouts] = useState({ available_balance: 0, payouts: [] });
  const [funds, setFunds] = useState([]);
  const [donors, setDonors] = useState({ donors: [], total: 0 });
  const [donorSearch, setDonorSearch] = useState('');
  const [donorPage, setDonorPage] = useState(1);
  const [donorDetail, setDonorDetail] = useState(null);
  const [stmtYear, setStmtYear] = useState(new Date().getFullYear() - 1);
  const [stmtResult, setStmtResult] = useState(null);
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showFundModal, setShowFundModal] = useState(false);
  const [editFund, setEditFund] = useState(null);
  const [schedulerStatus, setSchedulerStatus] = useState(null);
  const [schedulerRunning, setSchedulerRunning] = useState(false);
  const [fundForm, setFundForm] = useState({ name: '', description: '', goal_amount: '' });
  const [donorIQ, setDonorIQ] = useState(null);
  const [showVT, setShowVT] = useState(false);
  const [vtForm, setVtForm] = useState({ person_name: '', person_email: '', amount: '', fund_name: 'General Fund', payment_method: 'cash', note: '', cover_fees: false });
  const [qrCodes, setQrCodes] = useState([]);

  const headers = () => {
    const t = sessionStorage.getItem('session_token');
    return t ? { 'Authorization': `Bearer ${t}` } : {};
  };

  const fetchDashboard = useCallback(async () => {
    try {
      const qs = sourceFilter && sourceFilter !== 'all' ? `?source=${sourceFilter}` : '';
      const res = await fetch(`${API_URL}/admin/solomonpay/dashboard${qs}`, { headers: headers() });
      if (res.ok) setDashData(await res.json());
    } catch (e) { console.error(e); }
  }, [sourceFilter]);

  const fetchTransactions = useCallback(async () => {
    const params = new URLSearchParams({ page: txPage, per_page: 50 });
    if (txSearch) params.set('search', txSearch);
    if (txFund) params.set('fund', txFund);
    if (txDateFrom) params.set('date_from', txDateFrom);
    if (txDateTo) params.set('date_to', txDateTo);
    if (sourceFilter && sourceFilter !== 'all') params.set('source', sourceFilter);
    try {
      const res = await fetch(`${API_URL}/admin/solomonpay/transactions?${params}`, { headers: headers() });
      if (res.ok) setTransactions(await res.json());
    } catch (e) { console.error(e); }
  }, [txPage, txSearch, txFund, txDateFrom, txDateTo, sourceFilter]);

  const fetchPayouts = async () => {
    try { const res = await fetch(`${API_URL}/admin/solomonpay/payouts`, { headers: headers() }); if (res.ok) setPayouts(await res.json()); } catch (e) { console.error(e); }
  };

  const fetchFunds = async () => {
    try { const res = await fetch(`${API_URL}/admin/solomonpay/funds`, { headers: headers() }); if (res.ok) { const d = await res.json(); setFunds(d.funds || []); } } catch (e) { console.error(e); }
  };

  const fetchDonors = useCallback(async () => {
    const params = new URLSearchParams({ page: donorPage, per_page: 50 });
    if (donorSearch) params.set('search', donorSearch);
    try { const res = await fetch(`${API_URL}/admin/solomonpay/donors?${params}`, { headers: headers() }); if (res.ok) setDonors(await res.json()); } catch (e) { console.error(e); }
  }, [donorPage, donorSearch]);

  const fetchSettings = async () => {
    try { const res = await fetch(`${API_URL}/admin/solomonpay/settings`, { headers: headers() }); if (res.ok) setSettings(await res.json()); } catch (e) { console.error(e); }
  };

  const fetchSchedulerStatus = async () => {
    try { const res = await fetch(`${API_URL}/admin/solomonpay/scheduler/status`, { headers: headers() }); if (res.ok) setSchedulerStatus(await res.json()); } catch (e) { console.error(e); }
  };

  const triggerSchedulerRun = async () => {
    setSchedulerRunning(true);
    try {
      const res = await fetch(`${API_URL}/admin/solomonpay/scheduler/run-now`, { method: 'POST', headers: headers() });
      if (res.ok) { const d = await res.json(); toast.success(`Batch run complete: ${d.successful} processed, ${d.failed} failed`); fetchSchedulerStatus(); }
      else { toast.error('Batch run failed'); }
    } catch { toast.error('Failed to trigger run'); } finally { setSchedulerRunning(false); }
  };

  const resumeSchedule = async (scheduleId) => {
    try {
      const res = await fetch(`${API_URL}/admin/solomonpay/scheduler/resume/${scheduleId}`, { method: 'POST', headers: headers() });
      if (res.ok) { toast.success('Schedule resumed'); fetchSchedulerStatus(); }
    } catch { toast.error('Failed to resume'); }
  };

  useEffect(() => { fetchDashboard(); }, []);
  useEffect(() => { if (activeTab === 'transactions') fetchTransactions(); }, [activeTab, fetchTransactions]);
  useEffect(() => { if (activeTab === 'payouts') fetchPayouts(); }, [activeTab]);
  useEffect(() => { if (activeTab === 'funds') fetchFunds(); }, [activeTab]);
  useEffect(() => { if (activeTab === 'donors') fetchDonors(); }, [activeTab, fetchDonors]);
  useEffect(() => { if (activeTab === 'settings') fetchSettings(); }, [activeTab]);
  useEffect(() => { if (activeTab === 'recurring') fetchSchedulerStatus(); }, [activeTab]);

  // Real-time polling (5s for giving/transactions, 30s for general)
  usePolling(fetchDashboard, 5000, activeTab === 'dashboard');
  usePolling(fetchTransactions, 5000, activeTab === 'transactions');
  usePolling(fetchPayouts, 10000, activeTab === 'payouts');
  usePolling(fetchDonors, 30000, activeTab === 'donors');

  const requestPayout = async (type) => {
    const amount = payouts.available_balance;
    if (amount <= 0) { toast.error('No funds available'); return; }
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/admin/solomonpay/payouts/request`, { method: 'POST', headers: { ...headers(), 'Content-Type': 'application/json' }, body: JSON.stringify({ type, amount }) });
      if (res.ok) { const d = await res.json(); toast.success(d.message); fetchPayouts(); }
    } catch { toast.error('Failed'); } finally { setLoading(false); }
  };

  const exportCSV = () => {
    const t = sessionStorage.getItem('session_token');
    window.open(`${API_URL}/admin/solomonpay/transactions/export?${txDateFrom ? `date_from=${txDateFrom}&` : ''}${txDateTo ? `date_to=${txDateTo}` : ''}`, '_blank');
  };

  const generateStatements = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/admin/solomonpay/statements/bulk`, { method: 'POST', headers: { ...headers(), 'Content-Type': 'application/json' }, body: JSON.stringify({ year: stmtYear }) });
      if (res.ok) { const d = await res.json(); setStmtResult(d); toast.success(d.message); }
    } catch { toast.error('Failed'); } finally { setLoading(false); }
  };

  const openDonorDetail = async (personId) => {
    try {
      const res = await fetch(`${API_URL}/admin/solomonpay/donors/${personId}`, { headers: headers() });
      if (res.ok) setDonorDetail(await res.json());
    } catch (e) { console.error(e); }
  };

  const saveFund = async () => {
    setLoading(true);
    try {
      if (editFund) {
        await fetch(`${API_URL}/admin/solomonpay/funds/${editFund.id}`, { method: 'PUT', headers: { ...headers(), 'Content-Type': 'application/json' }, body: JSON.stringify({ name: fundForm.name, description: fundForm.description, goal_amount: fundForm.goal_amount ? parseFloat(fundForm.goal_amount) : null }) });
        toast.success('Fund updated');
      } else {
        await fetch(`${API_URL}/admin/solomonpay/funds`, { method: 'POST', headers: { ...headers(), 'Content-Type': 'application/json' }, body: JSON.stringify({ name: fundForm.name, description: fundForm.description, goal_amount: fundForm.goal_amount ? parseFloat(fundForm.goal_amount) : null }) });
        toast.success('Fund created');
      }
      setShowFundModal(false); setEditFund(null); setFundForm({ name: '', description: '', goal_amount: '' }); fetchFunds();
    } catch { toast.error('Failed'); } finally { setLoading(false); }
  };

  const archiveFund = async (id) => {
    if (!confirm('Archive this fund?')) return;
    try { await fetch(`${API_URL}/admin/solomonpay/funds/${id}`, { method: 'DELETE', headers: headers() }); toast.success('Archived'); fetchFunds(); } catch { toast.error('Failed'); }
  };

  const saveSettings = async () => {
    setLoading(true);
    try {
      await fetch(`${API_URL}/admin/solomonpay/settings`, { method: 'PUT', headers: { ...headers(), 'Content-Type': 'application/json' }, body: JSON.stringify(settings) });
      toast.success('Settings saved');
    } catch { toast.error('Failed'); } finally { setLoading(false); }
  };

  const fetchDonorIQ = async () => {
    try { const res = await fetch(`${API_URL}/admin/solomonpay/donor-insights`, { headers: headers() }); if (res.ok) setDonorIQ(await res.json()); } catch (e) { console.error(e); }
  };

  const submitVirtualTerminal = async () => {
    if (!vtForm.amount || parseFloat(vtForm.amount) <= 0) { toast.error('Enter a valid amount'); return; }
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/admin/solomonpay/virtual-terminal`, { method: 'POST', headers: { ...headers(), 'Content-Type': 'application/json' }, body: JSON.stringify({ ...vtForm, amount: parseFloat(vtForm.amount) }) });
      if (res.ok) { const d = await res.json(); toast.success(d.message); setShowVT(false); setVtForm({ person_name: '', person_email: '', amount: '', fund_name: 'General Fund', payment_method: 'cash', note: '', cover_fees: false }); fetchDashboard(); }
      else { const err = await res.json(); toast.error(err.detail || 'Failed'); }
    } catch { toast.error('Failed'); } finally { setLoading(false); }
  };

  const refundDonation = async (donationId) => {
    if (!confirm('Are you sure you want to refund this donation?')) return;
    try {
      const res = await fetch(`${API_URL}/admin/solomonpay/refund/${donationId}`, { method: 'POST', headers: headers() });
      if (res.ok) { const d = await res.json(); toast.success(d.message); fetchTransactions(); fetchDashboard(); }
      else { const err = await res.json(); toast.error(err.detail || 'Refund failed'); }
    } catch { toast.error('Refund failed'); }
  };

  const fetchQRCodes = async () => {
    try { const res = await fetch(`${API_URL}/admin/solomonpay/qr-codes`, { headers: headers() }); if (res.ok) { const d = await res.json(); setQrCodes(d.qr_codes || []); } } catch (e) { console.error(e); }
  };

  useEffect(() => { if (activeTab === 'dashboard') { fetchDonorIQ(); fetchQRCodes(); } }, [activeTab]);

  return (
    <div className="space-y-4" data-testid="solomonpay-admin">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">SolomonPay</h1>
          <p className="page-subtitle">Payment processing & giving management</p>
        </div>
        <HelpTooltip featureKey="giving" />
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 bg-slate-100 rounded-lg p-1 overflow-x-auto" data-testid="solomonpay-tabs">
        {TABS.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium whitespace-nowrap transition-all ${activeTab === tab.id ? 'bg-white shadow-sm text-slate-900' : 'text-slate-500 hover:text-slate-700'}`} data-testid={`tab-${tab.id}`}>
            <tab.icon className="w-3.5 h-3.5" /> {tab.label}
          </button>
        ))}
      </div>

      {/* === DASHBOARD TAB === */}
      {activeTab === 'dashboard' && dashData && (
        <div className="space-y-4" data-testid="solomonpay-dashboard-tab">
        <FeatureEducationHeader featureKey="solomonpay" />

          {/* Source filter — separate Stripe real transactions from seeded demo data */}
          <div className="flex items-center gap-2 flex-wrap" data-testid="solomonpay-source-toggle">
            {[
              { key: 'all', label: 'All', count: dashData.source_counts?.total ?? 0 },
              { key: 'stripe', label: 'Stripe', count: dashData.source_counts?.stripe ?? 0 },
              { key: 'demo', label: 'Demo data', count: dashData.source_counts?.demo ?? 0 },
            ].map((opt) => (
              <button
                key={opt.key}
                onClick={() => setSourceFilter(opt.key)}
                data-testid={`solomonpay-source-${opt.key}`}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-colors border ${
                  sourceFilter === opt.key
                    ? 'bg-slate-900 text-white border-slate-900'
                    : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
                }`}
              >
                {opt.label}
                <span className="ml-1.5 text-[10px] opacity-70 font-mono">{opt.count}</span>
              </button>
            ))}
            {sourceFilter === 'stripe' && (
              <span className="ml-2 text-[11px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-medium">
                Showing real Stripe transactions only
              </span>
            )}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard title="Today" value={formatCurrency(dashData.today.total)} subtitle={`${dashData.today.count} gifts`} />
            <StatCard title="This Week" value={formatCurrency(dashData.week.total)} subtitle={`${dashData.week.count} gifts`} />
            <StatCard title="This Month" value={formatCurrency(dashData.month.total)} subtitle={`${dashData.month.count} gifts`} />
            <StatCard title="Year to Date" value={formatCurrency(dashData.ytd.total)} subtitle={`${dashData.ytd.count} gifts`} />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <StatCard title="Active Recurring" value={dashData.active_recurring} />
            <StatCard title="Average Gift" value={formatCurrency(dashData.avg_gift)} />
            <StatCard title="Top Fund" value={dashData.top_fund} />
          </div>

          {/* 12-Month Chart */}
          <div className="bg-white border border-slate-200 rounded-xl p-5" data-testid="giving-trend-chart">
            <h3 className="text-sm font-semibold text-slate-800 mb-4">Giving Trend (12 Months)</h3>
            <div className="h-64" style={{ minWidth: '200px', minHeight: '200px' }}>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={dashData.trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} tickFormatter={v => { const [y,m] = v.split('-'); return ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][parseInt(m)-1]; }} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
                  <Tooltip formatter={v => formatCurrency(v)} labelFormatter={v => v} />
                  <Bar dataKey="total" fill="#0f172a" radius={[4,4,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Recent 20 Transactions */}
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-slate-100">
              <h3 className="text-sm font-semibold text-slate-800">Recent Transactions</h3>
              <button onClick={() => setActiveTab('transactions')} className="text-xs text-blue-600 hover:underline">View All</button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="bg-slate-50 text-xs text-slate-500 uppercase"><th className="px-4 py-2 text-left">Date</th><th className="px-4 py-2 text-left">Donor</th><th className="px-4 py-2 text-left">Fund</th><th className="px-4 py-2 text-right">Amount</th><th className="px-4 py-2 text-left">Source</th><th className="px-4 py-2 text-left">Status</th></tr></thead>
                <tbody>
                  {(dashData.recent_transactions || []).slice(0, 20).map((tx, i) => (
                    <tr key={i} className="border-t border-slate-50 hover:bg-slate-50">
                      <td className="px-4 py-2.5 font-mono text-xs">{tx.donation_date}</td>
                      <td className="px-4 py-2.5 font-medium text-slate-700">{tx.person_name || tx.donor_name || 'Anonymous'}</td>
                      <td className="px-4 py-2.5 text-slate-500">{tx.fund_name || 'General'}</td>
                      <td className="px-4 py-2.5 text-right font-mono font-semibold">{formatCurrency(tx.amount)}</td>
                      <td className="px-4 py-2.5">
                        {tx.payment_source === 'stripe' ? (
                          <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-100" data-testid={`tx-badge-stripe-${i}`}>
                            STRIPE{tx.test_mode ? ' · TEST' : ''}
                          </span>
                        ) : (
                          <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider bg-slate-100 text-slate-500 border border-slate-200">
                            DEMO
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-2.5"><span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${tx.status === 'completed' || tx.status === 'succeeded' ? 'bg-green-50 text-green-700' : tx.status === 'refunded' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700'}`}>{tx.status || 'completed'}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* DonorIQ Engagement Insights */}
          {donorIQ && (
            <div className="bg-white border border-slate-200 rounded-xl p-5" data-testid="donor-iq-panel">
              <h3 className="text-sm font-semibold text-slate-800 mb-4">DonorIQ — Engagement Stages</h3>
              <div className="grid grid-cols-3 md:grid-cols-6 gap-2 mb-4">
                {[
                  { key: 'recurring', label: 'Recurring', color: '#16a34a' },
                  { key: 'regular', label: 'Regular', color: '#2563eb' },
                  { key: 'occasional', label: 'Occasional', color: '#8b5cf6' },
                  { key: 'once', label: 'First-Time', color: '#f59e0b' },
                  { key: 'at_risk', label: 'At Risk', color: '#f97316' },
                  { key: 'lapsed', label: 'Lapsed', color: '#dc2626' },
                ].map(s => (
                  <div key={s.key} className="text-center p-3 rounded-lg" style={{ background: s.color + '10' }}>
                    <p className="text-2xl font-bold" style={{ color: s.color }}>{donorIQ.stages[s.key] || 0}</p>
                    <p className="text-xs font-medium text-slate-500">{s.label}</p>
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-400">Total: {donorIQ.total_donors} unique donors tracked</p>
            </div>
          )}

          {/* Quick Actions */}
          <div className="grid grid-cols-2 gap-3">
            <button onClick={() => setShowVT(true)} className="flex items-center gap-3 p-4 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors" data-testid="virtual-terminal-btn">
              <Terminal className="w-5 h-5 text-slate-600" />
              <div className="text-left"><p className="text-sm font-semibold text-slate-800">Virtual Terminal</p><p className="text-xs text-slate-400">Process donation on behalf of a donor</p></div>
            </button>
            <div className="flex items-center gap-3 p-4 bg-white border border-slate-200 rounded-xl">
              <QrCode className="w-5 h-5 text-slate-600" />
              <div className="text-left"><p className="text-sm font-semibold text-slate-800">QR Code Giving</p><p className="text-xs text-slate-400">{qrCodes.length} giving links available</p></div>
            </div>
          </div>
        </div>
      )}

      {/* Virtual Terminal Modal */}
      {showVT && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6 space-y-4" data-testid="virtual-terminal-modal">
            <div className="flex items-center justify-between"><h3 className="font-semibold text-slate-800">Virtual Terminal</h3><button onClick={() => setShowVT(false)}><X className="w-4 h-4" /></button></div>
            <p className="text-xs text-slate-500">Process a donation on behalf of a donor (phone, walk-in, mail)</p>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-xs font-medium text-slate-500">DONOR NAME</label><input type="text" value={vtForm.person_name} onChange={e => setVtForm({...vtForm, person_name: e.target.value})} placeholder="John Smith" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" data-testid="vt-name" /></div>
              <div><label className="text-xs font-medium text-slate-500">EMAIL</label><input type="email" value={vtForm.person_email} onChange={e => setVtForm({...vtForm, person_email: e.target.value})} placeholder="john@email.com" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" data-testid="vt-email" /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-xs font-medium text-slate-500">AMOUNT</label><input type="number" step="0.01" value={vtForm.amount} onChange={e => setVtForm({...vtForm, amount: e.target.value})} placeholder="100.00" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" data-testid="vt-amount" /></div>
              <div><label className="text-xs font-medium text-slate-500">FUND</label><select value={vtForm.fund_name} onChange={e => setVtForm({...vtForm, fund_name: e.target.value})} className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"><option>General Fund</option><option>Building Fund</option><option>Missions</option><option>Benevolence</option><option>Youth Ministry</option></select></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-xs font-medium text-slate-500">PAYMENT METHOD</label><select value={vtForm.payment_method} onChange={e => setVtForm({...vtForm, payment_method: e.target.value})} className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"><option value="cash">Cash</option><option value="check">Check</option><option value="card">Card</option></select></div>
              <div><label className="text-xs font-medium text-slate-500">NOTE</label><input type="text" value={vtForm.note} onChange={e => setVtForm({...vtForm, note: e.target.value})} placeholder="Optional note" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" /></div>
            </div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={vtForm.cover_fees} onChange={e => setVtForm({...vtForm, cover_fees: e.target.checked})} className="rounded" />
              <span className="text-sm text-slate-600">Donor covers processing fees (+2.5% + $0.30)</span>
            </label>
            <div className="flex gap-2"><Button onClick={submitVirtualTerminal} disabled={loading} className="flex-1" data-testid="vt-submit">{loading ? 'Processing...' : 'Process Donation'}</Button><Button variant="outline" onClick={() => setShowVT(false)}>Cancel</Button></div>
          </div>
        </div>
      )}

      {/* === TRANSACTIONS TAB === */}
      {activeTab === 'transactions' && (
        <div className="space-y-4" data-testid="solomonpay-transactions-tab">
          <div className="flex flex-wrap gap-3 items-end">
            <div className="flex-1 min-w-[200px]">
              <label className="text-xs text-slate-500">Search</label>
              <div className="relative mt-1"><Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" /><input type="text" value={txSearch} onChange={e => { setTxSearch(e.target.value); setTxPage(1); }} placeholder="Donor name or transaction ID" className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm" data-testid="tx-search" /></div>
            </div>
            <div><label className="text-xs text-slate-500">From</label><input type="date" value={txDateFrom} onChange={e => setTxDateFrom(e.target.value)} className="mt-1 block px-3 py-2 border border-slate-200 rounded-lg text-sm" /></div>
            <div><label className="text-xs text-slate-500">To</label><input type="date" value={txDateTo} onChange={e => setTxDateTo(e.target.value)} className="mt-1 block px-3 py-2 border border-slate-200 rounded-lg text-sm" /></div>
            <Button variant="outline" size="sm" onClick={exportCSV} data-testid="export-transactions"><Download className="w-3.5 h-3.5 mr-1" /> Export CSV</Button>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="bg-slate-50 text-xs text-slate-500 uppercase"><th className="px-4 py-2 text-left">Date</th><th className="px-4 py-2 text-left">Donor</th><th className="px-4 py-2 text-left">Fund</th><th className="px-4 py-2 text-right">Amount</th><th className="px-4 py-2 text-left">Method</th><th className="px-4 py-2 text-left">Status</th><th className="px-4 py-2"></th></tr></thead>
                <tbody>
                  {transactions.data.map((tx, i) => (
                    <tr key={i} className="border-t border-slate-50 hover:bg-slate-50">
                      <td className="px-4 py-2.5 font-mono text-xs">{tx.donation_date}</td>
                      <td className="px-4 py-2.5 font-medium text-slate-700 cursor-pointer hover:text-blue-600" onClick={() => { if (tx.person_id) { openDonorDetail(tx.person_id); setActiveTab('donors'); } }}>{tx.person_name || 'Anonymous'}</td>
                      <td className="px-4 py-2.5 text-slate-500">{tx.fund_name || 'General'}</td>
                      <td className="px-4 py-2.5 text-right font-mono font-semibold">{formatCurrency(tx.amount)}</td>
                      <td className="px-4 py-2.5 capitalize text-slate-500">{tx.payment_method || 'card'}</td>
                      <td className="px-4 py-2.5"><span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${tx.status === 'completed' ? 'bg-green-50 text-green-700' : tx.status === 'refunded' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700'}`}>{tx.status || 'completed'}</span></td>
                      <td className="px-4 py-2.5">{tx.status === 'completed' && tx.amount > 0 && <button onClick={() => refundDonation(tx.id)} className="text-xs text-red-500 hover:underline" data-testid={`refund-${tx.id}`}><RotateCcw className="w-3 h-3 inline mr-0.5" />Refund</button>}</td>
                    </tr>
                  ))}
                  {transactions.data.length === 0 && <tr><td colSpan={6} className="text-center py-8 text-slate-400">No transactions found</td></tr>}
                </tbody>
              </table>
            </div>
            {transactions.total > 50 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100">
                <span className="text-xs text-slate-500">{((txPage-1)*50)+1}–{Math.min(txPage*50, transactions.total)} of {transactions.total}</span>
                <div className="flex gap-1">
                  <button disabled={txPage===1} onClick={() => setTxPage(p=>p-1)} className="px-2 py-1 border border-slate-200 rounded text-xs disabled:opacity-40"><ChevronLeft className="w-3 h-3" /></button>
                  <button disabled={txPage*50 >= transactions.total} onClick={() => setTxPage(p=>p+1)} className="px-2 py-1 border border-slate-200 rounded text-xs disabled:opacity-40"><ChevronRight className="w-3 h-3" /></button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* === PAYOUTS TAB === */}
      {activeTab === 'payouts' && (
        <div className="space-y-4" data-testid="solomonpay-payouts-tab">
          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <p className="text-xs font-medium text-slate-500 uppercase">Available Balance</p>
            <p className="text-3xl font-bold text-slate-900 mt-1">{formatCurrency(payouts.available_balance)}</p>
            <div className="flex gap-3 mt-4">
              <Button onClick={() => requestPayout('instant')} disabled={loading || payouts.available_balance <= 0} className="bg-slate-900 text-white" data-testid="instant-payout-btn">
                <Zap className="w-4 h-4 mr-1" /> Instant Payout (1.5% fee)
              </Button>
              <Button variant="outline" onClick={() => requestPayout('standard')} disabled={loading || payouts.available_balance <= 0} data-testid="standard-payout-btn">
                <Clock className="w-4 h-4 mr-1" /> Standard Payout (Free, 2-3 days)
              </Button>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-100"><h3 className="text-sm font-semibold text-slate-800">Payout History</h3></div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="bg-slate-50 text-xs text-slate-500 uppercase"><th className="px-4 py-2 text-left">Date</th><th className="px-4 py-2 text-right">Amount</th><th className="px-4 py-2 text-right">Fee</th><th className="px-4 py-2 text-right">Net</th><th className="px-4 py-2 text-left">Type</th><th className="px-4 py-2 text-left">Status</th></tr></thead>
                <tbody>
                  {payouts.payouts.map((p, i) => (
                    <tr key={i} className="border-t border-slate-50">
                      <td className="px-4 py-2.5 text-xs">{new Date(p.created_at).toLocaleDateString()}</td>
                      <td className="px-4 py-2.5 text-right font-mono">{formatCurrency(p.amount)}</td>
                      <td className="px-4 py-2.5 text-right text-slate-400 font-mono">{p.fee > 0 ? `-${formatCurrency(p.fee)}` : '$0.00'}</td>
                      <td className="px-4 py-2.5 text-right font-mono font-semibold">{formatCurrency(p.net_amount)}</td>
                      <td className="px-4 py-2.5 capitalize">{p.type}</td>
                      <td className="px-4 py-2.5"><span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${p.status === 'completed' ? 'bg-green-50 text-green-700' : p.status === 'processing' ? 'bg-blue-50 text-blue-700' : 'bg-amber-50 text-amber-700'}`}>{p.status}</span></td>
                    </tr>
                  ))}
                  {payouts.payouts.length === 0 && <tr><td colSpan={6} className="text-center py-8 text-slate-400">No payouts yet</td></tr>}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-slate-800 mb-3">Bank Account</h3>
            <div className="flex items-center gap-4 p-4 border border-dashed border-slate-300 rounded-lg">
              <Building2 className="w-8 h-8 text-slate-400" />
              <div>
                <p className="text-sm font-medium text-slate-700">Connect Bank Account</p>
                <p className="text-xs text-slate-400">Add your bank routing and account number for payouts</p>
              </div>
              <Button variant="outline" size="sm" className="ml-auto">Connect Bank</Button>
            </div>
          </div>
        </div>
      )}

      {/* === FUNDS TAB === */}
      {activeTab === 'funds' && (
        <div className="space-y-4" data-testid="solomonpay-funds-tab">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-800">Fund Management</h3>
            <Button size="sm" onClick={() => { setEditFund(null); setFundForm({ name: '', description: '', goal_amount: '' }); setShowFundModal(true); }} data-testid="create-fund-btn"><Plus className="w-3.5 h-3.5 mr-1" /> Create Fund</Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {funds.filter(f => !f.is_archived).map(f => (
              <div key={f.id} className="bg-white border border-slate-200 rounded-xl p-5" data-testid={`fund-card-${f.id}`}>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-slate-800">{f.name}</h4>
                  <div className="flex gap-1">
                    <button onClick={() => { setEditFund(f); setFundForm({ name: f.name, description: f.description || '', goal_amount: f.goal_amount || '' }); setShowFundModal(true); }} className="p-1 hover:bg-slate-100 rounded"><Pencil className="w-3.5 h-3.5 text-slate-400" /></button>
                    <button onClick={() => archiveFund(f.id)} className="p-1 hover:bg-red-50 rounded"><Archive className="w-3.5 h-3.5 text-slate-400 hover:text-red-500" /></button>
                  </div>
                </div>
                {f.description && <p className="text-xs text-slate-500 mb-3">{f.description}</p>}
                <div className="flex justify-between text-xs text-slate-500 mb-1">
                  <span>{f.donation_count || 0} donations</span>
                  <span className="font-semibold text-slate-800">{formatCurrency(f.total_received || 0)}</span>
                </div>
                {f.goal_amount && (
                  <div className="mt-2">
                    <div className="flex justify-between text-xs text-slate-400 mb-1"><span>Goal</span><span>{formatCurrency(f.goal_amount)}</span></div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden"><div className="h-full bg-slate-800 rounded-full transition-all" style={{ width: `${Math.min(100, ((f.total_received || 0) / f.goal_amount) * 100)}%` }} /></div>
                  </div>
                )}
              </div>
            ))}
          </div>
          {showFundModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
              <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6 space-y-4">
                <div className="flex items-center justify-between"><h3 className="font-semibold">{editFund ? 'Edit' : 'Create'} Fund</h3><button onClick={() => setShowFundModal(false)}><X className="w-4 h-4" /></button></div>
                <div><label className="text-xs font-medium text-slate-500">NAME</label><input type="text" value={fundForm.name} onChange={e => setFundForm({...fundForm, name: e.target.value})} className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" data-testid="fund-name-input" /></div>
                <div><label className="text-xs font-medium text-slate-500">DESCRIPTION</label><textarea value={fundForm.description} onChange={e => setFundForm({...fundForm, description: e.target.value})} className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" rows={2} /></div>
                <div><label className="text-xs font-medium text-slate-500">GOAL AMOUNT (optional)</label><input type="number" value={fundForm.goal_amount} onChange={e => setFundForm({...fundForm, goal_amount: e.target.value})} className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" placeholder="0.00" /></div>
                <div className="flex gap-2"><Button onClick={saveFund} disabled={loading || !fundForm.name} className="flex-1">{loading ? 'Saving...' : 'Save Fund'}</Button><Button variant="outline" onClick={() => setShowFundModal(false)}>Cancel</Button></div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* === RECURRING TAB === */}
      {activeTab === 'recurring' && (
        <div className="space-y-4" data-testid="solomonpay-recurring-tab">
          {/* Scheduler Status */}
          <div className="bg-white border border-slate-200 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold text-slate-900">Recurring Giving Scheduler</h3>
                <p className="text-xs text-slate-500 mt-0.5">Automatically processes due recurring gifts via Solomon Pay</p>
              </div>
              <Button onClick={triggerSchedulerRun} disabled={schedulerRunning} size="sm" className="flex items-center gap-1.5" data-testid="run-scheduler-btn">
                <RefreshCw className={`w-3.5 h-3.5 ${schedulerRunning ? 'animate-spin' : ''}`} />
                {schedulerRunning ? 'Running...' : 'Run Now'}
              </Button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {[
                { label: 'Active Schedules', value: schedulerStatus?.stats?.active_schedules ?? '—' },
                { label: 'Due Today', value: schedulerStatus?.stats?.due_today ?? '—' },
                { label: 'Failed/Retry', value: schedulerStatus?.stats?.failed_retry_queue ?? '—' },
                { label: 'Auto-Paused', value: schedulerStatus?.stats?.auto_paused_count ?? '—' },
                { label: 'Paused Schedules', value: schedulerStatus?.stats?.paused_schedules ?? '—' },
              ].map(s => (
                <div key={s.label} className="bg-slate-50 rounded-lg p-3 text-center">
                  <p className="text-xs text-slate-500">{s.label}</p>
                  <p className="text-xl font-bold text-slate-900 mt-1">{s.value}</p>
                </div>
              ))}
            </div>
            {schedulerStatus?.scheduler?.next_run_estimate && (
              <p className="text-xs text-slate-400 mt-3 flex items-center gap-1">
                <Clock className="w-3 h-3" /> Next scheduled run: {new Date(schedulerStatus.scheduler.next_run_estimate).toLocaleString()}
              </p>
            )}
          </div>

          {/* Failed Retry Queue */}
          {schedulerStatus?.failed_queue?.length > 0 && (
            <div className="bg-white border border-amber-200 rounded-xl p-5">
              <h3 className="font-semibold text-amber-700 mb-3">Failed / Retry Queue ({schedulerStatus.failed_queue.length})</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="text-xs text-slate-500 border-b border-slate-100"><th className="text-left py-2">Schedule ID</th><th className="text-left py-2">Amount</th><th className="text-left py-2">Frequency</th><th className="text-left py-2">Failures</th><th className="text-left py-2">Reason</th><th className="text-left py-2">Next Attempt</th></tr></thead>
                  <tbody>
                    {schedulerStatus.failed_queue.map(r => (
                      <tr key={r.id} className="border-b border-slate-50 hover:bg-amber-50">
                        <td className="py-2 font-mono text-xs">{r.id?.slice(-8)}</td>
                        <td className="py-2">{formatCurrency(r.amount)}</td>
                        <td className="py-2 capitalize">{r.frequency}</td>
                        <td className="py-2 text-amber-600 font-medium">{r.consecutive_failures}</td>
                        <td className="py-2 text-xs text-slate-500 max-w-xs truncate">{r.last_failure_reason}</td>
                        <td className="py-2 font-mono text-xs">{r.next_charge_date}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Auto-Paused */}
          {schedulerStatus?.auto_paused?.length > 0 && (
            <div className="bg-white border border-red-200 rounded-xl p-5">
              <h3 className="font-semibold text-red-700 mb-3">Auto-Paused (3 failures) — {schedulerStatus.auto_paused.length}</h3>
              <div className="space-y-2">
                {schedulerStatus.auto_paused.map(r => (
                  <div key={r.id} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                    <div>
                      <p className="text-sm font-medium text-slate-800">{formatCurrency(r.amount)} — {r.last_failure_reason}</p>
                      <p className="text-xs text-slate-500 font-mono">{r.id}</p>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => resumeSchedule(r.id)} data-testid={`resume-schedule-${r.id}`}>Resume</Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Runs */}
          <div className="bg-white border border-slate-200 rounded-xl p-5">
            <h3 className="font-semibold text-slate-900 mb-3">Recent Batch Runs</h3>
            {(!schedulerStatus?.recent_runs || schedulerStatus.recent_runs.length === 0) ? (
              <p className="text-sm text-slate-400 py-4 text-center">No batch runs yet. Click "Run Now" to trigger the first run.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="text-xs text-slate-500 border-b border-slate-100"><th className="text-left py-2">Run ID</th><th className="text-left py-2">Date</th><th className="text-right py-2">Total</th><th className="text-right py-2">Success</th><th className="text-right py-2">Failed</th><th className="text-right py-2">Skipped</th><th className="text-right py-2">Duration</th></tr></thead>
                  <tbody>
                    {schedulerStatus.recent_runs.map(r => (
                      <tr key={r.id} className="border-b border-slate-50 hover:bg-slate-50">
                        <td className="py-2 font-mono text-xs">{r.id?.slice(-8)}</td>
                        <td className="py-2 text-xs">{new Date(r.started_at).toLocaleString()}</td>
                        <td className="py-2 text-right">{r.total_scheduled}</td>
                        <td className="py-2 text-right text-green-600 font-medium">{r.successful}</td>
                        <td className="py-2 text-right text-red-500 font-medium">{r.failed}</td>
                        <td className="py-2 text-right text-slate-400">{r.skipped}</td>
                        <td className="py-2 text-right text-xs text-slate-400">{r.duration_ms}ms</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Recurring Schedules List */}
          <AdminRecurringGiving />
        </div>
      )}

      {/* === DONORS TAB === */}
      {activeTab === 'donors' && (
        <div className="space-y-4" data-testid="solomonpay-donors-tab">
          {donorDetail ? (
            <div className="space-y-4">
              <button onClick={() => setDonorDetail(null)} className="flex items-center gap-1 text-sm text-blue-600 hover:underline"><ChevronLeft className="w-3 h-3" /> Back to Donors</button>
              <div className="bg-white border border-slate-200 rounded-xl p-6">
                <h3 className="text-lg font-bold text-slate-900">{donorDetail.person?.first_name} {donorDetail.person?.last_name}</h3>
                <p className="text-sm text-slate-500">{donorDetail.person?.email}</p>
                <div className="grid grid-cols-3 gap-4 mt-4">
                  <div><p className="text-xs text-slate-500">Lifetime Total</p><p className="text-xl font-bold text-slate-900">{formatCurrency(donorDetail.lifetime_total)}</p></div>
                  <div><p className="text-xs text-slate-500">Total Gifts</p><p className="text-xl font-bold text-slate-900">{donorDetail.donation_count}</p></div>
                  <div><p className="text-xs text-slate-500">Recurring</p><p className="text-xl font-bold text-slate-900">{donorDetail.recurring?.length > 0 ? `${formatCurrency(donorDetail.recurring[0].amount)}/${donorDetail.recurring[0].frequency}` : 'None'}</p></div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white border border-slate-200 rounded-xl p-5">
                  <h4 className="text-sm font-semibold text-slate-800 mb-3">By Year</h4>
                  {donorDetail.by_year.map(y => <div key={y.year} className="flex justify-between py-1 text-sm"><span className="text-slate-600">{y.year}</span><span className="font-mono font-semibold">{formatCurrency(y.total)}</span></div>)}
                </div>
                <div className="bg-white border border-slate-200 rounded-xl p-5">
                  <h4 className="text-sm font-semibold text-slate-800 mb-3">By Fund</h4>
                  {donorDetail.by_fund.map(f => <div key={f.fund} className="flex justify-between py-1 text-sm"><span className="text-slate-600">{f.fund}</span><span className="font-mono font-semibold">{formatCurrency(f.total)}</span></div>)}
                </div>
              </div>
              <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                <div className="p-4 border-b border-slate-100"><h4 className="text-sm font-semibold text-slate-800">Giving History</h4></div>
                <table className="w-full text-sm"><thead><tr className="bg-slate-50 text-xs text-slate-500 uppercase"><th className="px-4 py-2 text-left">Date</th><th className="px-4 py-2 text-left">Fund</th><th className="px-4 py-2 text-right">Amount</th><th className="px-4 py-2 text-left">Method</th></tr></thead>
                <tbody>{donorDetail.donations.map((d, i) => <tr key={i} className="border-t border-slate-50"><td className="px-4 py-2 text-xs font-mono">{d.donation_date}</td><td className="px-4 py-2 text-slate-500">{d.fund_name || 'General'}</td><td className="px-4 py-2 text-right font-mono font-semibold">{formatCurrency(d.amount)}</td><td className="px-4 py-2 capitalize text-slate-500">{d.payment_method}</td></tr>)}</tbody></table>
              </div>
            </div>
          ) : (
            <>
              <div className="flex gap-3 items-end">
                <div className="flex-1"><div className="relative"><Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" /><input type="text" value={donorSearch} onChange={e => { setDonorSearch(e.target.value); setDonorPage(1); }} placeholder="Search donors..." className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm" data-testid="donor-search" /></div></div>
                <span className="text-xs text-slate-500">{donors.total} donors</span>
              </div>
              <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead><tr className="bg-slate-50 text-xs text-slate-500 uppercase"><th className="px-4 py-2 text-left">Donor</th><th className="px-4 py-2 text-right">Lifetime</th><th className="px-4 py-2 text-right">Gifts</th><th className="px-4 py-2 text-left">First Gift</th><th className="px-4 py-2 text-left">Last Gift</th><th className="px-4 py-2 text-left">Recurring</th><th className="px-4 py-2"></th></tr></thead>
                  <tbody>
                    {donors.donors.map((d, i) => (
                      <tr key={i} className="border-t border-slate-50 hover:bg-slate-50">
                        <td className="px-4 py-2.5 font-medium text-slate-700">{d.name || 'Anonymous'}</td>
                        <td className="px-4 py-2.5 text-right font-mono font-semibold">{formatCurrency(d.lifetime_total)}</td>
                        <td className="px-4 py-2.5 text-right text-slate-500">{d.donation_count}</td>
                        <td className="px-4 py-2.5 text-xs text-slate-400">{d.first_gift}</td>
                        <td className="px-4 py-2.5 text-xs text-slate-400">{d.last_gift}</td>
                        <td className="px-4 py-2.5">{d.recurring ? <span className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded-full">{formatCurrency(d.recurring.amount)}/{d.recurring.frequency}</span> : <span className="text-xs text-slate-300">—</span>}</td>
                        <td className="px-4 py-2.5"><button onClick={() => openDonorDetail(d.person_id)} className="text-xs text-blue-600 hover:underline" data-testid={`view-donor-${d.person_id}`}><Eye className="w-3.5 h-3.5" /></button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {donors.total > 50 && (
                  <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100">
                    <span className="text-xs text-slate-500">Page {donorPage}</span>
                    <div className="flex gap-1">
                      <button disabled={donorPage===1} onClick={() => setDonorPage(p=>p-1)} className="px-2 py-1 border border-slate-200 rounded text-xs disabled:opacity-40"><ChevronLeft className="w-3 h-3" /></button>
                      <button disabled={donorPage*50>=donors.total} onClick={() => setDonorPage(p=>p+1)} className="px-2 py-1 border border-slate-200 rounded text-xs disabled:opacity-40"><ChevronRight className="w-3 h-3" /></button>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}

      {/* === STATEMENTS TAB === */}
      {activeTab === 'statements' && (
        <div className="space-y-4" data-testid="solomonpay-statements-tab">
          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-slate-800 mb-4">Year-End Statement Generation</h3>
            <div className="flex items-end gap-4">
              <div>
                <label className="text-xs font-medium text-slate-500">YEAR</label>
                <select value={stmtYear} onChange={e => setStmtYear(parseInt(e.target.value))} className="mt-1 block px-3 py-2 border border-slate-200 rounded-lg text-sm" data-testid="stmt-year-select">
                  {[2027, 2026, 2025, 2024].map(y => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
              <Button onClick={generateStatements} disabled={loading} data-testid="generate-statements-btn">
                <FileText className="w-4 h-4 mr-1" /> {loading ? 'Generating...' : 'Generate All Statements'}
              </Button>
            </div>
          </div>

          {stmtResult && (
            <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center"><FileText className="w-5 h-5 text-green-600" /></div>
                <div>
                  <p className="font-semibold text-slate-800">{stmtResult.job?.donor_count} statements generated for {stmtResult.job?.year}</p>
                  <p className="text-sm text-slate-500">Total: {formatCurrency(stmtResult.job?.total_amount)}</p>
                </div>
              </div>
              <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead><tr className="bg-slate-50 text-xs text-slate-500 uppercase"><th className="px-4 py-2 text-left">Donor</th><th className="px-4 py-2 text-right">Total</th><th className="px-4 py-2 text-right">Gifts</th></tr></thead>
                  <tbody>
                    {(stmtResult.donors || []).slice(0, 30).map((d, i) => (
                      <tr key={i} className="border-t border-slate-50"><td className="px-4 py-2">{d.name || 'Anonymous'}</td><td className="px-4 py-2 text-right font-mono font-semibold">{formatCurrency(d.total)}</td><td className="px-4 py-2 text-right text-slate-500">{d.count}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex gap-3">
                <Button variant="outline" disabled><Download className="w-4 h-4 mr-1" /> Download All as ZIP (Coming Soon)</Button>
                <Button variant="outline" disabled>Bulk Email to Donors (Coming Soon)</Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* === SETTINGS TAB === */}
      {activeTab === 'settings' && settings && (
        <div className="space-y-4" data-testid="solomonpay-settings-tab">
          <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-5">
            <h3 className="text-sm font-semibold text-slate-800">SolomonPay Configuration</h3>
            <div>
              <label className="text-xs font-medium text-slate-500">PAYOUT SCHEDULE</label>
              <select value={settings.payout_schedule} onChange={e => setSettings({...settings, payout_schedule: e.target.value})} className="mt-1 block w-full px-3 py-2 border border-slate-200 rounded-lg text-sm" data-testid="payout-schedule">
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
            <div className="flex items-center justify-between py-3 border-t border-slate-100">
              <div><p className="text-sm font-medium">Show Processing Fees</p><p className="text-xs text-slate-400">Display transaction fees to donors</p></div>
              <div className={`w-10 h-5 rounded-full transition-colors relative cursor-pointer ${settings.show_processing_fees ? 'bg-slate-900' : 'bg-slate-200'}`} onClick={() => setSettings({...settings, show_processing_fees: !settings.show_processing_fees})}>
                <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${settings.show_processing_fees ? 'translate-x-5' : 'translate-x-0.5'}`} />
              </div>
            </div>
            <div className="flex items-center justify-between py-3 border-t border-slate-100">
              <div><p className="text-sm font-medium">Giving Receipt Emails</p><p className="text-xs text-slate-400">Auto-send receipt after each donation</p></div>
              <div className={`w-10 h-5 rounded-full transition-colors relative cursor-pointer ${settings.receipt_email_enabled ? 'bg-slate-900' : 'bg-slate-200'}`} onClick={() => setSettings({...settings, receipt_email_enabled: !settings.receipt_email_enabled})}>
                <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${settings.receipt_email_enabled ? 'translate-x-5' : 'translate-x-0.5'}`} />
              </div>
            </div>
            <div className="pt-3 border-t border-slate-100">
              <h4 className="text-sm font-medium mb-3">Bank Account</h4>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="text-xs text-slate-500">Routing Number</label><input type="text" placeholder="•••••••••" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" disabled /></div>
                <div><label className="text-xs text-slate-500">Account Number</label><input type="text" placeholder="•••••••••" className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm" disabled /></div>
              </div>
              <p className="text-xs text-slate-400 mt-2">Bank connections are managed through SolomonPay's secure portal. Contact support for changes.</p>
            </div>
            <Button onClick={saveSettings} disabled={loading} className="w-full">{loading ? 'Saving...' : 'Save Settings'}</Button>
          </div>
        </div>
      )}
    </div>
  );
}
