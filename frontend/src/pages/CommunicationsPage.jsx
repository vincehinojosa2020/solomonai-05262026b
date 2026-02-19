import { useState, useEffect } from 'react';
import { Mail, Plus, Send, FileText, Users, Clock, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { API_URL, formatDate } from '@/lib/utils';
import SMSComposer from '@/components/modals/SMSComposer';

export default function CommunicationsPage() {
  const [communications, setCommunications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('compose');
  const [showSMSComposer, setShowSMSComposer] = useState(false);
  const [composeData, setComposeData] = useState({
    subject: '',
    body_html: '',
    recipients: [],
  });

  useEffect(() => {
    fetchCommunications();
  }, []);

  const fetchCommunications = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/communications`);
      const data = await response.json();
      setCommunications(data);
    } catch (error) {
      console.error('Failed to fetch communications:', error);
    } finally {
      setLoading(false);
    }
  };

  const templates = [
    { id: 1, name: 'Welcome Email', description: 'Send to new visitors' },
    { id: 2, name: 'Prayer Request Follow-up', description: 'Pastoral care response' },
    { id: 3, name: 'Event Invitation', description: 'Promote upcoming events' },
    { id: 4, name: 'Giving Statement', description: 'Annual contribution summary' },
  ];

  const segments = [
    { id: 1, name: 'All Active Members', count: 4287 },
    { id: 2, name: 'New This Month', count: 127 },
    { id: 3, name: 'Inactive 90+ Days', count: 47 },
    { id: 4, name: 'Group Leaders', count: 84 },
    { id: 5, name: 'Recurring Givers', count: 30 },
    { id: 6, name: 'Upcoming Birthdays', count: 156 },
  ];

  return (
    <div className="space-y-4" data-testid="communications-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Communications</h1>
          <p className="page-subtitle">Email and SMS messaging</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => setShowSMSComposer(true)} className="btn-secondary" data-testid="sms-btn">
            <MessageSquare className="w-4 h-4 mr-1" />
            Send SMS
          </Button>
          <Button className="btn-primary" data-testid="compose-email-btn">
            <Mail className="w-4 h-4 mr-1" />
            New Email
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-white border border-slate-200 p-1">
          <TabsTrigger value="compose" data-testid="tab-compose">Compose</TabsTrigger>
          <TabsTrigger value="sent" data-testid="tab-sent">Sent</TabsTrigger>
          <TabsTrigger value="sms" data-testid="tab-sms">SMS</TabsTrigger>
          <TabsTrigger value="templates" data-testid="tab-templates">Templates</TabsTrigger>
          <TabsTrigger value="segments" data-testid="tab-segments">Segments</TabsTrigger>
        </TabsList>

        {/* Compose Tab */}
        <TabsContent value="compose" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Compose Form */}
            <div className="bg-white border border-slate-200 p-4 space-y-4">
              <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">New Email</h3>
              
              <div className="form-group">
                <Label className="form-label">To</Label>
                <Input 
                  placeholder="Search members, groups, or select a segment..." 
                  className="form-input"
                  data-testid="recipients-input"
                />
                <p className="text-xs text-slate-400 mt-1">
                  Start typing to search, or select from segments →
                </p>
              </div>

              <div className="form-group">
                <Label className="form-label">Subject</Label>
                <Input 
                  placeholder="Enter email subject..."
                  className="form-input"
                  value={composeData.subject}
                  onChange={(e) => setComposeData({ ...composeData, subject: e.target.value })}
                  data-testid="subject-input"
                />
              </div>

              <div className="form-group">
                <Label className="form-label">Message</Label>
                <Textarea 
                  placeholder="Write your message... Use {first_name} for personalization."
                  className="form-input min-h-[160px] resize-none"
                  value={composeData.body_html}
                  onChange={(e) => setComposeData({ ...composeData, body_html: e.target.value })}
                  data-testid="body-input"
                />
                <p className="text-xs text-slate-400 mt-1">
                  Merge fields: {'{first_name}'}, {'{last_name}'}, {'{giving_ytd}'}
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Button variant="outline" className="btn-secondary" data-testid="save-draft-btn">Save Draft</Button>
                <Button variant="outline" className="btn-secondary" data-testid="preview-btn">Preview</Button>
                <Button className="btn-primary" data-testid="send-btn">
                  <Send className="w-4 h-4 mr-1" />
                  Send Now
                </Button>
              </div>
            </div>

            {/* Quick Segments */}
            <div className="space-y-4">
              <div className="bg-white border border-slate-200 p-4">
                <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-3">Quick Send Segments</h3>
                <div className="space-y-1">
                  {segments.map((segment) => (
                    <button
                      key={segment.id}
                      className="w-full p-2.5 text-left border border-slate-200 hover:border-blue-300 hover:bg-slate-50 transition-colors"
                      data-testid={`segment-${segment.id}`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-slate-700">{segment.name}</span>
                        <span className="text-xs text-slate-500 font-mono">{segment.count.toLocaleString()}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="bg-white border border-slate-200 p-4">
                <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-3">Quick Templates</h3>
                <div className="space-y-1">
                  {templates.slice(0, 3).map((template) => (
                    <button
                      key={template.id}
                      className="w-full p-2.5 text-left border border-slate-200 hover:border-blue-300 hover:bg-slate-50 transition-colors"
                    >
                      <p className="text-sm font-medium text-slate-700">{template.name}</p>
                      <p className="text-xs text-slate-500">{template.description}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Sent Tab */}
        <TabsContent value="sent">
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Subject</th>
                  <th>Status</th>
                  <th>Recipients</th>
                  <th>Sent</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={4} className="text-center py-8 text-slate-400">
                      Loading...
                    </td>
                  </tr>
                ) : communications.filter(c => c.status !== 'template').length === 0 ? (
                  <tr>
                    <td colSpan={4} className="text-center py-12 text-slate-400">
                      No emails sent yet
                    </td>
                  </tr>
                ) : (
                  communications.filter(c => c.status !== 'template').map((comm) => (
                    <tr key={comm.id}>
                      <td className="font-medium text-slate-700">{comm.subject}</td>
                      <td>
                        <span className={`badge ${
                          comm.status === 'sent' ? 'badge-active' :
                          comm.status === 'draft' ? 'badge-pending' :
                          'badge-inactive'
                        }`}>
                          {comm.status.charAt(0).toUpperCase() + comm.status.slice(1)}
                        </span>
                      </td>
                      <td className="font-mono text-sm">{comm.recipient_count}</td>
                      <td className="text-slate-500">{comm.sent_at ? formatDate(comm.sent_at) : '—'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </TabsContent>

        {/* SMS Tab */}
        <TabsContent value="sms">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* SMS Stats */}
            <div className="bg-white border border-slate-200 p-4">
              <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">SMS Overview</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-slate-50 border border-slate-200">
                  <p className="text-2xl font-mono font-semibold text-slate-900">0</p>
                  <p className="text-xs text-slate-500">Messages Sent (MTD)</p>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200">
                  <p className="text-2xl font-mono font-semibold text-slate-900">98%</p>
                  <p className="text-xs text-slate-500">Delivery Rate</p>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200">
                  <p className="text-2xl font-mono font-semibold text-slate-900">4</p>
                  <p className="text-xs text-slate-500">Templates</p>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200">
                  <p className="text-2xl font-mono font-semibold text-slate-900">$0.00</p>
                  <p className="text-xs text-slate-500">Cost (MTD)</p>
                </div>
              </div>
              
              <Button 
                onClick={() => setShowSMSComposer(true)} 
                className="btn-primary w-full mt-4"
              >
                <MessageSquare className="w-4 h-4 mr-2" />
                Compose SMS
              </Button>
            </div>

            {/* Recent SMS */}
            <div className="bg-white border border-slate-200 p-4">
              <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">Recent SMS Activity</h3>
              <div className="text-center py-12 text-slate-400">
                <MessageSquare className="w-10 h-10 mx-auto mb-3 opacity-50" />
                <p className="text-sm">No SMS messages sent yet</p>
                <p className="text-xs mt-1">Configure Twilio to enable SMS</p>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {templates.map((template) => (
              <div 
                key={template.id}
                className="bg-white border border-slate-200 p-4 hover:border-blue-300 transition-colors"
              >
                <FileText className="w-6 h-6 text-blue-500 mb-2" />
                <h3 className="text-sm font-semibold text-slate-700">{template.name}</h3>
                <p className="text-xs text-slate-500 mt-1">{template.description}</p>
                <Button variant="outline" size="sm" className="mt-3 btn-secondary text-xs">
                  Use Template
                </Button>
              </div>
            ))}
            <button className="border border-dashed border-slate-300 p-4 hover:border-slate-400 transition-colors text-center">
              <Plus className="w-6 h-6 text-slate-400 mx-auto mb-2" />
              <p className="text-xs font-medium text-slate-600">Create Template</p>
            </button>
          </div>
        </TabsContent>

        {/* Segments Tab */}
        <TabsContent value="segments">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {segments.map((segment) => (
              <div 
                key={segment.id}
                className="bg-white border border-slate-200 p-4 hover:border-blue-300 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <Users className="w-5 h-5 text-blue-500" />
                  <span className="text-xl font-mono font-semibold text-slate-900">
                    {segment.count.toLocaleString()}
                  </span>
                </div>
                <h3 className="text-sm font-semibold text-slate-700">{segment.name}</h3>
                <div className="flex items-center gap-2 mt-3">
                  <Button variant="outline" size="sm" className="btn-secondary text-xs flex-1">View</Button>
                  <Button size="sm" className="btn-primary text-xs flex-1">
                    <Mail className="w-3 h-3 mr-1" />
                    Email
                  </Button>
                </div>
              </div>
            ))}
            <button className="border border-dashed border-slate-300 p-4 hover:border-slate-400 transition-colors text-center">
              <Plus className="w-6 h-6 text-slate-400 mx-auto mb-2" />
              <p className="text-xs font-medium text-slate-600">Create Segment</p>
            </button>
          </div>
        </TabsContent>
      </Tabs>

      {/* SMS Composer Modal */}
      {showSMSComposer && (
        <SMSComposer onClose={() => setShowSMSComposer(false)} />
      )}
    </div>
  );
}
