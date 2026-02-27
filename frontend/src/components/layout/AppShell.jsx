import { useState, useEffect } from 'react';
import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, Users, Home, UsersRound, Calendar, 
  CheckSquare, DollarSign, Mail, BarChart3, Settings, 
  Building2, Search, Bell, ChevronLeft, Menu, Command,
  LogOut, Plug, Globe, Video, GraduationCap, BookOpen, ShoppingBag, MessageSquare, Coffee
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
import { API_URL } from '@/lib/utils';

const navItems = [
  { section: 'OVERVIEW', items: [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  ]},
  { section: 'PEOPLE', items: [
    { name: 'Members', path: '/people', icon: Users },
    { name: 'Households', path: '/households', icon: Home },
    { name: 'Notes', path: '/notes', icon: MessageSquare },
  ]},
  { section: 'MINISTRY', items: [
    { name: 'Groups', path: '/admin/groups', icon: UsersRound },
    { name: 'Events', path: '/admin/events', icon: Calendar },
    { name: 'Attendance', path: '/attendance', icon: CheckSquare },
  ]},
  { section: 'STEWARDSHIP', items: [
    { name: 'Giving', path: '/giving', icon: DollarSign },
  ]},
  { section: 'CONNECT', items: [
    { name: 'Communications', path: '/communications', icon: Mail },
    { name: 'Media Library', path: '/media', icon: Video },
    { name: 'Thinkific', path: '/thinkific', icon: GraduationCap },
    { name: 'Abundant Pathways', path: '/abundant-pathways', icon: BookOpen },
    { name: 'Merch', path: '/merch', icon: ShoppingBag },
    { name: 'Cafe', path: '/cafe', icon: Coffee },
  ]},
  { section: 'ANALYTICS', items: [
    { name: 'Reports', path: '/reports', icon: BarChart3 },
  ]},
  { section: 'ADMIN', items: [
    { name: 'Settings', path: '/settings', icon: Settings },
    { name: 'Integrations', path: '/integrations', icon: Plug },
  ]},
];

// Platform admin gets an extra section
const platformNavItems = [
  { section: 'PLATFORM', items: [
    { name: 'All Churches', path: '/platform', icon: Globe },
    { name: 'Notes', path: '/notes', icon: MessageSquare },
  ]},
];

export default function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [tenant, setTenant] = useState(null);
  const [user, setUser] = useState(null);
  const [impersonatedTenant, setImpersonatedTenant] = useState(null);
  const location = useLocation();
  const navigate = useNavigate();

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
    fetch(`${API_URL}/auth/me`, { credentials: 'include' })
      .then(res => res.ok ? res.json() : null)
      .then(data => setUser(data))
      .catch(err => console.error('Failed to fetch user:', err));
  }, [location.pathname]);  // Re-run when location changes

  const exitImpersonation = () => {
    sessionStorage.removeItem('impersonate_tenant');
    setImpersonatedTenant(null);
    navigate('/platform');
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
      await fetch(`${API_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
      navigate('/login');
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className={`app-sidebar ${collapsed ? 'collapsed' : ''}`} data-testid="app-sidebar">
        {/* Logo */}
        <div className="flex items-center justify-between h-12 px-3 border-b border-slate-700">
          {!collapsed && (
            <span className="logo-text" data-testid="app-logo">
              SOL<span className="logo-accent">O</span>MON
            </span>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 text-slate-500 hover:text-slate-300 transition-colors"
            data-testid="sidebar-toggle"
          >
            {collapsed ? <Menu className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-2 scrollbar-thin">
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
              // If platform admin and NOT impersonating, hide church-specific items
              if (isPlatformAdmin && !isImpersonating) {
                // Only show Settings, Integrations for platform admin without context
                const platformOnlyPaths = ['/settings', '/integrations'];
                return platformOnlyPaths.includes(item.path);
              }
              // If impersonating or regular church admin, show all items
              return true;
            });
            
            // Skip section if no items
            if (filteredItems.length === 0) return null;
            
            return (
            <div key={idx} className="nav-section">
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
      </aside>

      {/* Main Content */}
      <div className="app-main">
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

            {/* Tenant Badge - Hide for platform admin unless impersonating */}
            {(user?.role !== 'platform_admin' || impersonatedTenant) && (
              <div className="flex items-center gap-2 px-2 py-1 bg-slate-100 border border-slate-200">
                <Building2 className="w-3 h-3 text-slate-500" />
                <span className="text-xs font-medium text-slate-600">
                  {impersonatedTenant?.name || tenant?.name || 'Church'}
                </span>
              </div>
            )}

            {/* Preview Portal Link - Hide for platform admin unless impersonating */}
            {(user?.role !== 'platform_admin' || impersonatedTenant) && (
              <a
                href="/portal"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-600 hover:underline flex items-center gap-1"
                data-testid="preview-portal-link"
              >
                ↗ Preview Member Portal
              </a>
            )}

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
        <main className="app-content">
          <Outlet context={{ tenant, user, greeting: getGreeting() }} />
        </main>
      </div>

      {/* Command Palette */}
      {commandOpen && (
        <CommandPalette onClose={() => setCommandOpen(false)} />
      )}

      {/* Solomon AI Chat */}
      <SolomonChat />
    </div>
  );
}
