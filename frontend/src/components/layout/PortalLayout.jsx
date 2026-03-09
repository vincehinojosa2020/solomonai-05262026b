import { useState, useEffect } from 'react';
import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { Home, DollarSign, Users, Calendar, User, Bell, LogOut, Menu, X, Tv, GraduationCap, BookOpen, ShoppingBag, Coffee, MessageSquare } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { API_URL } from '@/lib/utils';
import SolomonChat from '@/components/SolomonChat';

export default function PortalLayout() {
  const [user, setUser] = useState(null);
  const [memberData, setMemberData] = useState(null);
  const [tenant, setTenant] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  
  // Check if we're on the Watch or Library page for dark mode
  const isDarkPage = location.pathname === '/portal/watch' || location.pathname === '/portal/library';
  
  // Library/Watch page has its own full navigation, so hide portal header
  const isLibraryPage = location.pathname === '/portal/watch' || location.pathname === '/portal/library';

  useEffect(() => {
    fetchMemberData();
    fetchTenant();
  }, []);

  const fetchTenant = async () => {
    try {
      const res = await fetch(`${API_URL}/tenant`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setTenant(data);
      }
    } catch (error) {
      console.error('Failed to fetch tenant:', error);
    }
  };

  const fetchMemberData = async () => {
    try {
      const [meRes, profileRes] = await Promise.all([
        fetch(`${API_URL}/auth/me`, { credentials: 'include' }),
        fetch(`${API_URL}/portal/me`, { credentials: 'include' })
      ]);

      if (!meRes.ok) {
        navigate('/login');
        return;
      }

      const userData = await meRes.json();
      // Only members can access portal
      if (userData.role !== 'member') {
        navigate('/dashboard');
        return;
      }
      
      setUser(userData);

      if (profileRes.ok) {
        const profileData = await profileRes.json();
        setMemberData(profileData);
      }
    } catch (error) {
      console.error('Failed to fetch member data:', error);
      navigate('/login');
    }
  };

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

  const navItems = [
    { name: 'Home', path: '/portal', icon: Home, exact: true },
    { name: 'Watch', path: '/portal/watch', icon: Tv },
    { name: 'Merch', path: '/portal/merch', icon: ShoppingBag },
    { name: 'Cafe', path: '/portal/cafe', icon: Coffee },
    { name: 'Meet', path: '/portal/meetings', icon: MessageSquare },
    { name: 'Give', path: '/portal/give', icon: DollarSign },
    { name: 'Groups', path: '/portal/groups', icon: Users },
    { name: 'Events', path: '/portal/events', icon: Calendar },
    { name: 'Me', path: '/portal/me', icon: User },
  ];

  const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  // Get church display name (simplified)
  const getChurchDisplayName = () => {
    if (tenant?.name) {
      // Shorten common church name patterns
      const name = tenant.name
        .replace(' Living Faith Center', '')
        .replace(' Church', '')
        .replace(' Ministries', '')
        .toUpperCase();
      return name;
    }
    return 'ABUNDANT';
  };

  if (!user) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${isDarkPage ? 'bg-black' : 'bg-[#f7f6f3]'}`}>
        <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className={`portal-layout ${isDarkPage ? 'portal-dark-mode' : ''}`}>
      {/* Top Navigation - Hidden on Library page which has its own nav */}
      {!isLibraryPage && (
        <header className={`portal-header ${isDarkPage ? 'portal-header-dark' : ''}`}>
        <div className="portal-header-content">
          {/* Logo - Dynamic church name */}
          <div className="portal-logo" data-testid="portal-logo">
            <span 
              className="font-bold text-lg tracking-wide"
              style={{ color: tenant?.primary_color || '#2563eb' }}
            >
              {getChurchDisplayName()}
            </span>
          </div>

          {/* Desktop Nav */}
          <nav className="portal-nav-desktop" data-testid="portal-nav">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.exact}
                data-testid={`portal-nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                className={({ isActive }) => 
                  `portal-nav-item ${isActive ? 'active' : ''}`
                }
              >
                {item.name}
              </NavLink>
            ))}
          </nav>

          {/* Right Actions */}
          <div className="portal-header-actions">
            <button className="portal-notification-btn" data-testid="portal-notifications">
              <Bell className="w-5 h-5" />
            </button>
            <Avatar className="w-8 h-8 cursor-pointer" onClick={() => navigate('/portal/me')} data-testid="portal-avatar">
              <AvatarImage src={user?.picture} />
              <AvatarFallback className="bg-teal-500 text-white text-xs font-semibold">
                {getInitials(user?.name)}
              </AvatarFallback>
            </Avatar>
            <button 
              className="portal-logout-btn hidden md:flex"
              onClick={handleLogout}
              data-testid="portal-logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
            
            {/* Mobile Menu Toggle */}
            <button 
              className="portal-mobile-toggle md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="portal-mobile-menu md:hidden">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.exact}
                onClick={() => setMobileMenuOpen(false)}
                data-testid={`portal-mobile-nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                className={({ isActive }) => 
                  `portal-mobile-nav-item ${isActive ? 'active' : ''}`
                }
              >
                <item.icon className="w-5 h-5" />
                {item.name}
              </NavLink>
            ))}
            <button 
              className="portal-mobile-nav-item text-red-600"
              onClick={handleLogout}
            >
              <LogOut className="w-5 h-5" />
              Sign Out
            </button>
          </div>
        )}
      </header>
      )}

      {/* Main Content */}
      <main className={`portal-main ${isDarkPage ? 'portal-main-dark' : ''}`}>
        <div className={isDarkPage ? 'portal-content-full' : 'portal-content'}>
          <Outlet context={{ user, memberData, tenant, refreshData: fetchMemberData }} />
        </div>
      </main>

      {/* Mobile Bottom Nav - Hidden on Library page */}
      {!isLibraryPage && (
        <nav className={`portal-bottom-nav md:hidden ${isDarkPage ? 'portal-bottom-nav-dark' : ''}`} data-testid="portal-bottom-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.exact}
              data-testid={`portal-bottom-nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
              className={({ isActive }) => 
                `portal-bottom-nav-item ${isActive ? 'active' : ''}`
              }
            >
              <item.icon className="w-5 h-5" />
              <span>{item.name}</span>
            </NavLink>
          ))}
        </nav>
      )}

      {/* Solomon AI Chat */}
      <SolomonChat />
    </div>
  );
}
