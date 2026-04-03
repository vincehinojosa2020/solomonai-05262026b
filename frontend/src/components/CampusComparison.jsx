import { useState, useEffect } from 'react';
import {
  BarChart3, Users, DollarSign, TrendingUp, MapPin,
  Coffee, ShoppingBag, Heart, ChevronDown, ArrowUpRight,
  ArrowDownRight, Minus
} from 'lucide-react';
import { API_URL, formatCurrency } from '@/lib/utils';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, LineChart, Line
} from 'recharts';

const COLORS = ['#4f6ef7', '#22c55e', '#f59e0b', '#ec4899', '#8b5cf6'];

const MetricCard = ({ label, value, format = 'number', comparison, color }) => {
  const formatted = format === 'currency' ? formatCurrency(value) :
                    format === 'percent' ? `${value}%` :
                    typeof value === 'number' ? value.toLocaleString() : value;

  return (
    <div className="comparison-metric-card" data-testid={`metric-${label.toLowerCase().replace(/\s/g, '-')}`}>
      <span className="metric-label">{label}</span>
      <span className="metric-value" style={{ color: color || 'inherit' }}>{formatted}</span>
    </div>
  );
};

const TrendIndicator = ({ current, previous }) => {
  if (!previous || previous === 0) return <Minus className="w-3 h-3 text-gray-400" />;
  const pct = ((current - previous) / previous * 100).toFixed(1);
  if (pct > 0) return <span className="trend-up"><ArrowUpRight className="w-3 h-3" /> {pct}%</span>;
  if (pct < 0) return <span className="trend-down"><ArrowDownRight className="w-3 h-3" /> {Math.abs(pct)}%</span>;
  return <Minus className="w-3 h-3 text-gray-400" />;
};

export default function CampusComparison({ organizationId, onBack }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState('total_members');

  useEffect(() => {
    fetchComparison();
  }, [organizationId]);

  const fetchComparison = async () => {
    try {
      const res = await fetch(`${API_URL}/platform/organizations/${organizationId}/comparison`);
      if (res.ok) {
        setData(await res.json());
      }
    } catch (err) {
      console.error('Failed to fetch comparison:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="comparison-loading">Loading campus comparison...</div>;
  }

  if (!data) {
    return <div className="comparison-error">Failed to load comparison data</div>;
  }

  const barMetrics = [
    { key: 'total_members', label: 'Total Members', format: 'number' },
    { key: 'active_members', label: 'Active Members', format: 'number' },
    { key: 'weekly_attendance', label: 'Weekly Attendance', format: 'number' },
    { key: 'mtd_giving', label: 'Monthly Giving', format: 'currency' },
    { key: 'active_groups', label: 'Groups', format: 'number' },
    { key: 'cafe_orders_week', label: 'Cafe Orders/Week', format: 'number' },
    { key: 'merch_orders_week', label: 'Merch Orders/Week', format: 'number' },
    { key: 'recurring_givers', label: 'Recurring Givers', format: 'number' },
  ];

  const efficiencyMetrics = [
    { key: 'engagement_rate', label: 'Engagement Rate', format: 'percent', icon: Users },
    { key: 'attendance_rate', label: 'Attendance Rate', format: 'percent', icon: TrendingUp },
    { key: 'giving_per_capita', label: 'Giving / Member', format: 'currency', icon: DollarSign },
    { key: 'recurring_rate', label: 'Recurring Donor %', format: 'percent', icon: Heart },
    { key: 'members_per_group', label: 'Members / Group', format: 'number', icon: Users },
  ];

  const chartData = data.campuses.map((c, i) => ({
    name: c.name.replace('Abundant ', ''),
    ...c.metrics,
    fill: COLORS[i % COLORS.length],
  }));

  const selectedBarMetric = barMetrics.find(m => m.key === selectedMetric);

  return (
    <div className="campus-comparison" data-testid="campus-comparison">
      {/* Header */}
      <div className="comparison-header">
        <div>
          <button className="comparison-back-btn" onClick={onBack} data-testid="comparison-back-btn">
            Back to Organizations
          </button>
          <h2 className="comparison-title">{data.organization_name}</h2>
          <p className="comparison-subtitle">
            {data.campus_count} campuses &middot; {data.totals.total_members.toLocaleString()} total members
          </p>
        </div>
      </div>

      {/* Org-wide Summary */}
      <div className="comparison-summary-grid" data-testid="comparison-summary">
        <MetricCard label="Total Members" value={data.totals.total_members} color="#4f6ef7" />
        <MetricCard label="Monthly Giving" value={data.totals.total_mtd_giving} format="currency" color="#22c55e" />
        <MetricCard label="Combined MRR" value={data.totals.total_mrr} format="currency" color="#8b5cf6" />
        <MetricCard label="YTD Giving" value={data.totals.total_ytd_giving} format="currency" color="#f59e0b" />
        <MetricCard label="Total Groups" value={data.totals.total_groups} color="#ec4899" />
        <MetricCard label="Giving / Member" value={data.totals.giving_per_capita} format="currency" color="#14b8a6" />
      </div>

      {/* Bar Chart Comparison */}
      <div className="comparison-chart-section" data-testid="comparison-bar-chart">
        <div className="chart-header">
          <h3>Campus Comparison</h3>
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            className="metric-selector"
            data-testid="metric-selector"
          >
            {barMetrics.map(m => (
              <option key={m.key} value={m.key}>{m.label}</option>
            ))}
          </select>
        </div>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 13 }} />
              <YAxis
                tick={{ fill: '#64748b', fontSize: 12 }}
                tickFormatter={v => selectedBarMetric?.format === 'currency' ? `$${(v/1000).toFixed(0)}k` : v.toLocaleString()}
              />
              <Tooltip
                formatter={(v) => selectedBarMetric?.format === 'currency' ? formatCurrency(v) : v.toLocaleString()}
                contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8, color: '#fff', fontSize: 13 }}
              />
              <Bar dataKey={selectedMetric} radius={[6, 6, 0, 0]}>
                {chartData.map((entry, idx) => (
                  <rect key={`bar-${idx}`} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Efficiency Metrics (Per Capita) */}
      <div className="comparison-efficiency" data-testid="comparison-efficiency">
        <h3>Efficiency Metrics</h3>
        <div className="efficiency-grid">
          {data.campuses.map((campus, ci) => (
            <div key={campus.tenant_id} className="efficiency-campus-card" style={{ borderTopColor: COLORS[ci % COLORS.length] }}>
              <h4 style={{ color: COLORS[ci % COLORS.length] }}>{campus.name}</h4>
              <div className="efficiency-metrics">
                {efficiencyMetrics.map(em => {
                  const Icon = em.icon;
                  const val = campus.metrics[em.key];
                  const formatted = em.format === 'currency' ? formatCurrency(val) :
                                    em.format === 'percent' ? `${val}%` : val?.toLocaleString();
                  return (
                    <div key={em.key} className="efficiency-row">
                      <span className="efficiency-label"><Icon className="w-3.5 h-3.5" /> {em.label}</span>
                      <span className="efficiency-value">{formatted}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Giving Trends */}
      {data.giving_trends && data.giving_trends.length > 0 && (
        <div className="comparison-chart-section" data-testid="comparison-giving-trends">
          <h3>Giving Trends (Last 4 Weeks)</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={data.giving_trends} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="week" tick={{ fill: '#64748b', fontSize: 12 }} />
                <YAxis tick={{ fill: '#64748b', fontSize: 12 }} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
                <Tooltip
                  formatter={(v) => formatCurrency(v)}
                  contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8, color: '#fff', fontSize: 13 }}
                />
                <Legend />
                {data.campuses.map((c, i) => (
                  <Line
                    key={c.tenant_id}
                    type="monotone"
                    dataKey={c.name}
                    stroke={COLORS[i % COLORS.length]}
                    strokeWidth={2.5}
                    dot={{ r: 4, fill: COLORS[i % COLORS.length] }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Campus Detail Cards */}
      <div className="comparison-campus-cards" data-testid="comparison-campus-cards">
        <h3>Campus Details</h3>
        <div className="campus-cards-grid">
          {data.campuses.map((campus, ci) => (
            <div key={campus.tenant_id} className="campus-detail-card" style={{ borderLeftColor: COLORS[ci % COLORS.length] }}>
              <div className="campus-card-header">
                <h4>{campus.name}</h4>
                <span className="campus-plan-badge">{campus.plan}</span>
              </div>
              <div className="campus-card-location">
                <MapPin className="w-3.5 h-3.5" /> {campus.location}
              </div>
              <div className="campus-card-stats">
                <div><Users className="w-3.5 h-3.5" /> <strong>{campus.metrics.total_members.toLocaleString()}</strong> members</div>
                <div><DollarSign className="w-3.5 h-3.5" /> <strong>{formatCurrency(campus.metrics.mtd_giving)}</strong> /month</div>
                <div><Coffee className="w-3.5 h-3.5" /> <strong>{campus.metrics.cafe_orders_week}</strong> cafe orders/wk</div>
                <div><ShoppingBag className="w-3.5 h-3.5" /> <strong>{campus.metrics.merch_orders_week}</strong> merch orders/wk</div>
                <div><BarChart3 className="w-3.5 h-3.5" /> <strong>{campus.metrics.active_groups}</strong> active groups</div>
                <div><Heart className="w-3.5 h-3.5" /> <strong>{campus.metrics.recurring_givers.toLocaleString()}</strong> recurring givers</div>
              </div>
              <div className="campus-card-mrr">
                <span>MRR:</span> <strong>{formatCurrency(campus.mrr)}</strong>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
