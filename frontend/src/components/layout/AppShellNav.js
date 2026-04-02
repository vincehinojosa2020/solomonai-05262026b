/**
 * AppShell navigation configuration — extracted for maintainability.
 */
import {
  LayoutDashboard, Users, Home, UsersRound, Calendar,
  CheckSquare, DollarSign, Mail, BarChart3, Settings,
  Search, Plug, Globe, Video, GraduationCap, BookOpen, ShoppingBag, Coffee, Code, Baby, Shield,
  Music, HandHeart, GitBranch, FileText, ListFilter, Merge, ClipboardList, CreditCard
} from 'lucide-react';

export const navItems = [
  { section: 'OVERVIEW', items: [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  ]},
  { section: 'PEOPLE', items: [
    { name: 'Members', path: '/people', icon: Users },
    { name: 'Households', path: '/households', icon: Home },
    { name: 'Workflows', path: '/workflows', icon: GitBranch },
    { name: 'Forms', path: '/forms', icon: FileText },
    { name: 'Smart Lists', path: '/smart-lists', icon: ListFilter },
    { name: 'Duplicates', path: '/people/duplicates', icon: Merge },
  ]},
  { section: 'MINISTRY', items: [
    { name: 'Services', path: '/services', icon: Music },
    { name: 'Song Library', path: '/songs', icon: Music },
    { name: 'Volunteers', path: '/volunteers', icon: HandHeart },
    { name: 'Courses', path: '/admin/courses', icon: GraduationCap },
    { name: 'Groups', path: '/admin/groups', icon: UsersRound },
    { name: 'Events', path: '/admin/events', icon: Calendar },
    { name: 'Registrations', path: '/registrations', icon: ClipboardList },
    { name: 'Approvals', path: '/calendar/approvals', icon: CheckSquare },
    { name: 'Kids Check-in', path: '/kids-checkin', icon: Baby },
    { name: 'Check-In Setup', path: '/checkin-setup', icon: Settings },
    { name: 'Attendance', path: '/attendance', icon: CheckSquare },
  ]},
  { section: 'STEWARDSHIP', items: [
    { name: 'Giving', path: '/giving', icon: DollarSign },
    { name: 'SolomonPay', path: '/solomonpay', icon: CreditCard, permission: 'admin.giving.view' },
  ]},
  { section: 'CONNECT', items: [
    { name: 'Communications', path: '/communications', icon: Mail },
    { name: 'Media Library', path: '/media', icon: Video },
    { name: 'Merch', path: '/merch', icon: ShoppingBag },
    { name: 'Cafe', path: '/cafe', icon: Coffee },
  ]},
  { section: 'ANALYTICS', items: [
    { name: 'Reports', path: '/reports', icon: BarChart3 },
    { name: 'Audit Log', path: '/audit-log', icon: Shield },
  ]},
  { section: 'ADMIN', items: [
    { name: 'Settings', path: '/settings', icon: Settings },
    { name: 'Integrations', path: '/integrations', icon: Plug },
    { name: 'Developer API', path: '/developer', icon: Code },
  ]},
];

export const platformNavItems = [
  { section: 'PLATFORM', items: [
    { name: 'All Churches', path: '/platform', icon: Globe },
  ]},
];
