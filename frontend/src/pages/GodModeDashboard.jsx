import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import {
  Globe, LayoutDashboard, ArrowLeftRight, Landmark, Users,
  DollarSign, Building2, Headphones, LogOut
} from 'lucide-react';

import PlatformExecDashboard from './platform/PlatformExecDashboard';
import PlatformTransactions from './platform/PlatformTransactions';
import PlatformPayouts from './platform/PlatformPayouts';
import PlatformDonors from './platform/PlatformDonors';
import PlatformRevenue from './platform/PlatformRevenue';
import PlatformChurches from './platform/PlatformChurches';
import PlatformSupport from './platform/PlatformSupport';

const TABS = [
  { id: 'exec', label: 'Executive', icon: LayoutDashboard },
  { id: 'transactions', label: 'Transactions', icon: ArrowLeftRight },
  { id: 'payouts', label: 'Payouts', icon: Landmark },
  { id: 'donors', label: 'Donors', icon: Users },
  { id: 'revenue', label: 'Revenue', icon: DollarSign },
  { id: 'churches', label: 'Churches', icon: Building2 },
  { id: 'support', label: 'Support', icon: Headphones },
];

export default function GodModeDashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('exec');
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const token = sessionStorage.getItem('session_token');

  const fetchStats = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/platform/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 403) {
        toast.error('Platform admin access required');
        navigate('/dashboard');
        return;
      }
      if (res.ok) setStats(await res.json());
    } catch (e) {
      console.error('Stats fetch failed:', e);
    } finally {
      setLoading(false);
    }
  }, [token, navigate]);

  useEffect(() => { fetchStats(); }, [fetchStats]);

  const handleImpersonate = (data) => {
    if (data?.user) {
      sessionStorage.setItem('impersonate_tenant', JSON.stringify(data));
      navigate('/dashboard');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]" data-testid="godmode-loading">
        <div className="text-center">
          <div className="w-10 h-10 border-3 border-slate-200 border-t-violet-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-slate-500">Loading God Mode...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="godmode-root" data-testid="godmode-dashboard">
      {/* God Mode Header */}
      <div className="godmode-header">
        <div className="flex items-center gap-3">
          <div className="godmode-icon">
            <Globe className="w-6 h-6" />
          </div>
          <div>
            <h1 className="godmode-title">Solomon AI — God Mode</h1>
            <p className="godmode-subtitle">Platform Admin Dashboard &middot; All churches, all data</p>
          </div>
        </div>
        <button
          onClick={() => navigate('/platform')}
          className="godmode-back-btn"
          title="Switch to the previous platform dashboard layout"
          data-testid="back-to-platform"
        >
          <LogOut className="w-4 h-4" />
          Previous Dashboard
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="godmode-tabs" data-testid="godmode-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`godmode-tab ${activeTab === tab.id ? 'active' : ''}`}
            data-testid={`godmode-tab-${tab.id}`}
          >
            <tab.icon className="w-4 h-4" />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Active Tab Content */}
      <div className="godmode-content" data-testid="godmode-content">
        {activeTab === 'exec' && <PlatformExecDashboard stats={stats} />}
        {activeTab === 'transactions' && <PlatformTransactions token={token} />}
        {activeTab === 'payouts' && <PlatformPayouts token={token} />}
        {activeTab === 'donors' && <PlatformDonors token={token} />}
        {activeTab === 'revenue' && <PlatformRevenue token={token} />}
        {activeTab === 'churches' && <PlatformChurches token={token} stats={stats} />}
        {activeTab === 'support' && <PlatformSupport token={token} onImpersonate={handleImpersonate} />}
      </div>
    </div>
  );
}
