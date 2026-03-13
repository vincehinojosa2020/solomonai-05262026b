import { NavLink, useLocation } from 'react-router-dom';
import { Home, Tv, DollarSign, Users, Calendar } from 'lucide-react';

const navItems = [
  { name: 'Home', path: '/portal', icon: Home, exact: true },
  { name: 'Watch', path: '/portal/watch', icon: Tv },
  { name: 'Give', path: '/portal/give', icon: DollarSign },
  { name: 'Groups', path: '/portal/groups', icon: Users },
  { name: 'Events', path: '/portal/events', icon: Calendar },
];

export default function PWABottomNav() {
  const location = useLocation();

  // Only show on portal routes
  if (!location.pathname.startsWith('/portal')) return null;

  // Hide on pages that have their own full nav (Watch/Library)
  if (location.pathname === '/portal/watch' || location.pathname === '/portal/library') return null;

  return (
    <nav data-testid="pwa-bottom-nav" className="pwa-bottom-nav">
      {navItems.map((item) => {
        const isActive = item.exact
          ? location.pathname === item.path
          : location.pathname.startsWith(item.path);
        return (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.exact}
            data-testid={`pwa-nav-${item.name.toLowerCase()}`}
            className={`pwa-bottom-nav-item ${isActive ? 'active' : ''}`}
          >
            <item.icon className="w-5 h-5" />
            <span>{item.name}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}
