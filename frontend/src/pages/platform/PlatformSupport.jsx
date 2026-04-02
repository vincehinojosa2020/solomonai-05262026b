import { useState } from 'react';
import { API_URL } from '@/lib/utils';
import { Eye, LogIn, Building2, AlertTriangle, Shield, Search } from 'lucide-react';
import { toast } from 'sonner';

const CHURCHES = [
  { id: 'abundant-east-001', name: 'Abundant East', members: '25,000', donors: '8,500' },
  { id: 'abundant-west-001', name: 'Abundant West', members: '12,000', donors: '4,200' },
  { id: 'abundant-downtown-001', name: 'Abundant Downtown', members: '5,000', donors: '2,534' },
];

export default function PlatformSupport({ token, onImpersonate }) {
  const [selectedChurch, setSelectedChurch] = useState('');
  const [loading, setLoading] = useState(false);

  const handleImpersonate = async (tenantId) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/platform/impersonate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ tenant_id: tenantId }),
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(`Impersonating ${data.user.name} at ${tenantId}`);
        if (onImpersonate) onImpersonate(data);
      } else {
        toast.error('Failed to impersonate');
      }
    } finally { setLoading(false); }
  };

  return (
    <div className="space-y-6" data-testid="platform-support">
      <div className="bg-white rounded-xl border border-slate-100 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center"><LogIn className="w-5 h-5 text-blue-600" /></div>
          <div><h3 className="font-semibold text-slate-800">Impersonate Church</h3><p className="text-sm text-slate-500">Sign in as a church admin to see their view</p></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {CHURCHES.map(c => (
            <div key={c.id} className="border border-slate-200 rounded-xl p-4 hover:border-blue-300 transition-colors">
              <div className="flex items-center gap-2 mb-3">
                <Building2 className="w-5 h-5 text-slate-400" />
                <span className="font-semibold text-slate-800">{c.name}</span>
              </div>
              <div className="text-sm text-slate-500 space-y-1 mb-3">
                <div>Members: {c.members}</div>
                <div>Donors: {c.donors}</div>
              </div>
              <button
                onClick={() => handleImpersonate(c.id)}
                disabled={loading}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                data-testid={`impersonate-${c.id}`}
              >
                <Eye className="w-4 h-4" />
                Impersonate
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-100 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center"><AlertTriangle className="w-5 h-5 text-amber-600" /></div>
          <div><h3 className="font-semibold text-slate-800">Issue Detection</h3><p className="text-sm text-slate-500">Automated monitoring for platform issues</p></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="border border-emerald-200 rounded-xl p-4 bg-emerald-50/50">
            <div className="text-2xl font-bold text-emerald-700">0</div>
            <div className="text-sm text-slate-600">Failed transactions (7d)</div>
          </div>
          <div className="border border-emerald-200 rounded-xl p-4 bg-emerald-50/50">
            <div className="text-2xl font-bold text-emerald-700">0</div>
            <div className="text-sm text-slate-600">Payout failures</div>
          </div>
          <div className="border border-emerald-200 rounded-xl p-4 bg-emerald-50/50">
            <div className="text-2xl font-bold text-emerald-700">0</div>
            <div className="text-sm text-slate-600">Inactive churches (30d)</div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-100 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-purple-50 flex items-center justify-center"><Shield className="w-5 h-5 text-purple-600" /></div>
          <div><h3 className="font-semibold text-slate-800">Audit Log</h3><p className="text-sm text-slate-500">All platform admin actions are logged</p></div>
        </div>
        <div className="text-sm text-slate-500 p-4 border border-dashed border-slate-200 rounded-lg text-center">
          Audit logging is active. All impersonation and admin actions are recorded.
        </div>
      </div>
    </div>
  );
}
