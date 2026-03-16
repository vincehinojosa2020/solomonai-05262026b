import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Building2, Users, DollarSign, TrendingUp, Settings, 
  CheckCircle, XCircle, AlertCircle, ChevronRight, 
  Search, Filter, MoreVertical, Eye, Edit, Trash2,
  Globe, Shield, Activity, BarChart3, UserPlus, Mail,
  Heart, Layers, Server, MapPin
} from 'lucide-react';
import { API_URL, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';
import CampusComparison from '@/components/CampusComparison';

export default function PlatformDashboard() {
  const navigate = useNavigate();
  const [tenants, setTenants] = useState([]);
  const [activeTab, setActiveTab] = useState('churches');
  const [members, setMembers] = useState([]);
  const [membersTotal, setMembersTotal] = useState(0);
  const [membersLoading, setMembersLoading] = useState(false);
  const [organizations, setOrganizations] = useState([]);
  const [selectedOrg, setSelectedOrg] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [stats, setStats] = useState({
    totalChurches: 0,
    activeChurches: 0,
    totalMembers: 0,
    totalDonationsThisMonth: 0,
    recentSignups: 0,
    totalMrr: 0,
    totalArr: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedTenant, setSelectedTenant] = useState(null);

  useEffect(() => {
    fetchTenants();
    fetchPlatformStats();
    fetchOrganizations();
    fetchHealth();
  }, []);

  useEffect(() => {
    if (activeTab === 'members') {
      fetchMembers();
    }
  }, [activeTab, searchQuery]);

  const fetchPlatformStats = async () => {
    try {
      const res = await fetch(`${API_URL}/platform/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats({
          totalChurches: data.churches.total,
          activeChurches: data.churches.active,
          totalMembers: data.members.total_users,
          totalDonationsThisMonth: data.giving.mtd_total,
          recentSignups: data.members.recent_signups,
          totalMrr: data.platform?.total_mrr || 0,
          totalArr: data.platform?.arr || 0,
        });
      }
    } catch (error) {
      console.error('Failed to fetch platform stats:', error);
    }
  };

  const fetchOrganizations = async () => {
    try {
      const res = await fetch(`${API_URL}/platform/organizations`);
      if (res.ok) {
        setOrganizations(await res.json());
      }
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/platform/health`);
      if (res.ok) {
        setHealthData(await res.json());
      }
    } catch (error) {
      console.error('Failed to fetch health:', error);
    }
  };

  const fetchTenants = async () => {
    try {
      const res = await fetch(`${API_URL}/tenants`);
      if (res.status === 403) {
        toast.error('Platform admin access required');
        navigate('/dashboard');
        return;
      }
      if (!res.ok) throw new Error('Failed to fetch tenants');
      
      const data = await res.json();
      setTenants(data);
    } catch (error) {
      console.error('Failed to fetch tenants:', error);
      toast.error('Failed to load platform data');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchMembers = async () => {
    setMembersLoading(true);
    try {
      const params = new URLSearchParams({ limit: '50' });
      if (searchQuery) params.append('search', searchQuery);
      
      const res = await fetch(`${API_URL}/admin/members?${params}`);
      if (res.ok) {
        const data = await res.json();
        setMembers(data.members);
        setMembersTotal(data.total);
      }
    } catch (error) {
      console.error('Failed to fetch members:', error);
    } finally {
      setMembersLoading(false);
    }
  };

  const updateSubscription = async (tenantId, status) => {
    try {
      const res = await fetch(`${API_URL}/tenants/${tenantId}/subscription?status=${status}`, {
        method: 'PATCH',
        
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
          <p className="platform-subtitle">Manage all churches on Solomon AI</p>
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

        <div className="platform-stat-card teal">
          <div className="platform-stat-icon">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div className="platform-stat-content">
            <span className="platform-stat-value">{formatCurrency(stats.totalMrr)}</span>
            <span className="platform-stat-label">Monthly Recurring Revenue</span>
          </div>
        </div>

        <div className="platform-stat-card pink">
          <div className="platform-stat-icon">
            <Heart className="w-6 h-6" />
          </div>
          <div className="platform-stat-content">
            <span className="platform-stat-value">{formatCurrency(stats.totalArr)}</span>
            <span className="platform-stat-label">Annual Run Rate</span>
          </div>
        </div>
      </div>

      {/* System Health Banner */}
      {healthData && (
        <div className={`health-banner ${healthData.status}`} data-testid="health-banner">
          <Server className="w-4 h-4" />
          <span>System: <strong>{healthData.status === 'healthy' ? 'All Systems Operational' : 'Degraded'}</strong></span>
          <span className="health-separator">|</span>
          <span>DB: {healthData.database.status}</span>
          <span className="health-separator">|</span>
          <span>Active Sessions: {healthData.sessions.active_now}</span>
          <span className="health-separator">|</span>
          <span>Uptime: {healthData.uptime}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="platform-tabs">
        <button 
          className={`platform-tab ${activeTab === 'churches' ? 'active' : ''}`}
          onClick={() => setActiveTab('churches')}
          data-testid="tab-churches"
        >
          <Building2 className="w-4 h-4" />
          Churches ({stats.totalChurches})
        </button>
        <button 
          className={`platform-tab ${activeTab === 'organizations' ? 'active' : ''}`}
          onClick={() => { setActiveTab('organizations'); setSelectedOrg(null); }}
          data-testid="tab-organizations"
        >
          <Layers className="w-4 h-4" />
          Organizations ({organizations.length})
        </button>
        <button 
          className={`platform-tab ${activeTab === 'members' ? 'active' : ''}`}
          onClick={() => setActiveTab('members')}
          data-testid="tab-members"
        >
          <Users className="w-4 h-4" />
          All Members ({stats.totalMembers.toLocaleString()})
        </button>
      </div>

      {/* Churches Tab Content */}
      {activeTab === 'churches' && (
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
                <th>MRR</th>
                <th>MTD Giving</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredTenants.map((tenant) => (
                <tr 
                  key={tenant.id} 
                  data-testid={`tenant-row-${tenant.subdomain}`}
                  onClick={() => viewAsChurchAdmin(tenant)}
                  className="tenant-row-clickable"
                  style={{ cursor: 'pointer' }}
                >
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
                    <code className="tenant-subdomain">{tenant.subdomain}.solomon.ai</code>
                  </td>
                  <td>
                    <span className="tenant-plan">{tenant.plan}</span>
                  </td>
                  <td>
                    <span className="tenant-members">{(tenant.member_count || 0).toLocaleString()}</span>
                  </td>
                  <td>
                    <span className="tenant-mrr">{formatCurrency(tenant.mrr || 0)}</span>
                  </td>
                  <td>
                    <span className="tenant-giving">{formatCurrency(tenant.mtd_giving || 0)}</span>
                  </td>
                  <td onClick={(e) => e.stopPropagation()}>{getStatusBadge(tenant.subscription_status)}</td>
                  <td onClick={(e) => e.stopPropagation()}>
                    <div className="tenant-actions">
                      <button 
                        className="action-btn view"
                        onClick={(e) => { e.stopPropagation(); viewAsChurchAdmin(tenant); }}
                        title="View as Church Admin"
                        data-testid={`view-${tenant.subdomain}`}
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button 
                        className="action-btn edit"
                        onClick={(e) => { e.stopPropagation(); setSelectedTenant(tenant); }}
                        title="Manage"
                      >
                        <Settings className="w-4 h-4" />
                      </button>
                      {tenant.subscription_status === 'active' ? (
                        <button 
                          className="action-btn suspend"
                          onClick={(e) => { e.stopPropagation(); updateSubscription(tenant.id, 'suspended'); }}
                          title="Suspend"
                        >
                          <AlertCircle className="w-4 h-4" />
                        </button>
                      ) : (
                        <button 
                          className="action-btn activate"
                          onClick={(e) => { e.stopPropagation(); updateSubscription(tenant.id, 'active'); }}
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
      )}

      {/* Members Tab Content */}
      {activeTab === 'members' && (
      <div className="platform-section">
        <div className="platform-section-header">
          <h2>Member Directory</h2>
          <div className="platform-filters">
            <div className="platform-search">
              <Search className="w-4 h-4" />
              <input
                type="text"
                placeholder="Search members by name or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                data-testid="member-search"
              />
            </div>
            <span className="member-count-badge">
              {membersTotal.toLocaleString()} total members
            </span>
          </div>
        </div>

        <div className="platform-table-container">
          {membersLoading ? (
            <div className="loading-spinner-inline">Loading members...</div>
          ) : (
          <table className="platform-table" data-testid="members-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Church</th>
                <th>Status</th>
                <th>Joined</th>
              </tr>
            </thead>
            <tbody>
              {members.map((member) => (
                <tr key={member.user_id || member.id} data-testid={`member-row-${member.email}`}>
                  <td>
                    <div className="member-info">
                      <div className="member-avatar">
                        {member.name?.charAt(0)?.toUpperCase() || '?'}
                      </div>
                      <span className="member-name">{member.name || 'Unknown'}</span>
                    </div>
                  </td>
                  <td>
                    <span className="member-email">{member.email}</span>
                  </td>
                  <td>
                    <span className="member-church">{member.church_name || 'N/A'}</span>
                  </td>
                  <td>
                    <span className={`member-status ${member.membership_status?.toLowerCase() || 'active'}`}>
                      {member.membership_status || 'Active'}
                    </span>
                  </td>
                  <td>
                    <span className="member-date">
                      {member.created_at ? new Date(member.created_at).toLocaleDateString() : 'N/A'}
                    </span>
                  </td>
                </tr>
              ))}
              {members.length === 0 && (
                <tr>
                  <td colSpan="5" className="no-results">
                    {searchQuery ? 'No members found matching your search' : 'No members yet'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
          )}
        </div>
      </div>
      )}

      {/* Organizations Tab Content */}
      {activeTab === 'organizations' && !selectedOrg && (
        <div className="platform-section">
          <div className="platform-section-header">
            <h2>Multi-Campus Organizations</h2>
            <p className="section-description">Churches operating multiple campuses as separate tenants</p>
          </div>
          {organizations.length === 0 ? (
            <div className="no-results-card">
              <Layers className="w-8 h-8 text-gray-400" />
              <p>No multi-campus organizations yet.</p>
              <p className="text-sm text-gray-500">When churches add multiple campuses, they'll appear here for comparison.</p>
            </div>
          ) : (
            <div className="org-cards-grid">
              {organizations.map((org) => (
                <div
                  key={org.organization_id}
                  className="org-card"
                  onClick={() => setSelectedOrg(org.organization_id)}
                  data-testid={`org-card-${org.organization_id}`}
                >
                  <div className="org-card-header">
                    <h3>{org.organization_name}</h3>
                    <span className="org-campus-count">{org.campuses.length} campuses</span>
                  </div>
                  <div className="org-card-stats">
                    <div className="org-stat">
                      <Users className="w-4 h-4" />
                      <span>{org.total_members.toLocaleString()} members</span>
                    </div>
                    <div className="org-stat">
                      <DollarSign className="w-4 h-4" />
                      <span>{formatCurrency(org.total_mrr)} MRR</span>
                    </div>
                    <div className="org-stat">
                      <TrendingUp className="w-4 h-4" />
                      <span>{formatCurrency(org.total_mtd_giving)} /mo giving</span>
                    </div>
                  </div>
                  <div className="org-campuses-list">
                    {org.campuses.map((c) => (
                      <div key={c.tenant_id} className="org-campus-pill">
                        <MapPin className="w-3 h-3" /> {c.name}
                      </div>
                    ))}
                  </div>
                  <div className="org-card-footer">
                    <span>View Comparison</span>
                    <ChevronRight className="w-4 h-4" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Campus Comparison View */}
      {activeTab === 'organizations' && selectedOrg && (
        <CampusComparison
          organizationId={selectedOrg}
          onBack={() => setSelectedOrg(null)}
        />
      )}

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
                <code>{selectedTenant.subdomain}.solomon.ai</code>
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
