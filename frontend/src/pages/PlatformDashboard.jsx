import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Building2, Users, DollarSign, TrendingUp, Settings, 
  CheckCircle, XCircle, AlertCircle, ChevronRight, 
  Search, Filter, MoreVertical, Eye, Edit, Trash2,
  Globe, Shield, Activity, BarChart3, UserPlus, Mail,
  Heart, Layers, Server, MapPin, Gauge, X, ChevronDown, ArrowUpCircle
} from 'lucide-react';
import { API_URL, formatCurrency } from '@/lib/utils';
import { toast } from 'sonner';
import CampusComparison from '@/components/CampusComparison';
import ChurchOnboardingWizard from '@/components/ChurchOnboardingWizard';

const ROLE_OPTIONS = [
  { value: 'member', label: 'Church Member' },
  { value: 'kids_volunteer', label: 'Kids Check-In Volunteer' },
  { value: 'small_group_leader', label: 'Small Group Leader' },
  { value: 'cafe_manager', label: 'Cafe Manager' },
  { value: 'merch_manager', label: 'Merch Manager' },
  { value: 'worship_media_team', label: 'Worship & Media Team' },
  { value: 'ministry_leader', label: 'Ministry Leader' },
  { value: 'executive_pastor', label: 'Executive Pastor' },
  { value: 'church_admin', label: 'Church Administrator' },
];

function getAuthHeaders() {
  const token = sessionStorage.getItem('session_token');
  return token ? { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
}

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
  const [healthScores, setHealthScores] = useState([]);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [showPromote, setShowPromote] = useState(null);
  const [createUserForm, setCreateUserForm] = useState({ name: '', email: '', tenant_id: '', role_template: 'member', password: 'Welcome2026!' });
  const [promoteRole, setPromoteRole] = useState('church_admin');
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
    fetchHealthScores();
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

  const fetchHealthScores = async () => {
    try {
      const res = await fetch(`${API_URL}/platform/health-scores`);
      if (res.ok) {
        setHealthScores(await res.json());
      }
    } catch (error) {
      console.error('Failed to fetch health scores:', error);
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
    sessionStorage.setItem('impersonate_tenant', JSON.stringify(tenant));
    toast.success(`Viewing as ${tenant.name} admin`);
    navigate('/dashboard');
  };

  const handleCreateUser = async () => {
    const { name, email, tenant_id, role_template, password } = createUserForm;
    if (!name || !email || !tenant_id) {
      toast.error('Name, email, and church are required');
      return;
    }
    try {
      const res = await fetch(`${API_URL}/platform/users/create`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ name, email, tenant_id, role_template, password }),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message);
        setShowCreateUser(false);
        setCreateUserForm({ name: '', email: '', tenant_id: '', role_template: 'member', password: 'Welcome2026!' });
        fetchMembers();
        fetchPlatformStats();
      } else {
        toast.error(data.detail || 'Failed to create user');
      }
    } catch (err) {
      toast.error('Failed to create user');
    }
  };

  const handlePromote = async (userId) => {
    try {
      const res = await fetch(`${API_URL}/platform/users/${userId}/promote`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({ role_template: promoteRole }),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message);
        setShowPromote(null);
        fetchMembers();
      } else {
        toast.error(data.detail || 'Failed to update role');
      }
    } catch (err) {
      toast.error('Failed to update role');
    }
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
      {/* Header - Enhanced God Mode */}
      <div className="platform-header" style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', color: 'white', padding: '28px 32px', borderRadius: 12, marginBottom: 24 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
            <div style={{ width: 44, height: 44, borderRadius: 10, background: 'rgba(168,85,247,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Globe className="w-6 h-6" style={{ color: '#a855f7' }} />
            </div>
            <div>
              <h1 style={{ fontSize: 24, fontWeight: 800, letterSpacing: '-0.02em', margin: 0, color: 'white' }}>
                Solomon AI Platform
              </h1>
              <p style={{ fontSize: 13, color: '#94a3b8', margin: 0 }}>God Mode &middot; Full platform oversight</p>
            </div>
          </div>
        </div>
        <div className="platform-header-actions" style={{ display: 'flex', gap: 8 }}>
          <button className="btn-primary" onClick={() => setShowCreateUser(true)} style={{ background: '#a855f7', border: 'none', padding: '10px 16px', borderRadius: 8, color: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }} data-testid="create-user-btn-header">
            <UserPlus className="w-4 h-4" />
            Create User
          </button>
          <button className="btn-primary" onClick={() => setShowOnboarding(true)} style={{ background: 'white', border: 'none', padding: '10px 16px', borderRadius: 8, color: '#0f172a', fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }} data-testid="add-church-btn">
            <Building2 className="w-4 h-4" />
            Add Church
          </button>
        </div>
      </div>

      {/* KPI Row - Enhanced */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 12, marginBottom: 24 }}>
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 20px' }}>
          <p style={{ fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Churches</p>
          <p style={{ fontSize: 28, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>{stats.totalChurches}</p>
          <p style={{ fontSize: 12, color: '#22c55e', fontWeight: 500 }}>{stats.activeChurches} active</p>
        </div>
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 20px' }}>
          <p style={{ fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Members</p>
          <p style={{ fontSize: 28, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>{stats.totalMembers.toLocaleString()}</p>
          <p style={{ fontSize: 12, color: '#3b82f6', fontWeight: 500 }}>+{stats.recentSignups} this week</p>
        </div>
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 20px' }}>
          <p style={{ fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Platform GMV</p>
          <p style={{ fontSize: 28, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>{formatCurrency(stats.totalDonationsThisMonth)}</p>
          <p style={{ fontSize: 12, color: '#64748b', fontWeight: 500 }}>Month to date</p>
        </div>
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 20px' }}>
          <p style={{ fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>MRR</p>
          <p style={{ fontSize: 28, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>{formatCurrency(stats.totalMrr)}</p>
          <p style={{ fontSize: 12, color: '#22c55e', fontWeight: 500 }}>Recurring</p>
        </div>
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 20px' }}>
          <p style={{ fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>ARR</p>
          <p style={{ fontSize: 28, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>{formatCurrency(stats.totalArr)}</p>
          <p style={{ fontSize: 12, color: '#a855f7', fontWeight: 500 }}>Annual run rate</p>
        </div>
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, padding: '16px 20px' }}>
          <p style={{ fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Organizations</p>
          <p style={{ fontSize: 28, fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>{organizations.length}</p>
          <p style={{ fontSize: 12, color: '#64748b', fontWeight: 500 }}>Multi-campus</p>
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
                <th>Health</th>
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
                  <td>
                    {(() => {
                      const hs = healthScores.find(h => h.tenant_id === tenant.id);
                      if (!hs || !hs.health) return <span className="health-score-na">—</span>;
                      const { score, grade } = hs.health;
                      const color = score >= 80 ? '#22c55e' : score >= 60 ? '#f59e0b' : score >= 40 ? '#f97316' : '#ef4444';
                      return (
                        <div className="health-score-pill" style={{ background: `${color}18`, color }} data-testid={`health-score-${tenant.subdomain}`}>
                          <span className="health-score-num">{score}</span>
                          <span className="health-score-grade">{grade}</span>
                        </div>
                      );
                    })()}
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
            <button 
              className="platform-btn primary"
              onClick={() => setShowCreateUser(true)}
              data-testid="create-user-btn"
            >
              <UserPlus className="w-4 h-4" />
              Create User
            </button>
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
                <th>Role</th>
                <th>Status</th>
                <th>Joined</th>
                <th style={{ width: 90, textAlign: 'center' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {members.map((member) => {
                const hasAdmin = member.permissions?.some(p => p.startsWith('admin.'));
                const roleLabel = member.role === 'church_admin' ? 'Admin' : (hasAdmin ? 'Leader' : 'Member');
                const roleClass = member.role === 'church_admin' ? 'role-admin' : (hasAdmin ? 'role-leader' : 'role-member');
                return (
                <tr key={member.user_id || member.id} data-testid={`member-row-${member.email}`}>
                  <td>
                    <div className="member-info">
                      <div className="member-avatar">
                        {member.name?.charAt(0)?.toUpperCase() || '?'}
                      </div>
                      <div>
                        <span className="member-name">{member.name || 'Unknown'}</span>
                        {member.role_title && member.role_title !== 'Church Member' && (
                          <span className="member-title-sub">{member.role_title}</span>
                        )}
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className="member-email">{member.email}</span>
                  </td>
                  <td>
                    <span className="member-church">{member.church_name || 'N/A'}</span>
                  </td>
                  <td>
                    <span className={`role-badge ${roleClass}`}>{roleLabel}</span>
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
                  <td style={{ textAlign: 'center' }}>
                    <button
                      className="promote-btn"
                      title="Change Role"
                      onClick={() => { setShowPromote(member); setPromoteRole('church_admin'); }}
                      data-testid={`promote-btn-${member.email}`}
                    >
                      <ArrowUpCircle className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
                );
              })}
              {members.length === 0 && (
                <tr>
                  <td colSpan="7" className="no-results">
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

      {/* Create User Modal */}
      {showCreateUser && (
        <div className="modal-overlay" onClick={() => setShowCreateUser(false)} data-testid="create-user-modal">
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 460 }}>
            <div className="modal-header">
              <h3><UserPlus className="w-5 h-5" style={{ display: 'inline', verticalAlign: '-3px', marginRight: 8 }} />Create User Account</h3>
              <button className="modal-close" onClick={() => setShowCreateUser(false)} data-testid="close-create-user"><X className="w-4 h-4" /></button>
            </div>
            <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <label className="modal-label">
                Full Name
                <input className="modal-input" placeholder="e.g. Shannon Nieman" value={createUserForm.name} onChange={e => setCreateUserForm(f => ({...f, name: e.target.value}))} data-testid="create-user-name" />
              </label>
              <label className="modal-label">
                Email
                <input className="modal-input" type="email" placeholder="e.g. shannon@abundant.org" value={createUserForm.email} onChange={e => setCreateUserForm(f => ({...f, email: e.target.value}))} data-testid="create-user-email" />
              </label>
              <label className="modal-label">
                Church
                <select className="modal-input" value={createUserForm.tenant_id} onChange={e => setCreateUserForm(f => ({...f, tenant_id: e.target.value}))} data-testid="create-user-church">
                  <option value="">Select a church...</option>
                  {tenants.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </label>
              <label className="modal-label">
                Role
                <select className="modal-input" value={createUserForm.role_template} onChange={e => setCreateUserForm(f => ({...f, role_template: e.target.value}))} data-testid="create-user-role">
                  {ROLE_OPTIONS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
              </label>
              <label className="modal-label">
                Temporary Password
                <input className="modal-input" value={createUserForm.password} onChange={e => setCreateUserForm(f => ({...f, password: e.target.value}))} data-testid="create-user-password" />
              </label>
            </div>
            <div className="modal-footer">
              <button className="platform-btn secondary" onClick={() => setShowCreateUser(false)}>Cancel</button>
              <button className="platform-btn primary" onClick={handleCreateUser} data-testid="submit-create-user">Create Account</button>
            </div>
          </div>
        </div>
      )}

      {/* Promote / Change Role Modal */}
      {showPromote && (
        <div className="modal-overlay" onClick={() => setShowPromote(null)} data-testid="promote-modal">
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 420 }}>
            <div className="modal-header">
              <h3><ArrowUpCircle className="w-5 h-5" style={{ display: 'inline', verticalAlign: '-3px', marginRight: 8 }} />Change Role</h3>
              <button className="modal-close" onClick={() => setShowPromote(null)}><X className="w-4 h-4" /></button>
            </div>
            <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{ padding: '12px 16px', background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                <div style={{ fontWeight: 600, color: '#1e3a5f' }}>{showPromote.name}</div>
                <div style={{ fontSize: 13, color: '#64748b' }}>{showPromote.email}</div>
                <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>Current: {showPromote.role_title || showPromote.role}</div>
              </div>
              <label className="modal-label">
                New Role
                <select className="modal-input" value={promoteRole} onChange={e => setPromoteRole(e.target.value)} data-testid="promote-role-select">
                  {ROLE_OPTIONS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
              </label>
              <p style={{ fontSize: 12, color: '#64748b', lineHeight: '1.5' }}>
                Changing role updates permissions immediately. The user will see the change on their next login or page refresh.
                {promoteRole !== 'member' && ' They will gain the Admin/Member toggle.'}
              </p>
            </div>
            <div className="modal-footer">
              <button className="platform-btn secondary" onClick={() => setShowPromote(null)}>Cancel</button>
              <button className="platform-btn primary" onClick={() => handlePromote(showPromote.user_id)} data-testid="submit-promote">Update Role</button>
            </div>
          </div>
        </div>
      )}

      {/* Organizations Tab Content */}
      {activeTab === 'organizations' && !selectedOrg && (
        <div className="platform-section">
          <div className="platform-section-header">
            <h2>Multi-Campus Organizations</h2>
            <p className="section-description">Billing: 1 Account = Multiple Campuses. Each org gets one invoice.</p>
          </div>
          {organizations.length === 0 ? (
            <div className="no-results-card">
              <Layers className="w-8 h-8 text-gray-400" />
              <p>No multi-campus organizations yet.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {organizations.map((org) => (
                <div
                  key={org.organization_id}
                  style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 12, overflow: 'hidden' }}
                  data-testid={`org-card-${org.organization_id}`}
                >
                  {/* Org Header */}
                  <div style={{ padding: '20px 24px', borderBottom: '1px solid #f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                      <h3 style={{ fontSize: 18, fontWeight: 700, color: '#0f172a', margin: '0 0 4px 0' }}>{org.organization_name}</h3>
                      <div style={{ display: 'flex', gap: 16, fontSize: 13, color: '#64748b' }}>
                        <span><strong>{org.campuses.length}</strong> campuses</span>
                        <span><strong>{org.total_members.toLocaleString()}</strong> total members</span>
                        <span><strong>{formatCurrency(org.total_mrr)}</strong> MRR</span>
                        <span style={{ color: '#a855f7', fontWeight: 600 }}>1 billing account</span>
                      </div>
                    </div>
                    <button
                      onClick={() => setSelectedOrg(org.organization_id)}
                      style={{ padding: '8px 16px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 13, fontWeight: 600, color: '#334155', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}
                    >
                      Compare <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                  {/* Campus Rows */}
                  <div>
                    {org.campuses.map((c, idx) => (
                      <div
                        key={c.tenant_id}
                        style={{
                          display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr',
                          padding: '12px 24px', fontSize: 13, alignItems: 'center',
                          borderBottom: idx < org.campuses.length - 1 ? '1px solid #f1f5f9' : 'none',
                          background: idx % 2 === 0 ? '#fff' : '#fafbfc'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <MapPin style={{ width: 14, height: 14, color: '#3b82f6' }} />
                          <span style={{ fontWeight: 600, color: '#1e293b' }}>{c.name}</span>
                        </div>
                        <span style={{ color: '#64748b' }}>{c.member_count?.toLocaleString() || 0} members</span>
                        <span style={{ color: '#64748b' }}>{formatCurrency(c.mrr || 0)} MRR</span>
                        <span style={{ color: '#64748b' }}>{formatCurrency(c.mtd_giving || 0)} MTD</span>
                        <button
                          onClick={() => viewAsChurchAdmin({ id: c.tenant_id, name: c.name })}
                          style={{ padding: '4px 12px', background: 'none', border: '1px solid #e2e8f0', borderRadius: 6, fontSize: 12, color: '#3b82f6', cursor: 'pointer', fontWeight: 500, justifySelf: 'end' }}
                        >
                          View
                        </button>
                      </div>
                    ))}
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

      {/* Health Scores Leaderboard - visible on churches tab */}
      {activeTab === 'churches' && healthScores.length > 0 && (
        <div className="platform-section health-scores-section" data-testid="health-scores-section">
          <h2><Gauge className="w-5 h-5" /> Church Health Scores</h2>
          <p className="section-description">Composite score (0-100) based on engagement, giving, community, attendance, and growth</p>
          <div className="health-scores-grid">
            {healthScores.map((church, idx) => {
              const h = church.health;
              const scoreColor = h.score >= 80 ? '#22c55e' : h.score >= 60 ? '#f59e0b' : h.score >= 40 ? '#f97316' : '#ef4444';
              const dims = h.dimensions || {};
              return (
                <div key={church.tenant_id} className="health-card" data-testid={`health-card-${church.tenant_id}`}>
                  <div className="health-card-top">
                    <div>
                      <span className="health-rank">#{idx + 1}</span>
                      <h4>{church.name}</h4>
                      <span className="health-location">{church.location}</span>
                    </div>
                    <div className="health-ring" style={{ '--score-color': scoreColor, '--score-pct': `${h.score}%` }}>
                      <span className="health-ring-score">{h.score}</span>
                      <span className="health-ring-grade">{h.grade}</span>
                    </div>
                  </div>
                  <div className="health-dimensions">
                    {Object.entries(dims).map(([key, dim]) => (
                      <div key={key} className="health-dim-row">
                        <span className="health-dim-label">{dim.label}</span>
                        <div className="health-dim-bar-wrap">
                          <div className="health-dim-bar" style={{ width: `${Math.min(100, dim.score)}%`, background: dim.score >= 70 ? '#22c55e' : dim.score >= 40 ? '#f59e0b' : '#ef4444' }} />
                        </div>
                        <span className="health-dim-value">{dim.value}{dim.unit === '%' ? '%' : dim.unit === '$/mo' ? `$/mo` : ''}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
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

      {/* Church Onboarding Wizard */}
      <ChurchOnboardingWizard
        isOpen={showOnboarding}
        onClose={() => setShowOnboarding(false)}
        onSuccess={() => fetchTenants()}
      />
    </div>
  );
}
