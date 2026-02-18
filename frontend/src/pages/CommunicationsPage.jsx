import { useState, useEffect } from 'react';
import { Mail, Plus, Send, FileText, Users, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { API_URL, formatDate } from '@/lib/utils';

export default function CommunicationsPage() {
  const [communications, setCommunications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('compose');
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
    <div className="space-y-6 animate-fade-in" data-testid="communications-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Communications</h1>
          <p className="page-subtitle">Send emails and manage templates</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-white border border-slate-200 p-1">
          <TabsTrigger value="compose" data-testid="tab-compose">Compose</TabsTrigger>
          <TabsTrigger value="sent" data-testid="tab-sent">Sent</TabsTrigger>
          <TabsTrigger value="templates" data-testid="tab-templates">Templates</TabsTrigger>
          <TabsTrigger value="segments" data-testid="tab-segments">Segments</TabsTrigger>
        </TabsList>

        {/* Compose Tab */}
        <TabsContent value="compose" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Compose Form */}
            <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-5">
              <h3 className="font-semibold text-slate-900">New Email</h3>
              
              <div className="form-group">
                <Label className="form-label">To</Label>
                <Input 
                  placeholder="Search members, groups, or select a segment..." 
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
                  value={composeData.subject}
                  onChange={(e) => setComposeData({ ...composeData, subject: e.target.value })}
                  data-testid="subject-input"
                />
              </div>

              <div className="form-group">
                <Label className="form-label">Message</Label>
                <Textarea 
                  placeholder="Write your message... Use {first_name} for personalization."
                  className="min-h-[200px]"
                  value={composeData.body_html}
                  onChange={(e) => setComposeData({ ...composeData, body_html: e.target.value })}
                  data-testid="body-input"
                />
                <p className="text-xs text-slate-400 mt-1">
                  Available merge fields: {'{first_name}'}, {'{last_name}'}, {'{giving_ytd}'}
                </p>
              </div>

              <div className="flex items-center gap-3">
                <Button variant="outline" data-testid="save-draft-btn">Save as Draft</Button>
                <Button variant="outline" data-testid="preview-btn">Preview</Button>
                <Button className="btn-primary" data-testid="send-btn">
                  <Send className="w-4 h-4 mr-2" />
                  Send Now
                </Button>
              </div>
            </div>

            {/* Quick Segments */}
            <div className="space-y-4">
              <div className="bg-white border border-slate-200 rounded-lg p-5">
                <h3 className="font-semibold text-slate-900 mb-4">Quick Send Segments</h3>
                <div className="space-y-2">
                  {segments.map((segment) => (
                    <button
                      key={segment.id}
                      className="w-full p-3 text-left border border-slate-200 rounded-lg hover:border-blue-200 hover:bg-blue-50/50 transition-colors"
                      data-testid={`segment-${segment.id}`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-slate-900">{segment.name}</span>
                        <span className="text-sm text-slate-500 font-data">{segment.count.toLocaleString()}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="bg-white border border-slate-200 rounded-lg p-5">
                <h3 className="font-semibold text-slate-900 mb-4">Quick Templates</h3>
                <div className="space-y-2">
                  {templates.slice(0, 3).map((template) => (
                    <button
                      key={template.id}
                      className="w-full p-3 text-left border border-slate-200 rounded-lg hover:border-blue-200 hover:bg-blue-50/50 transition-colors"
                    >
                      <p className="font-medium text-slate-900">{template.name}</p>
                      <p className="text-sm text-slate-500">{template.description}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Sent Tab */}
        <TabsContent value="sent">
          <div className="bg-white border border-slate-200 rounded-lg">
            <div className="overflow-x-auto">
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
                      <td colSpan={4} className="text-center py-8">
                        <div className="animate-pulse">Loading...</div>
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
                      <tr key={comm.id} className="hover:bg-slate-50">
                        <td className="font-medium text-slate-900">{comm.subject}</td>
                        <td>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            comm.status === 'sent' ? 'bg-emerald-50 text-emerald-700' :
                            comm.status === 'draft' ? 'bg-amber-50 text-amber-700' :
                            'bg-slate-100 text-slate-600'
                          }`}>
                            {comm.status.charAt(0).toUpperCase() + comm.status.slice(1)}
                          </span>
                        </td>
                        <td className="font-data text-sm">{comm.recipient_count}</td>
                        <td className="text-slate-500">{comm.sent_at ? formatDate(comm.sent_at) : '—'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map((template) => (
              <div 
                key={template.id}
                className="bg-white border border-slate-200 rounded-lg p-5 hover:border-blue-200 transition-colors"
              >
                <FileText className="w-8 h-8 text-blue-500 mb-3" />
                <h3 className="font-semibold text-slate-900">{template.name}</h3>
                <p className="text-sm text-slate-500 mt-1">{template.description}</p>
                <Button variant="outline" size="sm" className="mt-4">
                  Use Template
                </Button>
              </div>
            ))}
            <button className="border-2 border-dashed border-slate-300 rounded-lg p-5 hover:border-slate-400 transition-colors text-center">
              <Plus className="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <p className="font-medium text-slate-600">Create Template</p>
            </button>
          </div>
        </TabsContent>

        {/* Segments Tab */}
        <TabsContent value="segments">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {segments.map((segment) => (
              <div 
                key={segment.id}
                className="bg-white border border-slate-200 rounded-lg p-5 hover:border-blue-200 transition-colors"
              >
                <div className="flex items-center justify-between mb-3">
                  <Users className="w-8 h-8 text-blue-500" />
                  <span className="text-2xl font-bold font-data text-slate-900">
                    {segment.count.toLocaleString()}
                  </span>
                </div>
                <h3 className="font-semibold text-slate-900">{segment.name}</h3>
                <div className="flex items-center gap-2 mt-4">
                  <Button variant="outline" size="sm">View List</Button>
                  <Button size="sm" className="btn-primary">
                    <Mail className="w-4 h-4 mr-1" />
                    Email
                  </Button>
                </div>
              </div>
            ))}
            <button className="border-2 border-dashed border-slate-300 rounded-lg p-5 hover:border-slate-400 transition-colors text-center">
              <Plus className="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <p className="font-medium text-slate-600">Create Segment</p>
            </button>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
