import { useState, useEffect, useRef } from 'react';
import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { Home, DollarSign, Users, Calendar, User, Bell, BellRing, LogOut, Menu, X, Tv, GraduationCap, BookOpen, ShoppingBag, Coffee, MessageSquare, Heart, BookUser, ChevronDown } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { API_URL } from '@/lib/utils';
import SolomonChat from '@/components/SolomonChat';
import PWABottomNav from '@/components/PWABottomNav';
import { usePushNotifications } from '@/hooks/usePushNotifications';
import NotificationBell from '@/components/NotificationBell';
import DemoWalkthrough from '@/components/DemoWalkthrough';
import OnboardingFlow from '@/components/OnboardingFlow';
import CampusSelectorModal from '@/components/CampusSelectorModal';

export default function PortalLayout() {
  const [user, setUser] = useState(null);
  const [memberData, setMemberData] = useState(null);
  const [tenant, setTenant] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showCampusSelector, setShowCampusSelector] = useState(false);
  const [isPWA, setIsPWA] = useState(false);
  const { isSubscribed, isSupported, subscribe } = usePushNotifications();
  const location = useLocation();
  const navigate = useNavigate();
  
  // Check if we're on the Watch or Library page for dark mode
  const isDarkPage = location.pathname === '/portal/watch' || location.pathname === '/portal/library';
  
  // Library/Watch page has its own full navigation, so hide portal header
  const isLibraryPage = location.pathname === '/portal/watch' || location.pathname === '/portal/library';
  
  // Kids check-in page gets full-width treatment
  const isKidsPage = location.pathname === '/portal/kids';

  useEffect(() => {
    fetchMemberData();
    fetchTenant();
    // Detect standalone PWA mode
    setIsPWA(
      window.matchMedia('(display-mode: standalone)').matches ||
      window.navigator.standalone === true
    );
  }, []);

  const fetchTenant = async () => {
    try {
      const res = await fetch(`${API_URL}/tenant`);
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
      const token = sessionStorage.getItem('session_token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      const [meRes, profileRes] = await Promise.all([
        fetch(`${API_URL}/auth/me`, { headers }),
        fetch(`${API_URL}/portal/me`, { headers })
      ]);

      if (!meRes.ok) {
        navigate('/login');
        return;
      }

      const userData = await meRes.json();
      // Allow members and admins using Lyft dual-mode toggle
      // Only redirect if user has no member permissions at all
      if (userData.role === 'platform_admin' && !localStorage.getItem('portal_mode')) {
        navigate('/dashboard');
        return;
      }
      
      setUser(userData);
      
      // Show campus selector on first login for multi-campus churches
      if (!userData.campus_selected && !sessionStorage.getItem('campus_selector_shown')) {
        sessionStorage.setItem('campus_selector_shown', '1');
        setShowCampusSelector(true);
      }

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

  const navItems = [
    { name: 'Home', path: '/portal', icon: Home, exact: true },
    { name: 'Kids Check-in', path: '/portal/kids', icon: Users },
    { name: 'Give', path: '/portal/give', icon: DollarSign },
    { name: 'Groups', path: '/portal/groups', icon: Users },
    { name: 'Events', path: '/portal/events', icon: Calendar },
  ];

  const shopItems = [
    { name: 'Cafe', path: '/portal/cafe', icon: Coffee },
    { name: 'Merch', path: '/portal/merch', icon: ShoppingBag },
  ];

  const learnItems = [
    { name: 'Watch', path: '/portal/watch', icon: Tv },
    { name: 'Courses', path: '/portal/courses', icon: GraduationCap },
  ];

  const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  // Get church display name (simplified — strips campus suffix for multi-campus)
  const getChurchDisplayName = () => {
    if (tenant?.name) {
      const name = tenant.name;
      // For multi-campus: strip "East", "West", "Downtown" etc. to show parent brand
      const suffixes = [' East', ' West', ' Downtown', ' North', ' South', ' Central', ' Online', ' Living Faith Center', ' Church', ' Ministries'];
      for (const suffix of suffixes) {
        if (name.endsWith(suffix)) {
          return name.slice(0, -suffix.length).toUpperCase();
        }
      }
      return name.toUpperCase();
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
          {/* Logo - Dynamic church name, links to Home */}
          <NavLink to="/portal" className="portal-logo" data-testid="portal-logo" style={{ textDecoration: 'none' }}>
            <span 
              className="font-bold text-lg tracking-wide"
              style={{ color: tenant?.primary_color || '#2563eb' }}
            >
              {getChurchDisplayName()}
            </span>
          </NavLink>

          {/* Desktop Nav */}
          <nav className="portal-nav-desktop" data-testid="portal-nav">
            {navItems.filter(item => !item.exact).map((item) => (
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
            {/* Shop dropdown */}
            <div className="relative group">
              <button className="portal-nav-item flex items-center gap-1" data-testid="portal-nav-shop">
                Shop <ChevronDown className="w-3 h-3" />
              </button>
              <div className="absolute top-full left-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg py-1 opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto transition-opacity z-50 min-w-[140px]">
                {shopItems.map(item => (
                  <NavLink key={item.path} to={item.path} className="flex items-center gap-2 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50" data-testid={`portal-nav-${item.name.toLowerCase()}`}>
                    <item.icon className="w-4 h-4 text-slate-400" /> {item.name}
                  </NavLink>
                ))}
              </div>
            </div>
            {/* Learn dropdown */}
            <div className="relative group">
              <button className="portal-nav-item flex items-center gap-1" data-testid="portal-nav-learn">
                Learn <ChevronDown className="w-3 h-3" />
              </button>
              <div className="absolute top-full left-0 mt-1 bg-white border border-slate-200 rounded-lg shadow-lg py-1 opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto transition-opacity z-50 min-w-[140px]">
                {learnItems.map(item => (
                  <NavLink key={item.path} to={item.path} className="flex items-center gap-2 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50" data-testid={`portal-nav-${item.name.toLowerCase()}`}>
                    <item.icon className="w-4 h-4 text-slate-400" /> {item.name}
                  </NavLink>
                ))}
              </div>
            </div>
          </nav>

          {/* Right Actions */}
          <div className="portal-header-actions">
            {/* Mode Toggle — visible to admin users */}
            {user && (user.role === 'church_admin' || user.role === 'admin' || user.role === 'platform_admin' || (user.permissions && user.permissions.some(p => p.startsWith('admin.')))) && (
              <div className="flex items-center gap-1 bg-white/80 border border-slate-200 rounded-lg p-0.5" data-testid="portal-mode-toggle" style={{marginRight: 4}}>
                <button
                  className="px-3 py-1.5 text-xs font-semibold rounded-md transition-all text-slate-500 hover:text-slate-700"
                  onClick={() => navigate('/dashboard')}
                  data-testid="portal-mode-admin"
                >
                  Admin
                </button>
                <button
                  className="px-3 py-1.5 text-xs font-semibold rounded-md transition-all"
                  style={{ background: '#0f172a', color: 'white' }}
                  data-testid="portal-mode-member"
                >
                  Member
                </button>
              </div>
            )}
            <NotificationBell />
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
            {[...navItems, ...shopItems, ...learnItems, { name: 'Me', path: '/portal/me', icon: User }].map((item) => (
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
      <main className={`portal-main ${isDarkPage ? 'portal-main-dark' : ''} ${isKidsPage ? 'portal-main-kids' : ''} ${isPWA ? 'portal-main-pwa' : ''}`}>
        <div className={isDarkPage ? 'portal-content-full' : isKidsPage ? 'portal-content-kids' : 'portal-content'}>
          <Outlet context={{ user, memberData, tenant, refreshData: fetchMemberData }} />
        </div>
      </main>

      {/* PWA Bottom Navigation — only in standalone mode */}
      {isPWA && <PWABottomNav />}
      
      {/* Solomon AI Chat */}
      <SolomonChat />

      {/* Demo Walkthrough for first-time users */}
      <DemoWalkthrough 
        userRole={user?.role || 'member'} 
        userName={user?.name?.split(' ')[0] || 'there'}
        onNavigate={navigate}
      />
      {/* First Sign-In Onboarding */}
      <OnboardingFlow user={user} onComplete={fetchMemberData} />
      
      {/* Campus Selector — first login for multi-campus */}
      {showCampusSelector && (
        <CampusSelectorModal
          user={user}
          onSelect={(campus) => {
            setShowCampusSelector(false);
            setUser(prev => prev ? {...prev, home_campus_id: campus?.id, campus_selected: true} : prev);
          }}
          onSkip={() => setShowCampusSelector(false)}
        />
      )}
    </div>
  );
}
