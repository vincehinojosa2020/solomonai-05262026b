import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { 
  DollarSign, Plus, TrendingUp, RefreshCw, CreditCard, 
  Banknote, Building2, FileText, Bitcoin, ChevronLeft, ChevronRight
} from 'lucide-react';
import { 
  PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer
} from 'recharts';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { API_URL, formatCurrency, formatDate } from '@/lib/utils';
import EnterDonationPanel from '@/components/modals/EnterDonationPanel';

const StatCard = ({ title, value, subtitle, icon: Icon }) => (
  <div className="stat-card">
    <div className="flex items-start justify-between">
      <div>
        <p className="stat-label">{title}</p>
        <p className="stat-value mt-1">{value}</p>
        {subtitle && <p className="text-xs text-[#8a8a8a] mt-1">{subtitle}</p>}
      </div>
      <div className="p-2 bg-[#f7f7f5] rounded">
        <Icon className="w-4 h-4 text-[#8a8a8a]" />
      </div>
    </div>
  </div>
);

const PAYMENT_COLORS = {
  card: '#2d7a6b',
  check: '#3b82f6',
  cash: '#8b5cf6',
  ach: '#f59e0b',
  crypto: '#ec4899',
  online: '#06b6d4',
};

export default function GivingDashboard() {
  const [searchParams] = useSearchParams();
  const [stats, setStats] = useState(null);
  const [donations, setDonations] = useState([]);
  const [funds, setFunds] = useState([]);
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDonationPanel, setShowDonationPanel] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const perPage = 20;

  useEffect(() => {
    if (searchParams.get('action') === 'add') {
      setShowDonationPanel(true);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchGivingData();
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
      <div className="animate-fade-in space-y-6">
        <div className="h-8 bg-[#e8e8e5] rounded w-64"></div>
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 bg-[#e8e8e5] rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="giving-dashboard">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Stewardship</h1>
          <p className="page-subtitle">Track and manage generosity</p>
        </div>
        <Button className="btn-primary" onClick={() => setShowDonationPanel(true)} data-testid="enter-donation-btn">
          <Plus className="w-4 h-4 mr-2" />
          Record Gift
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="MTD Giving"
          value={formatCurrency(stats?.mtd_total || 0)}
          subtitle={`${stats?.mtd_count || 0} gifts`}
          icon={DollarSign}
        />
        <StatCard
          title="YTD Giving"
          value={formatCurrency(stats?.ytd_total || 0)}
          subtitle={`${stats?.ytd_count || 0} gifts`}
          icon={TrendingUp}
        />
        <StatCard
          title="Recurring Partners"
          value={stats?.active_recurring || 0}
          subtitle="Active schedules"
          icon={RefreshCw}
        />
        <StatCard
          title="Open Batches"
          value={stats?.undeposited_batches || 0}
          subtitle="Pending deposit"
          icon={FileText}
        />
      </div>

      {/* Stewardship Options - Enterprise */}
      <div className="stewardship-section" data-testid="stewardship-section">
        <div className="stewardship-header">
          <div>
            <h3 className="stewardship-title">Partner With Us</h3>
            <p className="stewardship-subtitle">Multiple ways to support the mission</p>
          </div>
        </div>
        <div className="stewardship-grid">
          <a href="#" onClick={(e) => { e.preventDefault(); setShowDonationPanel(true); }} className="stewardship-card" data-testid="give-card">
            <div className="icon-wrap stripe"><CreditCard /></div>
            <span className="label">Card / ACH</span>
            <span className="status">Available</span>
          </a>
          <a href="https://paypal.me/placeholder" target="_blank" rel="noopener noreferrer" className="stewardship-card" data-testid="give-paypal">
            <div className="icon-wrap paypal">
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5"><path d="M7.076 21.337H2.47a.641.641 0 0 1-.633-.74L4.944.901C5.026.382 5.474 0 5.998 0h7.46c2.57 0 4.578.543 5.69 1.81 1.01 1.15 1.304 2.42 1.012 4.287-.023.143-.047.288-.077.437-.983 5.05-4.349 6.797-8.647 6.797h-2.19c-.524 0-.968.382-1.05.9l-1.12 7.106zm14.146-14.42a3.35 3.35 0 0 0-.607-.541c-.013.076-.026.175-.041.254-.93 4.778-4.005 7.201-9.138 7.201h-2.19a.563.563 0 0 0-.556.479l-1.187 7.527h-.506l-.24 1.516a.56.56 0 0 0 .554.647h3.882c.46 0 .85-.334.922-.788.06-.26.76-4.852.816-5.09a.932.932 0 0 1 .923-.788h.58c3.76 0 6.705-1.528 7.565-5.946.36-1.847.174-3.388-.777-4.471z"/></svg>
            </div>
            <span className="label">PayPal</span>
            <span className="status coming-soon">Coming Soon</span>
          </a>
          <a href="https://venmo.com/placeholder" target="_blank" rel="noopener noreferrer" className="stewardship-card" data-testid="give-venmo">
            <div className="icon-wrap venmo">
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5"><path d="M19.615 1.498c.979 1.609 1.42 3.267 1.42 5.37 0 6.694-5.715 15.384-10.353 21.132H3.528L.001 3.39l6.968-.648 1.986 15.94c1.85-3.017 4.138-7.765 4.138-11.006 0-2.002-.344-3.363-1.036-4.467l6.558-1.711z"/></svg>
            </div>
            <span className="label">Venmo</span>
            <span className="status coming-soon">Coming Soon</span>
          </a>
          <a href="#" className="stewardship-card" data-testid="give-zelle">
            <div className="icon-wrap zelle">
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5"><path d="M13.559 24h-2.79a.483.483 0 0 1-.483-.483v-3.276H2.49A2.49 2.49 0 0 1 0 17.752V6.248A2.49 2.49 0 0 1 2.49 3.76h7.797V.483c0-.267.216-.483.483-.483h2.79c.266 0 .482.216.482.483v3.276h7.47A2.49 2.49 0 0 1 24 6.248v11.504a2.49 2.49 0 0 1-2.49 2.49h-7.469v3.276a.483.483 0 0 1-.482.482zm.483-7.76h6.228V7.76H8.41l5.632 8.48zm-9.766 0h3.22l-3.22-4.848v4.849zm15.448-8.48H5.73L11.31 7.76h8.414z"/></svg>
            </div>
            <span className="label">Zelle</span>
            <span className="status coming-soon">Coming Soon</span>
          </a>
          <a href="#" className="stewardship-card" data-testid="give-crypto">
            <div className="icon-wrap crypto"><Bitcoin /></div>
            <span className="label">Crypto</span>
            <span className="status coming-soon">Coming Soon</span>
          </a>
          <a href="#" className="stewardship-card" data-testid="give-bank">
            <div className="icon-wrap bank"><Building2 /></div>
            <span className="label">Bank Transfer</span>
            <span className="status coming-soon">Contact Us</span>
          </a>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Giving by Method */}
        <div className="bento-card">
          <h3 className="card-title mb-4">Giving by Method (YTD)</h3>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={methodData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={85}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {methodData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={PAYMENT_COLORS[entry.name.toLowerCase()] || '#8a8a8a'} 
                    />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value) => formatCurrency(value)}
                  contentStyle={{ 
                    backgroundColor: 'white', 
                    border: '1px solid #e8e8e5',
                    borderRadius: '6px',
                    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Funds Overview */}
        <div className="bento-card">
          <h3 className="card-title mb-4">Fund Progress</h3>
          <div className="space-y-4">
            {funds.slice(0, 5).map((fund) => {
              const progress = fund.goal_amount 
                ? Math.min(100, (fund.current_amount / fund.goal_amount) * 100)
                : 0;
              return (
                <div key={fund.id}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-sm font-medium text-[#1a1a1a]">{fund.name}</span>
                    <span className="text-sm text-[#8a8a8a] font-data">
                      {formatCurrency(fund.current_amount)} 
                      {fund.goal_amount && ` / ${formatCurrency(fund.goal_amount)}`}
                    </span>
                  </div>
                  {fund.goal_amount && (
                    <div className="progress-bar">
                      <div 
                        className="progress-bar-fill"
                        style={{ width: `${progress}%` }}
                      ></div>
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
          <Link to="/reports?type=giving" className="card-action">
            View reports →
          </Link>
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
                  <td colSpan={6} className="text-center py-8 text-[#8a8a8a]">
                    No gifts recorded
                  </td>
                </tr>
              ) : (
                donations.map((donation) => (
                  <tr key={donation.id}>
                    <td className="font-data text-sm">{formatDate(donation.donation_date)}</td>
                    <td>
                      {donation.donor_name ? (
                        <div className="flex items-center gap-2">
                          <Avatar className="w-6 h-6">
                            <AvatarImage src={donation.donor_photo} />
                            <AvatarFallback className="text-xs bg-[#2d7a6b] text-white">
                              {donation.donor_name.split(' ').map(n => n[0]).join('')}
                            </AvatarFallback>
                          </Avatar>
                          <span className="font-medium text-[#1a1a1a]">{donation.donor_name}</span>
                        </div>
                      ) : (
                        <span className="text-[#8a8a8a]">Anonymous</span>
                      )}
                    </td>
                    <td className="text-[#4a4a4a]">{donation.fund_name || 'General Fund'}</td>
                    <td className="text-right font-data font-semibold text-[#1a1a1a]">
                      {formatCurrency(donation.amount)}
                    </td>
                    <td>
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-[#f7f7f5] text-[#4a4a4a]">
                        {donation.payment_method === 'card' && <CreditCard className="w-3 h-3" />}
                        {donation.payment_method === 'check' && <FileText className="w-3 h-3" />}
                        {donation.payment_method === 'cash' && <Banknote className="w-3 h-3" />}
                        {donation.payment_method === 'ach' && <Building2 className="w-3 h-3" />}
                        {donation.payment_method === 'crypto' && <Bitcoin className="w-3 h-3" />}
                        {donation.payment_method.charAt(0).toUpperCase() + donation.payment_method.slice(1)}
                      </span>
                    </td>
                    <td className="text-[#8a8a8a] text-sm">{donation.notes || '—'}</td>
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
              Showing {((page - 1) * perPage) + 1}–{Math.min(page * perPage, total)} of {total.toLocaleString()} gifts
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

      {/* Batches Section */}
      <div className="data-table-container">
        <div className="data-table-header">
          <h3 className="card-title">Gift Batches</h3>
          <Button variant="outline" size="sm" className="btn-secondary text-sm h-8">Create Batch</Button>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Batch Name</th>
                <th>Date</th>
                <th>Status</th>
                <th className="text-right">Total</th>
                <th className="text-right">Count</th>
              </tr>
            </thead>
            <tbody>
              {batches.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-[#8a8a8a]">
                    No batches created
                  </td>
                </tr>
              ) : (
                batches.map((batch) => (
                  <tr key={batch.id} className="cursor-pointer">
                    <td className="font-medium text-[#1a1a1a]">{batch.name}</td>
                    <td className="font-data text-sm">{formatDate(batch.date)}</td>
                    <td>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        batch.status === 'open' ? 'bg-[#e8f4f1] text-[#2d7a6b]' :
                        batch.status === 'closed' ? 'bg-[#fef3cd] text-[#856404]' :
                        'bg-[#f0f0f0] text-[#6b7280]'
                      }`}>
                        {batch.status.charAt(0).toUpperCase() + batch.status.slice(1)}
                      </span>
                    </td>
                    <td className="text-right font-data font-semibold">
                      {formatCurrency(batch.total_amount)}
                    </td>
                    <td className="text-right font-data">{batch.donation_count}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
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
    </div>
  );
}
