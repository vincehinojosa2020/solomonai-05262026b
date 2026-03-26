import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { 
  DollarSign, Plus, TrendingUp, RefreshCw, CreditCard, 
  Banknote, Building2, FileText, Bitcoin, ChevronLeft, ChevronRight,
  Link2, Unlink, CheckCircle2, Circle, Loader2, Settings2, Zap
} from 'lucide-react';
import { 
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer
} from 'recharts';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { API_URL, formatCurrency, formatDate } from '@/lib/utils';
import EnterDonationPanel from '@/components/modals/EnterDonationPanel';
import DonationCheckout from '@/components/modals/DonationCheckout';
import { toast } from 'sonner';

const StatCard = ({ title, value, subtitle, icon: Icon }) => (
  <div className="stat-card">
    <div className="flex items-start justify-between">
      <div>
        <p className="stat-label">{title}</p>
        <p className="stat-value">{value}</p>
        {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
      </div>
      <div className="p-2 bg-slate-100">
        <Icon className="w-4 h-4 text-slate-500" />
      </div>
    </div>
  </div>
);

const PAYMENT_COLORS = {
  card: '#3b82f6',
  check: '#64748b',
  cash: '#94a3b8',
  ach: '#475569',
  crypto: '#f59e0b',
};

export default function GivingDashboard() {
  const [searchParams] = useSearchParams();
  const [stats, setStats] = useState(null);
  const [donations, setDonations] = useState([]);
  const [funds, setFunds] = useState([]);
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDonationPanel, setShowDonationPanel] = useState(false);
  const [showStripeCheckout, setShowStripeCheckout] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [integrations, setIntegrations] = useState(null);
  const [connectingProcessor, setConnectingProcessor] = useState(null);
  const perPage = 20;

  useEffect(() => {
    if (searchParams.get('action') === 'add') {
      setShowDonationPanel(true);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchGivingData();
    fetchIntegrations();
  }, [page]);

  const fetchGivingData = async () => {
    setLoading(true);
    try {
      const [statsRes, donationsRes, fundsRes, batchesRes] = await Promise.all([
        fetch(`${API_URL}/giving/stats`),
        fetch(`${API_URL}/donations?page=${page}&per_page=${perPage}`),
        fetch(`${API_URL}/funds`),
        fetch(`${API_URL}/batches`),
      ]);

      const [statsData, donationsData, fundsData, batchesData] = await Promise.all([
        statsRes.json(),
        donationsRes.json(),
        fundsRes.json(),
        batchesRes.json(),
      ]);

      setStats(statsData);
      setDonations(donationsData.data);
      setTotal(donationsData.total);
      setFunds(fundsData);
      setBatches(batchesData);
    } catch (error) {
      console.error('Failed to fetch giving data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDonationAdded = () => {
    setShowDonationPanel(false);
    fetchGivingData();
  };

  const fetchIntegrations = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/giving/integrations`);
      if (res.ok) {
        const data = await res.json();
        setIntegrations(data);
      }
    } catch (err) {
      console.error('Failed to fetch giving integrations:', err);
    }
  };

  const handleConnectProcessor = async (processor) => {
    setConnectingProcessor(processor);
    try {
      const res = await fetch(`${API_URL}/admin/giving/integrations/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ processor }),
      });
      if (res.ok) {
        toast.success(`${processor.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} connected successfully`);
        await fetchIntegrations();
      }
    } catch (err) {
      toast.error('Failed to connect processor');
    } finally {
      setConnectingProcessor(null);
    }
  };

  const handleDisconnectProcessor = async (processor) => {
    setConnectingProcessor(processor);
    try {
      const res = await fetch(`${API_URL}/admin/giving/integrations/disconnect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ processor }),
      });
      if (res.ok) {
        toast.success('Processor disconnected');
        await fetchIntegrations();
      }
    } catch (err) {
      toast.error('Failed to disconnect');
    } finally {
      setConnectingProcessor(null);
    }
  };

  const methodData = stats?.by_method 
    ? Object.entries(stats.by_method).map(([method, data]) => ({
        name: method.charAt(0).toUpperCase() + method.slice(1),
        value: data.total,
        count: data.count,
      }))
    : [];

  const totalPages = Math.ceil(total / perPage);

  if (loading && !stats) {
    return (
      <div className="space-y-4">
        <div className="h-6 bg-slate-200 w-48"></div>
        <div className="grid grid-cols-4 gap-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 bg-slate-200"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="giving-dashboard">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Stewardship</h1>
          <p className="page-subtitle">Manage giving and financial operations</p>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            onClick={() => window.open(`${API_URL}/admin/giving/export`, '_blank')}
            data-testid="export-csv-btn"
          >
            <FileText className="w-4 h-4 mr-1" />
            Export CSV
          </Button>
          <Button className="btn-primary" onClick={() => setShowDonationPanel(true)} data-testid="enter-donation-btn">
            <Plus className="w-4 h-4 mr-1" />
            Record Gift
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard
          title="MTD GIVING"
          value={formatCurrency(stats?.mtd_total || 0)}
          subtitle={`${stats?.mtd_count || 0} gifts`}
          icon={DollarSign}
        />
        <StatCard
          title="YTD GIVING"
          value={formatCurrency(stats?.ytd_total || 0)}
          subtitle={`${stats?.ytd_count || 0} gifts`}
          icon={TrendingUp}
        />
        <StatCard
          title="RECURRING"
          value={stats?.active_recurring || 0}
          subtitle="Active schedules"
          icon={RefreshCw}
        />
        <StatCard
          title="OPEN BATCHES"
          value={stats?.undeposited_batches || 0}
          subtitle="Pending deposit"
          icon={FileText}
        />
      </div>

      {/* Giving Platform Integrations */}
      <div className="bento-card" data-testid="giving-integrations-section">
        <div className="card-header" style={{ marginBottom: '16px' }}>
          <div className="flex items-center gap-2">
            <Settings2 className="w-4 h-4 text-slate-500" />
            <h3 className="card-title">Giving Platform</h3>
          </div>
          <span className="text-xs text-slate-400">
            {integrations?.active_processor 
              ? <span className="flex items-center gap-1"><CheckCircle2 className="w-3 h-3 text-emerald-500" /> Connected</span>
              : <span className="flex items-center gap-1"><Circle className="w-3 h-3 text-slate-300" /> No processor active</span>
            }
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {integrations && Object.entries(integrations.processors || {}).map(([key, proc]) => {
            const isActive = integrations.active_processor === key;
            const isConnecting = connectingProcessor === key;
            return (
              <div
                key={key}
                className="relative rounded-lg border p-4 transition-all"
                style={{
                  borderColor: isActive ? '#10b981' : '#e2e8f0',
                  background: isActive ? '#f0fdf4' : '#fafafa',
                }}
                data-testid={`processor-${key}`}
              >
                {isActive && (
                  <div className="absolute -top-2 -right-2 bg-emerald-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
                    ACTIVE
                  </div>
                )}
                <div className="flex items-center gap-2 mb-2">
                  {key === 'solomon_pay' && <Zap className="w-4 h-4 text-blue-600" />}
                  {key === 'pushpay' && <CreditCard className="w-4 h-4 text-green-600" />}
                  {key === 'securegive' && <Building2 className="w-4 h-4 text-purple-600" />}
                  <span className="font-semibold text-sm text-slate-800">{proc.label || key}</span>
                </div>
                <p className="text-xs text-slate-500 mb-3 leading-relaxed">{proc.description}</p>
                {isActive ? (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full text-xs"
                    onClick={() => handleDisconnectProcessor(key)}
                    disabled={isConnecting}
                    data-testid={`disconnect-${key}`}
                  >
                    {isConnecting ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Unlink className="w-3 h-3 mr-1" />}
                    Disconnect
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    className="w-full text-xs"
                    onClick={() => handleConnectProcessor(key)}
                    disabled={isConnecting}
                    data-testid={`connect-${key}`}
                  >
                    {isConnecting ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Link2 className="w-3 h-3 mr-1" />}
                    Connect
                  </Button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Giving Options */}
      <div className="giving-section" data-testid="giving-section">
        <div className="giving-section-header">
          <h3 className="giving-section-title">Payment Channels</h3>
        </div>
        <div className="giving-grid">
          <a href="#" onClick={(e) => { e.preventDefault(); setShowStripeCheckout(true); }} className="giving-card" data-testid="give-card">
            <div className="icon-box stripe"><CreditCard /></div>
            <span className="label">Card / ACH</span>
            <span className="status">Active</span>
          </a>
          <a href="https://paypal.me/placeholder" target="_blank" rel="noopener noreferrer" className="giving-card" data-testid="give-paypal">
            <div className="icon-box paypal">
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4"><path d="M7.076 21.337H2.47a.641.641 0 0 1-.633-.74L4.944.901C5.026.382 5.474 0 5.998 0h7.46c2.57 0 4.578.543 5.69 1.81 1.01 1.15 1.304 2.42 1.012 4.287-.023.143-.047.288-.077.437-.983 5.05-4.349 6.797-8.647 6.797h-2.19c-.524 0-.968.382-1.05.9l-1.12 7.106zm14.146-14.42a3.35 3.35 0 0 0-.607-.541c-.013.076-.026.175-.041.254-.93 4.778-4.005 7.201-9.138 7.201h-2.19a.563.563 0 0 0-.556.479l-1.187 7.527h-.506l-.24 1.516a.56.56 0 0 0 .554.647h3.882c.46 0 .85-.334.922-.788.06-.26.76-4.852.816-5.09a.932.932 0 0 1 .923-.788h.58c3.76 0 6.705-1.528 7.565-5.946.36-1.847.174-3.388-.777-4.471z"/></svg>
            </div>
            <span className="label">PayPal</span>
            <span className="status pending">Pending</span>
          </a>
          <a href="https://venmo.com/placeholder" target="_blank" rel="noopener noreferrer" className="giving-card" data-testid="give-venmo">
            <div className="icon-box venmo">
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4"><path d="M19.615 1.498c.979 1.609 1.42 3.267 1.42 5.37 0 6.694-5.715 15.384-10.353 21.132H3.528L.001 3.39l6.968-.648 1.986 15.94c1.85-3.017 4.138-7.765 4.138-11.006 0-2.002-.344-3.363-1.036-4.467l6.558-1.711z"/></svg>
            </div>
            <span className="label">Venmo</span>
            <span className="status pending">Pending</span>
          </a>
          <a href="#" className="giving-card" data-testid="give-zelle">
            <div className="icon-box zelle">
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4"><path d="M13.559 24h-2.79a.483.483 0 0 1-.483-.483v-3.276H2.49A2.49 2.49 0 0 1 0 17.752V6.248A2.49 2.49 0 0 1 2.49 3.76h7.797V.483c0-.267.216-.483.483-.483h2.79c.266 0 .482.216.482.483v3.276h7.47A2.49 2.49 0 0 1 24 6.248v11.504a2.49 2.49 0 0 1-2.49 2.49h-7.469v3.276a.483.483 0 0 1-.482.482zm.483-7.76h6.228V7.76H8.41l5.632 8.48zm-9.766 0h3.22l-3.22-4.848v4.849zm15.448-8.48H5.73L11.31 7.76h8.414z"/></svg>
            </div>
            <span className="label">Zelle</span>
            <span className="status pending">Pending</span>
          </a>
          <a href="#" className="giving-card" data-testid="give-crypto">
            <div className="icon-box crypto"><Bitcoin /></div>
            <span className="label">Crypto</span>
            <span className="status pending">Pending</span>
          </a>
          <a href="#" className="giving-card" data-testid="give-bank">
            <div className="icon-box bank"><Building2 /></div>
            <span className="label">Wire Transfer</span>
            <span className="status pending">Contact</span>
          </a>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* Giving by Method */}
        <div className="bento-card">
          <div className="card-header">
            <h3 className="card-title">Giving by Method (YTD)</h3>
          </div>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={methodData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={70}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {methodData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={PAYMENT_COLORS[entry.name.toLowerCase()] || '#94a3b8'} 
                    />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value) => formatCurrency(value)}
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '1px solid #e2e8f0',
                    fontSize: '12px'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Funds Overview */}
        <div className="bento-card">
          <div className="card-header">
            <h3 className="card-title">Fund Progress</h3>
          </div>
          <div className="space-y-3">
            {funds.slice(0, 5).map((fund) => {
              const progress = fund.goal_amount 
                ? Math.min(100, (fund.current_amount / fund.goal_amount) * 100)
                : 0;
              return (
                <div key={fund.id}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-slate-700">{fund.name}</span>
                    <span className="text-xs text-slate-500 font-mono">
                      {formatCurrency(fund.current_amount)} 
                      {fund.goal_amount && ` / ${formatCurrency(fund.goal_amount)}`}
                    </span>
                  </div>
                  {fund.goal_amount && (
                    <div className="progress-bar">
                      <div className="progress-bar-fill" style={{ width: `${progress}%` }}></div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Recent Donations Table */}
      <div className="data-table-container">
        <div className="data-table-header">
          <h3 className="card-title">Recent Gifts</h3>
          <Link to="/reports?type=giving" className="card-action">View reports →</Link>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Donor</th>
                <th>Fund</th>
                <th className="text-right">Amount</th>
                <th>Method</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {donations.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-6 text-slate-400 text-xs">
                    No gifts recorded
                  </td>
                </tr>
              ) : (
                donations.map((donation) => (
                  <tr key={donation.id}>
                    <td className="font-mono text-xs">{formatDate(donation.donation_date)}</td>
                    <td>
                      {donation.donor_name ? (
                        <div className="flex items-center gap-2">
                          <Avatar className="w-5 h-5">
                            <AvatarImage src={donation.donor_photo} />
                            <AvatarFallback className="text-xs bg-blue-600 text-white">
                              {donation.donor_name.split(' ').map(n => n[0]).join('')}
                            </AvatarFallback>
                          </Avatar>
                          <span className="font-medium text-slate-700">{donation.donor_name}</span>
                        </div>
                      ) : (
                        <span className="text-slate-400">Anonymous</span>
                      )}
                    </td>
                    <td className="text-slate-600">{donation.fund_name || 'General Fund'}</td>
                    <td className="text-right font-mono font-semibold text-slate-900">
                      {formatCurrency(donation.amount)}
                    </td>
                    <td>
                      <span className="badge badge-inactive">
                        {donation.payment_method.charAt(0).toUpperCase() + donation.payment_method.slice(1)}
                      </span>
                    </td>
                    <td className="text-slate-400 text-xs">{donation.notes || '—'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {total > perPage && (
          <div className="pagination">
            <div className="pagination-info">
              {((page - 1) * perPage) + 1}–{Math.min(page * perPage, total)} of {total.toLocaleString()}
            </div>
            <div className="pagination-controls">
              <button
                className="pagination-btn"
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              {[...Array(Math.min(5, totalPages))].map((_, i) => {
                const pageNum = i + 1;
                return (
                  <button
                    key={pageNum}
                    className={`pagination-btn ${page === pageNum ? 'active' : ''}`}
                    onClick={() => setPage(pageNum)}
                  >
                    {pageNum}
                  </button>
                );
              })}
              <button
                className="pagination-btn"
                disabled={page === totalPages}
                onClick={() => setPage(p => p + 1)}
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Enter Donation Panel */}
      {showDonationPanel && (
        <EnterDonationPanel 
          onClose={() => setShowDonationPanel(false)}
          onSuccess={handleDonationAdded}
          funds={funds}
          batches={batches.filter(b => b.status === 'open')}
        />
      )}

      {/* Stripe Checkout */}
      {showStripeCheckout && (
        <DonationCheckout 
          onClose={() => setShowStripeCheckout(false)}
        />
      )}
    </div>
  );
}
