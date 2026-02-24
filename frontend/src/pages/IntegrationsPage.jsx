import { useState } from 'react';
import { 
  CreditCard, MessageSquare, Mail, Zap, Shield, Video, 
  Music, Calendar, Database, CheckCircle, Settings, ExternalLink,
  Globe, Smartphone, Bot, TrendingUp
} from 'lucide-react';
import { Button } from '@/components/ui/button';

const INTEGRATIONS = [
  {
    category: 'Payments & Giving',
    integrations: [
      {
        id: 'stripe',
        name: 'Stripe',
        description: 'Accept credit card, debit card, ACH, and Apple Pay donations with industry-leading security.',
        icon: CreditCard,
        color: '#635BFF',
        status: 'active',
        features: ['One-time gifts', 'Recurring donations', 'Apple Pay', 'ACH transfers'],
      },
      {
        id: 'paypal',
        name: 'PayPal',
        description: 'Enable PayPal payments for members who prefer this payment method.',
        icon: CreditCard,
        color: '#003087',
        status: 'coming_soon',
        features: ['PayPal checkout', 'Venmo', 'Pay Later options'],
      },
      {
        id: 'crypto',
        name: 'Crypto Donations',
        description: 'Accept Bitcoin, Ethereum, and other cryptocurrency donations.',
        icon: TrendingUp,
        color: '#F7931A',
        status: 'coming_soon',
        features: ['Bitcoin', 'Ethereum', 'Auto-conversion to USD'],
      },
    ],
  },
  {
    category: 'Communication',
    integrations: [
      {
        id: 'twilio',
        name: 'Twilio SMS',
        description: 'Send SMS messages to individuals or groups. Perfect for event reminders and urgent updates.',
        icon: MessageSquare,
        color: '#F22F46',
        status: 'active',
        features: ['Individual SMS', 'Bulk messaging', 'Templates', 'Delivery tracking'],
      },
      {
        id: 'resend',
        name: 'Resend Email',
        description: 'Beautiful transactional emails for giving receipts, event confirmations, and newsletters.',
        icon: Mail,
        color: '#000000',
        status: 'coming_soon',
        features: ['Transactional emails', 'Templates', 'Analytics', 'High deliverability'],
      },
      {
        id: 'whatsapp',
        name: 'WhatsApp Business',
        description: 'Reach members on WhatsApp for international or tech-savvy congregations.',
        icon: MessageSquare,
        color: '#25D366',
        status: 'coming_soon',
        features: ['WhatsApp messaging', 'Media sharing', 'Group broadcasts'],
      },
    ],
  },
  {
    category: 'Automation',
    integrations: [
      {
        id: 'zapier',
        name: 'Zapier',
        description: 'Connect Solomon AI to 5,000+ apps. Automate workflows without code.',
        icon: Zap,
        color: '#FF4A00',
        status: 'coming_soon',
        features: ['Triggers & actions', '5,000+ app connections', 'Multi-step Zaps'],
      },
      {
        id: 'webhooks',
        name: 'Webhooks',
        description: 'Real-time event notifications to your custom systems and applications.',
        icon: Database,
        color: '#3B82F6',
        status: 'active',
        features: ['Real-time events', 'Custom endpoints', 'Retry logic'],
      },
    ],
  },
  {
    category: 'Background Checks',
    integrations: [
      {
        id: 'checkr',
        name: 'Checkr',
        description: 'Industry-leading background checks for staff and volunteer screening.',
        icon: Shield,
        color: '#00BF6F',
        status: 'coming_soon',
        features: ['Criminal records', 'Sex offender registry', 'Motor vehicle records'],
      },
      {
        id: 'ministrysafe',
        name: 'MinistrySafe',
        description: 'Comprehensive child safety training and background screening.',
        icon: Shield,
        color: '#1E40AF',
        status: 'coming_soon',
        features: ['Training courses', 'Background checks', 'Compliance tracking'],
      },
    ],
  },
  {
    category: 'Video & Streaming',
    integrations: [
      {
        id: 'zoom',
        name: 'Zoom',
        description: 'Online services and virtual meetings with one-click join links.',
        icon: Video,
        color: '#2D8CFF',
        status: 'active',
        features: ['Meeting links', 'Webinars', 'Recording'],
      },
      {
        id: 'youtube',
        name: 'YouTube Live',
        description: 'Embed live streams and past services directly in your portal.',
        icon: Video,
        color: '#FF0000',
        status: 'coming_soon',
        features: ['Live streaming', 'Archive embedding', 'Analytics'],
      },
    ],
  },
  {
    category: 'Scheduling',
    integrations: [
      {
        id: 'calendly',
        name: 'Calendly',
        description: 'Easy appointment scheduling for pastoral meetings and counseling.',
        icon: Calendar,
        color: '#006BFF',
        status: 'active',
        features: ['Appointment booking', 'Calendar sync', 'Reminders'],
      },
      {
        id: 'google_calendar',
        name: 'Google Calendar',
        description: 'Sync church events with staff and member Google calendars.',
        icon: Calendar,
        color: '#4285F4',
        status: 'coming_soon',
        features: ['Two-way sync', 'Event sharing', 'Reminders'],
      },
    ],
  },
  {
    category: 'AI & Productivity',
    integrations: [
      {
        id: 'openai',
        name: 'AI Assistant',
        description: 'GPT-powered sermon notes, engagement scoring, and pastoral care suggestions.',
        icon: Bot,
        color: '#10A37F',
        status: 'coming_soon',
        features: ['Sermon summaries', 'Engagement scoring', 'Care recommendations'],
      },
      {
        id: 'slack',
        name: 'Slack',
        description: 'Notifications for staff on new members, donations, and important events.',
        icon: MessageSquare,
        color: '#4A154B',
        status: 'coming_soon',
        features: ['Notifications', 'Commands', 'Channel updates'],
      },
    ],
  },
];

export default function IntegrationsPage() {
  const [filter, setFilter] = useState('all'); // all, active, coming_soon

  const filteredIntegrations = INTEGRATIONS.map(category => ({
    ...category,
    integrations: category.integrations.filter(
      i => filter === 'all' || i.status === filter
    ),
  })).filter(c => c.integrations.length > 0);

  const activeCount = INTEGRATIONS.flatMap(c => c.integrations).filter(i => i.status === 'active').length;
  const totalCount = INTEGRATIONS.flatMap(c => c.integrations).length;

  return (
    <div className="space-y-4" data-testid="integrations-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Integrations</h1>
          <p className="page-subtitle">Connect Solomon AI to your favorite tools</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">{activeCount} of {totalCount} active</span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1.5 text-xs font-medium transition-colors ${
            filter === 'all'
              ? 'bg-blue-600 text-white'
              : 'bg-white text-slate-600 border border-slate-200 hover:border-slate-300'
          }`}
        >
          All ({totalCount})
        </button>
        <button
          onClick={() => setFilter('active')}
          className={`px-3 py-1.5 text-xs font-medium transition-colors ${
            filter === 'active'
              ? 'bg-blue-600 text-white'
              : 'bg-white text-slate-600 border border-slate-200 hover:border-slate-300'
          }`}
        >
          Active ({activeCount})
        </button>
        <button
          onClick={() => setFilter('coming_soon')}
          className={`px-3 py-1.5 text-xs font-medium transition-colors ${
            filter === 'coming_soon'
              ? 'bg-blue-600 text-white'
              : 'bg-white text-slate-600 border border-slate-200 hover:border-slate-300'
          }`}
        >
          Coming Soon ({totalCount - activeCount})
        </button>
      </div>

      {/* Integration Categories */}
      {filteredIntegrations.map((category) => (
        <div key={category.category} className="space-y-3">
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            {category.category}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {category.integrations.map((integration) => (
              <div
                key={integration.id}
                className="bg-white border border-slate-200 p-4 hover:border-blue-300 transition-colors"
                data-testid={`integration-${integration.id}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div 
                    className="w-10 h-10 flex items-center justify-center"
                    style={{ backgroundColor: `${integration.color}15` }}
                  >
                    <integration.icon 
                      className="w-5 h-5" 
                      style={{ color: integration.color }}
                    />
                  </div>
                  {integration.status === 'active' ? (
                    <span className="flex items-center gap-1 px-2 py-0.5 bg-green-50 text-green-700 text-xs font-medium">
                      <CheckCircle className="w-3 h-3" />
                      Active
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 bg-slate-100 text-slate-500 text-xs font-medium">
                      Coming Soon
                    </span>
                  )}
                </div>
                
                <h3 className="text-sm font-semibold text-slate-900">{integration.name}</h3>
                <p className="text-xs text-slate-500 mt-1 line-clamp-2">{integration.description}</p>
                
                <div className="flex flex-wrap gap-1 mt-3">
                  {integration.features.slice(0, 3).map((feature, idx) => (
                    <span 
                      key={idx}
                      className="px-1.5 py-0.5 bg-slate-100 text-slate-600 text-xs"
                    >
                      {feature}
                    </span>
                  ))}
                </div>
                
                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                  {integration.status === 'active' ? (
                    <>
                      <Button variant="outline" size="sm" className="btn-secondary text-xs">
                        <Settings className="w-3 h-3 mr-1" />
                        Configure
                      </Button>
                      <a 
                        href="#" 
                        className="text-xs text-blue-600 hover:underline flex items-center gap-1"
                      >
                        Docs <ExternalLink className="w-3 h-3" />
                      </a>
                    </>
                  ) : (
                    <Button disabled size="sm" className="w-full text-xs bg-slate-100 text-slate-400">
                      Coming Soon
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Request Integration */}
      <div className="bg-slate-50 border border-slate-200 p-6 text-center mt-8">
        <Globe className="w-8 h-8 text-slate-400 mx-auto mb-3" />
        <h3 className="text-sm font-semibold text-slate-700">Need a different integration?</h3>
        <p className="text-xs text-slate-500 mt-1">
          We're always adding new integrations. Let us know what you need.
        </p>
        <Button variant="outline" size="sm" className="mt-4 btn-secondary">
          Request Integration
        </Button>
      </div>
    </div>
  );
}
