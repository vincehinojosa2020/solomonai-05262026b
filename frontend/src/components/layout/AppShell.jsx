import { useState, useEffect } from 'react';
import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, Users, Home, UsersRound, Calendar, 
  CheckSquare, DollarSign, Mail, BarChart3, Settings, 
  Building2, Search, Bell, ChevronLeft, Menu, Command,
  LogOut, Plug, Globe, Video, GraduationCap, BookOpen, ShoppingBag, MessageSquare, Coffee, Code, Baby, Zap, Shield,
  ChevronDown, MapPin, Check, Music, HandHeart, GitBranch, FileText, ListFilter, Merge, ClipboardList, CreditCard
} from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import CommandPalette from '@/components/CommandPalette';
import SolomonChat from '@/components/SolomonChat';
import DemoWalkthrough from '@/components/DemoWalkthrough';
import { API_URL } from '@/lib/utils';
import { navItems, platformNavItems } from './AppShellNav';

export default function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [tenant, setTenant] = useState(null);
  const [user, setUser] = useState(null);
  const [impersonatedTenant, setImpersonatedTenant] = useState(null);
  const [campusSwitching, setCampusSwitching] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const switchCampus = async (tenantId) => {
    const token = sessionStorage.getItem('session_token');
    if (!token) return;
    setCampusSwitching(true);
    try {
      const res = await fetch(`${API_URL}/auth/switch-campus`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ tenant_id: tenantId }),
      });
      if (res.ok) {
        const data = await res.json();
        // Re-fetch user data to reflect new campus
        const meRes = await fetch(`${API_URL}/auth/me`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (meRes.ok) {
          const userData = await meRes.json();
          setUser(userData);
        }
        // Re-fetch tenant info
        fetch(`${API_URL}/tenant`).then(r => r.json()).then(d => setTenant(d)).catch(() => {});
        // Navigate to dashboard to refresh data
        navigate('/dashboard');
      }
    } catch (err) {
      console.error('Campus switch failed:', err);
    } finally {
      setCampusSwitching(false);
    }
  };

  useEffect(() => {
    // Check if platform admin is viewing a specific church
    const storedTenant = sessionStorage.getItem('impersonate_tenant');
    if (storedTenant) {
      setImpersonatedTenant(JSON.parse(storedTenant));
    } else {
      setImpersonatedTenant(null);
    }
    
    // Fetch tenant info
    fetch(`${API_URL}/tenant`)
      .then(res => res.json())
      .then(data => setTenant(data))
      .catch(err => console.error('Failed to fetch tenant:', err));
    
    // Fetch current user
    const token = sessionStorage.getItem('session_token');
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
    fetch(`${API_URL}/auth/me`, { headers })
      .then(res => res.ok ? res.json() : null)
      .then(data => setUser(data))
      .catch(err => console.error('Failed to fetch user:', err));
  }, [location.pathname]);  // Re-run when location changes

  const exitImpersonation = () => {
    sessionStorage.removeItem('impersonate_tenant');
    setImpersonatedTenant(null);
    navigate('/godmode');
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandOpen(true);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleLogout = async () => {
    try {
      const token = sessionStorage.getItem('session_token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      await fetch(`${API_URL}/auth/logout`, {
        method: 'POST',
        
        headers,
      });
    } catch (err) {
      console.error('Logout failed:', err);
    }
    sessionStorage.removeItem('session_token');
    sessionStorage.removeItem('user_data');
    navigate('/login');
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className="app-shell">
      {/* Skip to main content - WCAG AA */}
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:top-2 focus:left-2 focus:bg-blue-600 focus:text-white focus:px-4 focus:py-2 focus:rounded-lg focus:text-sm focus:font-medium" data-testid="skip-to-main">
        Skip to main content
      </a>
      {/* Sidebar */}
      <aside className={`app-sidebar ${collapsed ? 'collapsed' : ''}`} data-testid="app-sidebar" role="complementary" aria-label="Sidebar navigation">
        {/* Logo */}
        <div className="flex items-center justify-between h-12 px-3 border-b border-slate-700">
          {!collapsed && (
            <span className="logo-text" data-testid="app-logo" style={{ fontSize: 13, fontWeight: 600, letterSpacing: '0.02em' }}>
              {user?.role === 'platform_admin' ? 'Solomon AI' : (tenant?.church_name || tenant?.name || 'Church Admin')}
            </span>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 text-slate-500 hover:text-slate-300 transition-colors"
            data-testid="sidebar-toggle"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-expanded={!collapsed}
          >
            {collapsed ? <Menu className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-2 scrollbar-thin" role="navigation" aria-label="Main navigation">
          {/* Platform section for platform admins */}
          {user?.role === 'platform_admin' && platformNavItems.map((section, idx) => (
            <div key={`platform-${idx}`} className="nav-section">
              {!collapsed && (
                <div className="nav-section-label" style={{ color: '#a855f7' }}>{section.section}</div>
              )}
              {section.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                  data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                  title={collapsed ? item.name : undefined}
                  style={({ isActive }) => isActive ? { background: 'rgba(168, 85, 247, 0.2)' } : {}}
                >
                  <item.icon className="icon" style={{ color: '#a855f7' }} />
                  {!collapsed && <span style={{ color: '#a855f7' }}>{item.name}</span>}
                </NavLink>
              ))}
            </div>
          ))}
          
          {navItems.map((section, idx) => {
            // For platform admin without impersonation: only show limited nav
            // For platform admin WITH impersonation: show full church admin nav
            const isPlatformAdmin = user?.role === 'platform_admin';
            const isImpersonating = !!impersonatedTenant;
            
            const filteredItems = section.items.filter(item => {
              // Permission-based filtering
              if (item.permission) {
                const userPerms = JSON.parse(sessionStorage.getItem('user_permissions') || '[]');
                const userRole = sessionStorage.getItem('user_role') || '';
                // Always show for church_admin, platform_admin, senior_pastor
                if (!['church_admin', 'platform_admin', 'senior_pastor', 'admin'].includes(userRole)) {
                  if (!userPerms.includes(item.permission)) return false;
                }
              }
              // If platform admin and NOT impersonating, hide church-specific items
              if (isPlatformAdmin && !isImpersonating) {
                const platformOnlyPaths = ['/settings', '/integrations', '/audit-log', '/reports', '/war-room', '/dashboard'];
                return platformOnlyPaths.includes(item.path);
              }
              return true;
            });
            
            // Skip section if no items
            if (filteredItems.length === 0) return null;
            
            return (
            <div key={section.section} className="nav-section">
              {!collapsed && (
                <div className="nav-section-label">{section.section}</div>
              )}
              {filteredItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                  data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                  title={collapsed ? item.name : undefined}
                >
                  <item.icon className="icon" />
                  {!collapsed && <span>{item.name}</span>}
                  {!collapsed && item.badge === 'live' && (
                    <span className="ml-auto flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                    </span>
                  )}
                </NavLink>
              ))}
            </div>
            );
          })}
        </nav>

        {/* User Section */}
        {!collapsed && user && (
          <div className="p-3 border-t border-slate-700">
            <div className="flex items-center gap-2">
              <Avatar className="w-7 h-7">
                <AvatarImage src={user.picture} />
                <AvatarFallback className="bg-blue-600 text-white text-xs">
                  {user.role === 'platform_admin' ? 'S' : user.name?.split(' ').map(n => n[0]).join('') || 'U'}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-white truncate">
                  {user.role === 'platform_admin' ? 'Solomon' : user.name}
                </p>
                <p className="text-xs text-slate-500 truncate">
                  {user.role === 'platform_admin' ? 'Platform Admin' : user.email}
                </p>
              </div>
            </div>
          </div>
        )}
        {!collapsed && (
          <div className="px-3 py-2 text-center border-t border-slate-700">
            <span style={{ fontSize: 10, color: '#64748b', letterSpacing: '0.05em' }} data-testid="powered-by-solomon">Powered by Solomon AI</span>
          </div>
        )}
      </aside>

      {/* Main Content */}
      <main className="app-main" id="main-content" role="main">
        {/* Impersonation Banner - Shows when platform admin is viewing a specific church */}
        {impersonatedTenant && user?.role === 'platform_admin' && (
          <div className="impersonation-banner" data-testid="impersonation-banner">
            <div className="impersonation-content">
              <span 
                className="impersonation-dot" 
                style={{ backgroundColor: impersonatedTenant.primary_color }}
              />
              <span>Viewing as: <strong>{impersonatedTenant.name}</strong></span>
              <span className="impersonation-subdomain">({impersonatedTenant.subdomain}.solomon.ai)</span>
            </div>
            <button 
              onClick={exitImpersonation}
              className="impersonation-exit"
              data-testid="exit-impersonation"
            >
              ← Back to All Churches
            </button>
          </div>
        )}
        
        {/* Top Bar */}
        <header className="app-topbar" data-testid="app-topbar">
          <div className="flex items-center gap-3">
            {collapsed && (
              <span className="font-bold text-sm tracking-wider text-slate-900">
                SOL<span className="text-blue-600">O</span>MON
              </span>
            )}
          </div>

          {/* Search */}
          <button 
            className="search-input cursor-pointer"
            onClick={() => setCommandOpen(true)}
            data-testid="global-search-btn"
          >
            <Search className="search-icon" />
            <span className="flex-1 text-left text-slate-400 text-sm">Search...</span>
            <span className="kbd">
              <Command className="w-3 h-3" />K
            </span>
          </button>

          {/* Right Actions */}
          <div className="flex items-center gap-2">
            {/* Notifications */}
            <button 
              className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors"
              data-testid="notifications-btn"
            >
              <Bell className="w-4 h-4" />
            </button>

            {/* Mode Toggle — Lyft-style Admin ↔ Member switch */}
            {(user?.role !== 'platform_admin' || impersonatedTenant) && (
              <div className="flex items-center gap-1 bg-slate-100 border border-slate-200 rounded-lg p-0.5" data-testid="mode-toggle">
                <button
                  className="px-3 py-1.5 text-xs font-semibold rounded-md transition-all"
                  style={{ background: '#0f172a', color: 'white' }}
                  data-testid="mode-admin"
                  title="Admin view — manage your church"
                >
                  Admin
                </button>
                <button
                  className="px-3 py-1.5 text-xs font-semibold rounded-md transition-all text-slate-500 hover:text-slate-700"
                  onClick={() => { localStorage.setItem('portal_mode', 'true'); navigate('/portal'); }}
                  data-testid="mode-member"
                  title="Preview what your members see in the portal"
                >
                  Member
                </button>
              </div>
            )}

            {/* Campus Switcher / Tenant Badge */}
            {(user?.role !== 'platform_admin' || impersonatedTenant) && (
              user?.accessible_campuses && user.accessible_campuses.length > 1 ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button 
                      className="flex items-center gap-2 px-2.5 py-1.5 bg-slate-100 border border-slate-200 rounded-lg hover:bg-slate-200 transition-colors"
                      data-testid="campus-switcher-btn"
                      disabled={campusSwitching}
                    >
                      <MapPin className="w-3 h-3 text-blue-600" />
                      <span className="text-xs font-semibold text-slate-700">
                        {campusSwitching ? 'Switching...' : localStorage.getItem('campus_mode') === 'all' ? 'All Campuses' : (user.active_tenant_name || tenant?.name || user.tenant_name || 'Campus')}
                      </span>
                      <ChevronDown className="w-3 h-3 text-slate-400" />
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-56">
                    <DropdownMenuLabel className="text-xs text-slate-500">
                      {user.organization_name || 'Your Campuses'}
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={() => {
                        localStorage.setItem('campus_mode', 'all');
                        window.dispatchEvent(new Event('storage'));
                        navigate('/dashboard');
                      }}
                      className={`flex items-center gap-2 ${localStorage.getItem('campus_mode') === 'all' ? 'bg-purple-50 text-purple-700' : ''}`}
                      data-testid="campus-option-all"
                    >
                      <Globe className="w-3.5 h-3.5 text-purple-600" />
                      <span className="flex-1 text-sm font-semibold">All Campuses</span>
                      {localStorage.getItem('campus_mode') === 'all' && <Check className="w-3.5 h-3.5 text-purple-600" />}
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    {user.accessible_campuses.map((campus) => {
                      const isActive = localStorage.getItem('campus_mode') !== 'all' && (user.active_tenant_id || user.tenant_id) === campus.id;
                      return (
                        <DropdownMenuItem 
                          key={campus.id}
                          onClick={() => {
                            localStorage.removeItem('campus_mode');
                            window.dispatchEvent(new Event('storage'));
                            if (!isActive) switchCampus(campus.id);
                          }}
                          className={`flex items-center gap-2 ${isActive ? 'bg-blue-50 text-blue-700' : ''}`}
                          data-testid={`campus-option-${campus.id}`}
                        >
                          <MapPin className={`w-3.5 h-3.5 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                          <span className="flex-1 text-sm">{campus.name}</span>
                          {isActive && <Check className="w-3.5 h-3.5 text-blue-600" />}
                        </DropdownMenuItem>
                      );
                    })}
                  </DropdownMenuContent>
                </DropdownMenu>
              ) : (
                <div className="flex items-center gap-2 px-2 py-1 bg-slate-100 border border-slate-200">
                  <Building2 className="w-3 h-3 text-slate-500" />
                  <span className="text-xs font-medium text-slate-600">
                    {impersonatedTenant?.name || tenant?.name || 'Church'}
                  </span>
                </div>
              )
            )}

            {/* Preview Portal Link removed — use Member toggle above */}

            {/* User Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center gap-2" data-testid="user-menu-btn">
                  <Avatar className="w-7 h-7">
                    <AvatarImage src={user?.picture} />
                    <AvatarFallback className="bg-blue-600 text-white text-xs">
                      {user?.role === 'platform_admin' ? 'S' : user?.name?.split(' ').map(n => n[0]).join('') || 'U'}
                    </AvatarFallback>
                  </Avatar>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuLabel className="font-normal">
                  <div className="text-sm font-medium">
                    {user?.role === 'platform_admin' ? 'Solomon' : user?.name}
                  </div>
                  <div className="text-xs text-slate-500">
                    {user?.role === 'platform_admin' ? 'Platform Admin' : user?.email}
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem>Profile</DropdownMenuItem>
                <DropdownMenuItem>Settings</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                  <LogOut className="w-4 h-4 mr-2" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Page Content */}
        <div className="app-content">
          <Outlet context={{ tenant, user, greeting: getGreeting() }} />
        </div>
      </main>

      {/* Command Palette */}
      {commandOpen && (
        <CommandPalette onClose={() => setCommandOpen(false)} />
      )}

      {/* Solomon AI Chat */}
      <SolomonChat />
      
      {/* Demo Walkthrough for first-time admins */}
      <DemoWalkthrough 
        userRole={user?.role || 'church_admin'} 
        userName={user?.name?.split(' ')[0] || 'there'}
        onNavigate={navigate}
      />

      {/* Mobile Bottom Navigation */}
      <nav className="admin-bottom-nav" data-testid="mobile-bottom-nav">
        <NavLink to="/dashboard" className={({isActive}) => `admin-bottom-nav-item ${isActive ? 'active' : ''}`} data-testid="mobile-nav-dashboard">
          <LayoutDashboard size={20} />
          <span>Home</span>
        </NavLink>
        <NavLink to="/people" className={({isActive}) => `admin-bottom-nav-item ${isActive ? 'active' : ''}`} data-testid="mobile-nav-people">
          <Users size={20} />
          <span>People</span>
        </NavLink>
        <NavLink to="/services" className={({isActive}) => `admin-bottom-nav-item ${isActive ? 'active' : ''}`} data-testid="mobile-nav-services">
          <Music size={20} />
          <span>Services</span>
        </NavLink>
        <NavLink to="/admin/groups" className={({isActive}) => `admin-bottom-nav-item ${isActive ? 'active' : ''}`} data-testid="mobile-nav-groups">
          <UsersRound size={20} />
          <span>Groups</span>
        </NavLink>
        <NavLink to="/giving" className={({isActive}) => `admin-bottom-nav-item ${isActive ? 'active' : ''}`} data-testid="mobile-nav-giving">
          <DollarSign size={20} />
          <span>Giving</span>
        </NavLink>
      </nav>
    </div>
  );
}
