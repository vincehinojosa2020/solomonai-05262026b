import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { 
  DollarSign, Plus, TrendingUp, RefreshCw, CreditCard, 
  Banknote, Building2, Check, FileText, Bitcoin, Search,
  ChevronLeft, ChevronRight
} from 'lucide-react';
import { 
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { API_URL, formatCurrency, formatDate, getInitials } from '@/lib/utils';
import EnterDonationPanel from '@/components/modals/EnterDonationPanel';

const StatCard = ({ title, value, subtitle, icon: Icon, highlight }) => (
  <div className={`bg-white border border-slate-200 rounded-lg p-5 ${highlight ? 'border-l-4 border-l-emerald-500' : ''}`}>
    <div className="flex items-start justify-between">
      <div>
        <p className="text-xs text-slate-400 mb-1">{title}</p>
        <p className="text-2xl font-bold font-data text-slate-900">{value}</p>
        {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
      </div>
      <div className="p-2 bg-slate-100 rounded-lg">
        <Icon className="w-5 h-5 text-slate-400" />
      </div>
    </div>
  </div>
);

const PAYMENT_COLORS = {
  card: '#4f6ef7',
  check: '#f5a623',
  cash: '#00c896',
  ach: '#8b5cf6',
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

  // Prepare chart data
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
      <div className="animate-pulse space-y-6">
        <div className="h-8 bg-slate-200 rounded w-64"></div>
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-slate-200 rounded-lg"></div>
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
          <h1 className="page-title">Giving</h1>
          <p className="page-subtitle">Track and manage donations</p>
        </div>
        <Button className="h-9 btn-primary" onClick={() => setShowDonationPanel(true)} data-testid="enter-donation-btn">
          <Plus className="w-4 h-4 mr-2" />
          Enter Donation
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="MTD Giving"
          value={formatCurrency(stats?.mtd_total || 0)}
          subtitle={`${stats?.mtd_count || 0} donations`}
          icon={DollarSign}
          highlight={true}
        />
        <StatCard
          title="YTD Giving"
          value={formatCurrency(stats?.ytd_total || 0)}
          subtitle={`${stats?.ytd_count || 0} donations`}
          icon={TrendingUp}
        />
        <StatCard
          title="Active Recurring"
          value={stats?.active_recurring || 0}
          subtitle="Scheduled givers"
          icon={RefreshCw}
        />
        <StatCard
          title="Undeposited Batches"
          value={stats?.undeposited_batches || 0}
          subtitle="Open batches"
          icon={FileText}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Giving by Method */}
        <div className="bg-white border border-slate-200 rounded-lg p-5">
          <h3 className="font-semibold text-slate-900 mb-4">Giving by Method (YTD)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={methodData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
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
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Funds Overview */}
        <div className="bg-white border border-slate-200 rounded-lg p-5">
          <h3 className="font-semibold text-slate-900 mb-4">Fund Progress</h3>
          <div className="space-y-4">
            {funds.slice(0, 5).map((fund) => {
              const progress = fund.goal_amount 
                ? Math.min(100, (fund.current_amount / fund.goal_amount) * 100)
                : 0;
              return (
                <div key={fund.id}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-slate-700">{fund.name}</span>
                    <span className="text-sm text-slate-500 font-data">
                      {formatCurrency(fund.current_amount)} 
                      {fund.goal_amount && ` / ${formatCurrency(fund.goal_amount)}`}
                    </span>
                  </div>
                  {fund.goal_amount && (
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-emerald-500 rounded-full transition-all"
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
      <div className="bg-white border border-slate-200 rounded-lg">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="font-semibold text-slate-900">Recent Donations</h3>
          <div className="flex items-center gap-3">
            <Link to="/reports?type=giving" className="text-sm text-blue-600 hover:underline">
              View Reports →
            </Link>
          </div>
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
                  <td colSpan={6} className="text-center py-8 text-slate-400">
                    No donations recorded
                  </td>
                </tr>
              ) : (
                donations.map((donation) => (
                  <tr key={donation.id} className="hover:bg-slate-50">
                    <td className="font-data text-sm">{formatDate(donation.donation_date)}</td>
                    <td>
                      {donation.donor_name ? (
                        <div className="flex items-center gap-2">
                          <Avatar className="w-7 h-7">
                            <AvatarImage src={donation.donor_photo} />
                            <AvatarFallback className="text-xs">
                              {donation.donor_name.split(' ').map(n => n[0]).join('')}
                            </AvatarFallback>
                          </Avatar>
                          <span className="font-medium text-slate-900">{donation.donor_name}</span>
                        </div>
                      ) : (
                        <span className="text-slate-400">Anonymous</span>
                      )}
                    </td>
                    <td className="text-slate-600">{donation.fund_name || 'General Fund'}</td>
                    <td className="text-right font-data font-semibold text-slate-900">
                      {formatCurrency(donation.amount)}
                    </td>
                    <td>
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
                        {donation.payment_method === 'card' && <CreditCard className="w-3 h-3" />}
                        {donation.payment_method === 'check' && <FileText className="w-3 h-3" />}
                        {donation.payment_method === 'cash' && <Banknote className="w-3 h-3" />}
                        {donation.payment_method === 'ach' && <Building2 className="w-3 h-3" />}
                        {donation.payment_method === 'crypto' && <Bitcoin className="w-3 h-3" />}
                        {donation.payment_method.charAt(0).toUpperCase() + donation.payment_method.slice(1)}
                      </span>
                    </td>
                    <td className="text-slate-400 text-sm">{donation.notes || '—'}</td>
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
              Showing {((page - 1) * perPage) + 1}–{Math.min(page * perPage, total)} of {total.toLocaleString()} donations
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
      <div className="bg-white border border-slate-200 rounded-lg">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="font-semibold text-slate-900">Donation Batches</h3>
          <Button variant="outline" size="sm">Create Batch</Button>
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
                  <td colSpan={5} className="text-center py-8 text-slate-400">
                    No batches created
                  </td>
                </tr>
              ) : (
                batches.map((batch) => (
                  <tr key={batch.id} className="hover:bg-slate-50 cursor-pointer">
                    <td className="font-medium text-slate-900">{batch.name}</td>
                    <td className="font-data text-sm">{formatDate(batch.date)}</td>
                    <td>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        batch.status === 'open' ? 'bg-emerald-50 text-emerald-700' :
                        batch.status === 'closed' ? 'bg-amber-50 text-amber-700' :
                        'bg-slate-100 text-slate-600'
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
