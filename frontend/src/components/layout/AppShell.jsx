import { useState, useEffect } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, Users, Home, UsersRound, Calendar, 
  CheckSquare, DollarSign, Mail, BarChart3, Settings, 
  Building2, Search, Bell, ChevronLeft, Menu, Command
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
import { API_URL } from '@/lib/utils';

const navItems = [
  { section: 'OVERVIEW', items: [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  ]},
  { section: 'PEOPLE', items: [
    { name: 'Members', path: '/people', icon: Users },
    { name: 'Households', path: '/households', icon: Home },
  ]},
  { section: 'MINISTRY', items: [
    { name: 'Groups', path: '/groups', icon: UsersRound },
    { name: 'Events', path: '/events', icon: Calendar },
    { name: 'Attendance', path: '/attendance', icon: CheckSquare },
  ]},
  { section: 'STEWARDSHIP', items: [
    { name: 'Giving', path: '/giving', icon: DollarSign },
  ]},
  { section: 'CONNECT', items: [
    { name: 'Communications', path: '/communications', icon: Mail },
  ]},
  { section: 'ANALYTICS', items: [
    { name: 'Reports', path: '/reports', icon: BarChart3 },
  ]},
  { section: 'ADMIN', items: [
    { name: 'Settings', path: '/settings', icon: Settings },
  ]},
];

export default function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [tenant, setTenant] = useState(null);
  const location = useLocation();

  useEffect(() => {
    fetch(`${API_URL}/tenant`)
      .then(res => res.json())
      .then(data => setTenant(data))
      .catch(err => console.error('Failed to fetch tenant:', err));
  }, []);

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
        <div className="flex items-center justify-between h-14 px-4 border-b border-white/10">
          {!collapsed && (
            <span className="logo-text" data-testid="app-logo">
              SAMS<span className="logo-accent">O</span>N
            </span>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-2 rounded text-white/50 hover:text-white hover:bg-white/10 transition-colors"
            data-testid="sidebar-toggle"
          >
            {collapsed ? <Menu className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-3 scrollbar-thin">
          {navItems.map((section, idx) => (
            <div key={idx} className="nav-section">
              {!collapsed && (
                <div className="nav-section-label">{section.section}</div>
              )}
              {section.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => 
                    `nav-item ${isActive ? 'active' : ''}`
                  }
                  data-testid={`nav-${item.name.toLowerCase()}`}
                  title={collapsed ? item.name : undefined}
                >
                  <item.icon className="icon" />
                  {!collapsed && <span>{item.name}</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        {/* User Section */}
        {!collapsed && (
          <div className="p-4 border-t border-white/10">
            <div className="flex items-center gap-3">
              <Avatar className="w-8 h-8">
                <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=admin" />
                <AvatarFallback className="bg-[#2d7a6b] text-white text-xs font-medium">AD</AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">Admin User</p>
                <p className="text-xs text-white/50 truncate">admin@abundant.org</p>
              </div>
            </div>
          </div>
        )}
      </aside>

      {/* Main Content */}
      <div className="app-main">
        {/* Top Bar */}
        <header className="app-topbar" data-testid="app-topbar">
          <div className="flex items-center gap-4">
            {collapsed && (
              <span className="logo-text" style={{ color: '#1a1a1a' }}>
                SAMS<span style={{ color: '#2d7a6b' }}>O</span>N
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
            <span className="flex-1 text-left text-[#8a8a8a] text-sm">Search...</span>
            <span className="kbd">
              <Command className="w-3 h-3" />
              <span>K</span>
            </span>
          </button>

          {/* Right Actions */}
          <div className="flex items-center gap-3">
            {/* Notifications */}
            <button 
              className="relative p-2 rounded text-[#8a8a8a] hover:text-[#2d7a6b] hover:bg-[#f7f7f5] transition-colors"
              data-testid="notifications-btn"
            >
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#2d7a6b] rounded-full"></span>
            </button>

            {/* Tenant Badge */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-[#f7f7f5] border border-[#e8e8e5]">
              <Building2 className="w-4 h-4 text-[#8a8a8a]" />
              <span className="text-sm font-medium text-[#4a4a4a]">
                {tenant?.name || 'Abundant Church'}
              </span>
            </div>

            {/* User Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center gap-2" data-testid="user-menu-btn">
                  <Avatar className="w-8 h-8">
                    <AvatarImage src="https://api.dicebear.com/7.x/avataaars/svg?seed=admin" />
                    <AvatarFallback className="bg-[#2d7a6b] text-white text-xs">AD</AvatarFallback>
                  </Avatar>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuLabel>My Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem>Profile</DropdownMenuItem>
                <DropdownMenuItem>Settings</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem>Log out</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Page Content */}
        <main className="app-content">
          <Outlet context={{ tenant, greeting: getGreeting() }} />
        </main>
      </div>

      {/* Command Palette */}
      {commandOpen && (
        <CommandPalette onClose={() => setCommandOpen(false)} />
      )}
    </div>
  );
}
