import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Building2, Users, DollarSign, TrendingUp, Settings, 
  CheckCircle, XCircle, AlertCircle, ChevronRight, 
  Search, Filter, MoreVertical, Eye, Edit, Trash2,
  Globe, Shield, Activity, BarChart3
} from 'lucide-react';
import { API_URL, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';

export default function PlatformDashboard() {
  const navigate = useNavigate();
  const [tenants, setTenants] = useState([]);
  const [stats, setStats] = useState({
    totalChurches: 0,
    activeChurches: 0,
    totalMembers: 0,
    totalDonationsThisMonth: 0
  });
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedTenant, setSelectedTenant] = useState(null);

  useEffect(() => {
    fetchTenants();
  }, []);

  const fetchTenants = async () => {
    try {
      const res = await fetch(`${API_URL}/tenants`, { credentials: 'include' });
      if (res.status === 403) {
        toast.error('Platform admin access required');
        navigate('/dashboard');
        return;
      }
      if (!res.ok) throw new Error('Failed to fetch tenants');
      
      const data = await res.json();
      setTenants(data);
      
      // Calculate stats
      const active = data.filter(t => t.subscription_status === 'active').length;
      const totalMembers = data.reduce((sum, t) => sum + (t.member_count || 0), 0);
      
      setStats({
        totalChurches: data.length,
        activeChurches: active,
        totalMembers: totalMembers,
        totalDonationsThisMonth: 847500 // Demo value
      });
    } catch (error) {
      console.error('Failed to fetch tenants:', error);
      toast.error('Failed to load platform data');
    } finally {
      setIsLoading(false);
    }
  };

  const updateSubscription = async (tenantId, status) => {
    try {
      const res = await fetch(`${API_URL}/tenants/${tenantId}/subscription?status=${status}`, {
        method: 'PATCH',
        credentials: 'include'
      });
      if (!res.ok) throw new Error('Failed to update subscription');
      
      toast.success(`Subscription ${status}`);
      fetchTenants();
    } catch (error) {
      toast.error('Failed to update subscription');
    }
  };

  const viewAsChurchAdmin = (tenant) => {
    // Store selected tenant for impersonation
    sessionStorage.setItem('impersonate_tenant', JSON.stringify(tenant));
    toast.success(`Viewing as ${tenant.name} admin`);
    navigate('/dashboard');
  };

  const filteredTenants = tenants.filter(tenant => {
    const matchesSearch = tenant.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         tenant.subdomain.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterStatus === 'all' || tenant.subscription_status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case 'active':
        return <span className="platform-badge active"><CheckCircle className="w-3 h-3" /> Active</span>;
      case 'suspended':
        return <span className="platform-badge suspended"><AlertCircle className="w-3 h-3" /> Suspended</span>;
      case 'cancelled':
        return <span className="platform-badge cancelled"><XCircle className="w-3 h-3" /> Cancelled</span>;
      default:
        return <span className="platform-badge">{status}</span>;
    }
  };

  if (isLoading) {
    return (
      <div className="platform-loading">
        <div className="spinner"></div>
        <p>Loading platform data...</p>
      </div>
    );
  }

  return (
    <div className="platform-dashboard" data-testid="platform-dashboard">
      {/* Header */}
      <div className="platform-header">
        <div>
          <h1 className="platform-title">
            <Globe className="w-8 h-8 text-purple-500" />
            Platform Admin
          </h1>
          <p className="platform-subtitle">Manage all churches on SAMSON</p>
        </div>
        <div className="platform-header-actions">
          <button className="btn-primary" onClick={() => toast.info('Coming soon: Add new church')}>
            <Building2 className="w-4 h-4" />
            Add Church
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="platform-stats-grid">
        <div className="platform-stat-card purple">
          <div className="platform-stat-icon">
            <Building2 className="w-6 h-6" />
          </div>
          <div className="platform-stat-content">
            <span className="platform-stat-value">{stats.totalChurches}</span>
            <span className="platform-stat-label">Total Churches</span>
          </div>
        </div>
        
        <div className="platform-stat-card green">
          <div className="platform-stat-icon">
            <CheckCircle className="w-6 h-6" />
          </div>
          <div className="platform-stat-content">
            <span className="platform-stat-value">{stats.activeChurches}</span>
            <span className="platform-stat-label">Active Subscriptions</span>
          </div>
        </div>
        
        <div className="platform-stat-card blue">
          <div className="platform-stat-icon">
            <Users className="w-6 h-6" />
          </div>
          <div className="platform-stat-content">
            <span className="platform-stat-value">{stats.totalMembers.toLocaleString()}</span>
            <span className="platform-stat-label">Total Members</span>
          </div>
        </div>
        
        <div className="platform-stat-card gold">
          <div className="platform-stat-icon">
            <DollarSign className="w-6 h-6" />
          </div>
          <div className="platform-stat-content">
            <span className="platform-stat-value">{formatCurrency(stats.totalDonationsThisMonth)}</span>
            <span className="platform-stat-label">Platform GMV (MTD)</span>
          </div>
        </div>
      </div>

      {/* Tenants Table */}
      <div className="platform-section">
        <div className="platform-section-header">
          <h2>Church Tenants</h2>
          <div className="platform-filters">
            <div className="platform-search">
              <Search className="w-4 h-4" />
              <input
                type="text"
                placeholder="Search churches..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                data-testid="platform-search"
              />
            </div>
            <select 
              value={filterStatus} 
              onChange={(e) => setFilterStatus(e.target.value)}
              className="platform-filter-select"
              data-testid="platform-filter"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        <div className="platform-table-container">
          <table className="platform-table" data-testid="tenants-table">
            <thead>
              <tr>
                <th>Church</th>
                <th>Subdomain</th>
                <th>Plan</th>
                <th>Members</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredTenants.map((tenant) => (
                <tr key={tenant.id} data-testid={`tenant-row-${tenant.subdomain}`}>
                  <td>
                    <div className="tenant-info">
                      <div 
                        className="tenant-color-dot" 
                        style={{ backgroundColor: tenant.primary_color }}
                      />
                      <div>
                        <span className="tenant-name">{tenant.name}</span>
                        <span className="tenant-location">
                          {tenant.city}, {tenant.state}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <code className="tenant-subdomain">{tenant.subdomain}.samson.ai</code>
                  </td>
                  <td>
                    <span className="tenant-plan">{tenant.plan}</span>
                  </td>
                  <td>
                    <span className="tenant-members">{(tenant.member_count || 0).toLocaleString()}</span>
                  </td>
                  <td>{getStatusBadge(tenant.subscription_status)}</td>
                  <td>
                    <div className="tenant-actions">
                      <button 
                        className="action-btn view"
                        onClick={() => viewAsChurchAdmin(tenant)}
                        title="View as Church Admin"
                        data-testid={`view-${tenant.subdomain}`}
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button 
                        className="action-btn edit"
                        onClick={() => setSelectedTenant(tenant)}
                        title="Manage"
                      >
                        <Settings className="w-4 h-4" />
                      </button>
                      {tenant.subscription_status === 'active' ? (
                        <button 
                          className="action-btn suspend"
                          onClick={() => updateSubscription(tenant.id, 'suspended')}
                          title="Suspend"
                        >
                          <AlertCircle className="w-4 h-4" />
                        </button>
                      ) : (
                        <button 
                          className="action-btn activate"
                          onClick={() => updateSubscription(tenant.id, 'active')}
                          title="Activate"
                        >
                          <CheckCircle className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="platform-quick-actions">
        <h3>Quick Actions</h3>
        <div className="platform-actions-grid">
          <button className="platform-action-card" onClick={() => toast.info('Coming soon')}>
            <BarChart3 className="w-5 h-5" />
            <span>Platform Analytics</span>
          </button>
          <button className="platform-action-card" onClick={() => toast.info('Coming soon')}>
            <Shield className="w-5 h-5" />
            <span>Security Audit</span>
          </button>
          <button className="platform-action-card" onClick={() => toast.info('Coming soon')}>
            <Activity className="w-5 h-5" />
            <span>System Health</span>
          </button>
          <button className="platform-action-card" onClick={() => toast.info('Coming soon')}>
            <Settings className="w-5 h-5" />
            <span>Platform Settings</span>
          </button>
        </div>
      </div>

      {/* Tenant Detail Modal */}
      {selectedTenant && (
        <div className="platform-modal-backdrop" onClick={() => setSelectedTenant(null)}>
          <div className="platform-modal" onClick={(e) => e.stopPropagation()}>
            <div className="platform-modal-header">
              <h3>{selectedTenant.name}</h3>
              <button onClick={() => setSelectedTenant(null)}>×</button>
            </div>
            <div className="platform-modal-content">
              <div className="modal-info-row">
                <span>Subdomain:</span>
                <code>{selectedTenant.subdomain}.samson.ai</code>
              </div>
              <div className="modal-info-row">
                <span>Plan:</span>
                <strong>{selectedTenant.plan}</strong>
              </div>
              <div className="modal-info-row">
                <span>Member Limit:</span>
                <strong>{selectedTenant.member_limit?.toLocaleString()}</strong>
              </div>
              <div className="modal-info-row">
                <span>Status:</span>
                {getStatusBadge(selectedTenant.subscription_status)}
              </div>
              <div className="modal-info-row">
                <span>Location:</span>
                <strong>{selectedTenant.city}, {selectedTenant.state}</strong>
              </div>
              <div className="modal-info-row">
                <span>Website:</span>
                <a href={selectedTenant.website} target="_blank" rel="noopener noreferrer">
                  {selectedTenant.website}
                </a>
              </div>
            </div>
            <div className="platform-modal-actions">
              <button 
                className="btn-secondary"
                onClick={() => viewAsChurchAdmin(selectedTenant)}
              >
                <Eye className="w-4 h-4" /> View as Admin
              </button>
              <button 
                className="btn-primary"
                onClick={() => {
                  setSelectedTenant(null);
                  toast.info('Edit functionality coming soon');
                }}
              >
                <Edit className="w-4 h-4" /> Edit Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
