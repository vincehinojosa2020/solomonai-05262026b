import { useState, useEffect } from 'react';
import { 
  CreditCard, MessageSquare, Mail, Zap, Shield, Video, 
  Music, Calendar, Database, CheckCircle, Settings, ExternalLink,
  Globe, Smartphone, Bot, TrendingUp, Link2, Unlink, Loader2, Circle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

const INTEGRATIONS = [
  {
    category: 'Communication',
    integrations: [
      { id: 'twilio', name: 'Twilio SMS', description: 'Send SMS messages to individuals or groups.', icon: MessageSquare, color: '#F22F46', status: 'active', features: ['Individual SMS', 'Bulk messaging', 'Templates'] },
      { id: 'resend', name: 'Resend Email', description: 'Transactional emails for receipts and newsletters.', icon: Mail, color: '#000000', status: 'coming_soon', features: ['Transactional emails', 'Templates', 'Analytics'] },
      { id: 'whatsapp', name: 'WhatsApp Business', description: 'Reach members on WhatsApp.', icon: MessageSquare, color: '#25D366', status: 'coming_soon', features: ['WhatsApp messaging', 'Media sharing'] },
    ],
  },
  {
    category: 'Automation',
    integrations: [
      { id: 'zapier', name: 'Zapier', description: 'Connect to 5,000+ apps.', icon: Zap, color: '#FF4A00', status: 'active', features: ['Automated workflows', '5000+ apps', 'Triggers & actions'] },
    ],
  },
  {
    category: 'Media',
    integrations: [
      { id: 'youtube', name: 'YouTube Live', description: 'Stream services and auto-embed.', icon: Video, color: '#FF0000', status: 'active', features: ['Live stream embed', 'Auto-archive', 'Sermon clips'] },
      { id: 'spotify', name: 'Spotify', description: 'Worship playlists for your church.', icon: Music, color: '#1DB954', status: 'coming_soon', features: ['Playlist embed', 'Worship sets'] },
    ],
  },
  {
    category: 'Scheduling',
    integrations: [
      { id: 'calendly', name: 'Calendly', description: 'Appointment scheduling for pastoral meetings.', icon: Calendar, color: '#006BFF', status: 'active', features: ['Appointments', 'Calendar sync'] },
      { id: 'google_calendar', name: 'Google Calendar', description: 'Sync church events with staff calendars.', icon: Calendar, color: '#4285F4', status: 'coming_soon', features: ['Two-way sync', 'Event sharing'] },
    ],
  },
  {
    category: 'AI & Productivity',
    integrations: [
      { id: 'openai', name: 'AI Assistant', description: 'GPT-powered sermon notes and engagement scoring.', icon: Bot, color: '#10A37F', status: 'coming_soon', features: ['Sermon summaries', 'Engagement scoring'] },
      { id: 'slack', name: 'Slack', description: 'Staff notifications for new members, donations, and events.', icon: MessageSquare, color: '#4A154B', status: 'coming_soon', features: ['Notifications', 'Commands'] },
    ],
  },
];

const PROCESSORS = [
  { id: 'solomon_pay', name: 'Solomon Pay', desc: 'Proprietary card, ACH, and Apple Pay processing', color: '#1e40af', icon: CreditCard },
  { id: 'pushpay', name: 'Pushpay', desc: 'Church-focused giving platform', color: '#48BB78', icon: CreditCard },
  { id: 'tithe_ly', name: 'Tithe.ly', desc: 'Digital giving for churches', color: '#2B6CB0', icon: CreditCard },
  { id: 'planning_center', name: 'Planning Center Giving', desc: 'Church Center ecosystem', color: '#667EEA', icon: Database },
  { id: 'subsplash', name: 'Subsplash Giving', desc: 'Mobile-first church giving', color: '#ED8936', icon: Smartphone },
  { id: 'manual', name: 'Manual / Cash & Check', desc: 'Record offline gifts manually', color: '#718096', icon: CreditCard },
];

export default function IntegrationsPage() {
  const [filter, setFilter] = useState('all');
  const [processorSettings, setProcessorSettings] = useState(null);
  const [connectingId, setConnectingId] = useState(null);

  useEffect(() => {
    fetchProcessorSettings();
  }, []);

  const fetchProcessorSettings = async () => {
    try {
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/admin/giving/processor-settings`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        setProcessorSettings(data);
      }
    } catch (err) { console.error('Failed to fetch processor settings:', err); }
  };

  const connectProcessor = async (processorId) => {
    setConnectingId(processorId);
    try {
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/admin/giving/processor-settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
        body: JSON.stringify({ processor_id: processorId, action: 'connect', config: { test_mode: true } })
      });
      if (res.ok) {
        const data = await res.json();
        setProcessorSettings(prev => ({ ...prev, active_processor: data.active_processor, processors: data.processors }));
        toast.success(`${PROCESSORS.find(p => p.id === processorId)?.name} connected and set as active`);
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to connect');
      }
    } catch (err) { toast.error('Network error'); }
    finally { setConnectingId(null); }
  };

  const disconnectProcessor = async (processorId) => {
    setConnectingId(processorId);
    try {
      const token = sessionStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/admin/giving/processor-settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
        body: JSON.stringify({ processor_id: processorId, action: 'disconnect' })
      });
      if (res.ok) {
        const data = await res.json();
        setProcessorSettings(prev => ({ ...prev, active_processor: data.active_processor, processors: data.processors }));
        toast.success(`${PROCESSORS.find(p => p.id === processorId)?.name} disconnected`);
      }
    } catch (err) { toast.error('Network error'); }
    finally { setConnectingId(null); }
  };

  const getProcessorStatus = (id) => {
    const procs = processorSettings?.processors || {};
    if (procs[id]?.enabled && procs[id]?.status === 'connected') return 'connected';
    return 'not_configured';
  };

  const isActive = (id) => processorSettings?.active_processor === id;

  const filteredIntegrations = INTEGRATIONS.map(category => ({
    ...category,
    integrations: category.integrations.filter(i => filter === 'all' || i.status === filter),
  })).filter(c => c.integrations.length > 0);

  const activeCount = INTEGRATIONS.flatMap(c => c.integrations).filter(i => i.status === 'active').length;
  const totalCount = INTEGRATIONS.flatMap(c => c.integrations).length;

  return (
    <div className="space-y-6" data-testid="integrations-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Integrations</h1>
          <p className="page-subtitle">Connect Solomon AI to your favorite tools and payment processors</p>
        </div>
      </div>

      {/* ===== GIVING & PAYMENTS ORCHESTRATION ===== */}
      <div className="space-y-4" data-testid="payment-orchestration">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Giving & Payments</h2>
            <p className="text-sm text-slate-500">Connect your church's payment processor. Solomon AI routes all giving through your configured provider.</p>
          </div>
          {processorSettings?.active_processor && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 border border-green-200 rounded-lg">
              <Circle className="w-2 h-2 fill-green-500 text-green-500" />
              <span className="text-xs font-medium text-green-700">
                Active: {PROCESSORS.find(p => p.id === processorSettings.active_processor)?.name || processorSettings.active_processor}
              </span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {PROCESSORS.map((proc) => {
            const status = getProcessorStatus(proc.id);
            const active = isActive(proc.id);
            const connecting = connectingId === proc.id;

            return (
              <div
                key={proc.id}
                className={`bg-white border rounded-xl p-4 transition-all ${active ? 'border-green-300 ring-1 ring-green-100' : status === 'connected' ? 'border-blue-200' : 'border-slate-200 hover:border-slate-300'}`}
                data-testid={`processor-${proc.id}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${proc.color}12` }}>
                    <proc.icon className="w-5 h-5" style={{ color: proc.color }} />
                  </div>
                  {active ? (
                    <span className="flex items-center gap-1 px-2 py-0.5 bg-green-50 text-green-700 text-xs font-semibold rounded-full" data-testid={`processor-status-${proc.id}`}>
                      <CheckCircle className="w-3 h-3" /> Active
                    </span>
                  ) : status === 'connected' ? (
                    <span className="flex items-center gap-1 px-2 py-0.5 bg-blue-50 text-blue-700 text-xs font-medium rounded-full" data-testid={`processor-status-${proc.id}`}>
                      <Link2 className="w-3 h-3" /> Connected
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 bg-slate-100 text-slate-500 text-xs font-medium rounded-full" data-testid={`processor-status-${proc.id}`}>
                      Not configured
                    </span>
                  )}
                </div>

                <h3 className="text-sm font-semibold text-slate-900">{proc.name}</h3>
                <p className="text-xs text-slate-500 mt-1">{proc.desc}</p>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-2">
                  {status === 'connected' ? (
                    <>
                      {!active && (
                        <Button size="sm" className="text-xs flex-1" onClick={() => connectProcessor(proc.id)} disabled={connecting}>
                          {connecting ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : null}
                          Set as Active
                        </Button>
                      )}
                      {proc.id !== 'manual' && (
                        <Button variant="outline" size="sm" className="text-xs" onClick={() => disconnectProcessor(proc.id)} disabled={connecting}>
                          <Unlink className="w-3 h-3 mr-1" /> Disconnect
                        </Button>
                      )}
                      {active && <span className="text-xs text-green-600 font-medium">Primary processor</span>}
                    </>
                  ) : (
                    <Button size="sm" className="text-xs w-full" onClick={() => connectProcessor(proc.id)} disabled={connecting}>
                      {connecting ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Link2 className="w-3 h-3 mr-1" />}
                      Connect {proc.name}
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <p className="text-sm text-blue-800">
            <strong>How it works:</strong> Solomon AI acts as an orchestration layer. When a member gives, the donation is routed through your active payment processor. All processors return standardized transaction data, making it easy to switch providers without losing history.
          </p>
          <p className="text-xs text-blue-600 mt-2">
            Solomon AI will become its own payment processor in the future. For now, connect an external provider or use Manual mode for cash & check.
          </p>
        </div>
      </div>

      {/* Divider */}
      <hr className="border-slate-200" />

      {/* ===== EXISTING INTEGRATIONS ===== */}
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-slate-900">Other Integrations</h2>
        <div className="flex items-center gap-2">
          {['all', 'active', 'coming_soon'].map(f => (
            <button key={f} onClick={() => setFilter(f)} className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${filter === f ? 'bg-blue-600 text-white' : 'bg-white text-slate-600 border border-slate-200 hover:border-slate-300'}`}>
              {f === 'all' ? `All (${totalCount})` : f === 'active' ? `Active (${activeCount})` : `Coming Soon (${totalCount - activeCount})`}
            </button>
          ))}
        </div>
      </div>

      {filteredIntegrations.map((category) => (
        <div key={category.category} className="space-y-3">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{category.category}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {category.integrations.map((integration) => (
              <div key={integration.id} className="bg-white border border-slate-200 rounded-xl p-4 hover:border-blue-300 transition-colors" data-testid={`integration-${integration.id}`}>
                <div className="flex items-start justify-between mb-3">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${integration.color}12` }}>
                    <integration.icon className="w-5 h-5" style={{ color: integration.color }} />
                  </div>
                  {integration.status === 'active' ? (
                    <span className="flex items-center gap-1 px-2 py-0.5 bg-green-50 text-green-700 text-xs font-medium rounded-full">
                      <CheckCircle className="w-3 h-3" /> Active
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 bg-slate-100 text-slate-500 text-xs font-medium rounded-full">Coming Soon</span>
                  )}
                </div>
                <h3 className="text-sm font-semibold text-slate-900">{integration.name}</h3>
                <p className="text-xs text-slate-500 mt-1">{integration.description}</p>
                <div className="flex flex-wrap gap-1 mt-3">
                  {integration.features.slice(0, 3).map((f, i) => <span key={i} className="px-1.5 py-0.5 bg-slate-100 text-slate-600 text-xs rounded">{f}</span>)}
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100">
                  {integration.status === 'active' ? (
                    <div className="flex items-center justify-between">
                      <Button variant="outline" size="sm" className="text-xs"><Settings className="w-3 h-3 mr-1" />Configure</Button>
                      <a href="#" className="text-xs text-blue-600 hover:underline flex items-center gap-1">Docs <ExternalLink className="w-3 h-3" /></a>
                    </div>
                  ) : (
                    <Button disabled size="sm" className="w-full text-xs">Coming Soon</Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      <div className="bg-slate-50 border border-slate-200 rounded-xl p-6 text-center">
        <Globe className="w-8 h-8 text-slate-400 mx-auto mb-3" />
        <h3 className="text-sm font-semibold text-slate-700">Need a different integration?</h3>
        <p className="text-xs text-slate-500 mt-1">We're always adding new integrations. Let us know what you need.</p>
        <Button variant="outline" size="sm" className="mt-4">Request Integration</Button>
      </div>
    </div>
  );
}
