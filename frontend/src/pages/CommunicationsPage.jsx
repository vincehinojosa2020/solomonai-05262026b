import { useState, useEffect } from 'react';
import { Mail, Send, FileText, Users, Clock, MessageSquare, Plus, Search, ChevronRight, Loader2, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { API_URL, formatDate } from '@/lib/utils';
import { toast } from 'sonner';

export default function CommunicationsPage() {
  const [communications, setCommunications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('compose');
  const [sending, setSending] = useState(false);
  const [composeData, setComposeData] = useState({
    subject: '',
    body: '',
    channel: 'email',
    recipient_type: 'all',
    scheduled_at: '',
  });

  useEffect(() => { fetchCommunications(); }, []);

  const fetchCommunications = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('session_token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      const response = await fetch(`${API_URL}/admin/communications/list`, { headers });
      if (response.ok) {
        const data = await response.json();
        setCommunications(data.communications || []);
      }
    } catch (error) {
      console.error('Failed to fetch communications:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!composeData.subject || !composeData.body) {
      toast.error('Subject and body are required');
      return;
    }
    setSending(true);
    try {
      const token = localStorage.getItem('session_token');
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const res = await fetch(`${API_URL}/admin/communications/send`, {
        method: 'POST',
        headers,
        body: JSON.stringify(composeData),
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(data.message || 'Communication sent!');
        setComposeData({ subject: '', body: '', channel: 'email', recipient_type: 'all', scheduled_at: '' });
        fetchCommunications();
        setActiveTab('sent');
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to send');
      }
    } catch {
      toast.error('Failed to send communication');
    } finally {
      setSending(false);
    }
  };

  const templates = [
    { id: 1, name: 'Welcome Email', description: 'Send to new visitors', subject: 'Welcome to {church_name}!', body: 'Hi {first_name},\n\nWe are so glad you visited! We hope you felt at home with us.' },
    { id: 2, name: 'Prayer Request Follow-up', description: 'Pastoral care response', subject: 'Your Prayer Request', body: 'Hi {first_name},\n\nWe received your prayer request and our pastoral team is praying for you.' },
    { id: 3, name: 'Event Invitation', description: 'Promote upcoming events', subject: 'You are Invited!', body: 'Hi {first_name},\n\nWe have an exciting event coming up and we would love for you to join us!' },
    { id: 4, name: 'Giving Statement', description: 'Annual contribution summary', subject: 'Your {year} Giving Statement', body: 'Hi {first_name},\n\nThank you for your generous giving this year. Attached is your contribution statement.' },
    { id: 5, name: 'Volunteer Appreciation', description: 'Thank your team', subject: 'Thank You, Volunteer!', body: 'Hi {first_name},\n\nYour service makes such a difference. Thank you for giving your time!' },
  ];

  const segments = [
    { id: 1, name: 'All Active Members', count: 4287, icon: Users },
    { id: 2, name: 'New This Month', count: 127, icon: Plus },
    { id: 3, name: 'Inactive 90+ Days', count: 47, icon: Clock },
    { id: 4, name: 'Group Leaders', count: 84, icon: Users },
    { id: 5, name: 'Recurring Givers', count: 30, icon: Users },
    { id: 6, name: 'Upcoming Birthdays', count: 156, icon: Calendar },
  ];

  const sentComms = communications.filter(c => c.status === 'sent');
  const scheduledComms = communications.filter(c => c.status === 'scheduled');

  const loadTemplate = (tpl) => {
    setComposeData(prev => ({ ...prev, subject: tpl.subject, body: tpl.body }));
    setActiveTab('compose');
    toast.success(`Template "${tpl.name}" loaded`);
  };

  return (
    <div className="space-y-4" data-testid="communications-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Communications</h1>
          <p className="page-subtitle">Email, SMS, and messaging hub</p>
        </div>
        <div className="flex items-center gap-2">
          <Button className="btn-primary" onClick={() => setActiveTab('compose')} data-testid="compose-email-btn">
            <Mail className="w-4 h-4 mr-1" />
            Compose
          </Button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-white border border-slate-200 p-4 rounded-lg">
          <p className="text-2xl font-mono font-bold text-slate-900">{sentComms.length}</p>
          <p className="text-xs text-slate-500 font-medium mt-1">Sent This Month</p>
        </div>
        <div className="bg-white border border-slate-200 p-4 rounded-lg">
          <p className="text-2xl font-mono font-bold text-slate-900">{scheduledComms.length}</p>
          <p className="text-xs text-slate-500 font-medium mt-1">Scheduled</p>
        </div>
        <div className="bg-white border border-slate-200 p-4 rounded-lg">
          <p className="text-2xl font-mono font-bold text-slate-900">{templates.length}</p>
          <p className="text-xs text-slate-500 font-medium mt-1">Templates</p>
        </div>
        <div className="bg-white border border-slate-200 p-4 rounded-lg">
          <p className="text-2xl font-mono font-bold text-slate-900">{segments.length}</p>
          <p className="text-xs text-slate-500 font-medium mt-1">Segments</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-white border border-slate-200 p-1">
          <TabsTrigger value="compose" data-testid="tab-compose">Compose</TabsTrigger>
          <TabsTrigger value="sent" data-testid="tab-sent">Sent ({sentComms.length})</TabsTrigger>
          <TabsTrigger value="scheduled" data-testid="tab-scheduled">Scheduled ({scheduledComms.length})</TabsTrigger>
          <TabsTrigger value="templates" data-testid="tab-templates">Templates</TabsTrigger>
          <TabsTrigger value="segments" data-testid="tab-segments">Segments</TabsTrigger>
        </TabsList>

        {/* Compose Tab */}
        <TabsContent value="compose" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2 bg-white border border-slate-200 p-5 rounded-lg space-y-4">
              <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider">New Message</h3>

              <div className="flex gap-2">
                <button
                  onClick={() => setComposeData(p => ({ ...p, channel: 'email' }))}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${composeData.channel === 'email' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'}`}
                  data-testid="channel-email"
                >
                  <Mail className="w-3.5 h-3.5" /> Email
                </button>
                <button
                  onClick={() => setComposeData(p => ({ ...p, channel: 'sms' }))}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${composeData.channel === 'sms' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'}`}
                  data-testid="channel-sms"
                >
                  <MessageSquare className="w-3.5 h-3.5" /> SMS
                </button>
              </div>

              <div className="space-y-1">
                <Label className="text-xs font-semibold text-slate-600 uppercase">Recipients</Label>
                <select
                  value={composeData.recipient_type}
                  onChange={(e) => setComposeData(p => ({ ...p, recipient_type: e.target.value }))}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-md"
                  data-testid="recipients-select"
                >
                  <option value="all">All Active Members</option>
                  <option value="new">New This Month</option>
                  <option value="leaders">Group Leaders</option>
                  <option value="givers">Recurring Givers</option>
                  <option value="inactive">Inactive 90+ Days</option>
                </select>
              </div>

              <div className="space-y-1">
                <Label className="text-xs font-semibold text-slate-600 uppercase">Subject</Label>
                <Input
                  placeholder="Enter subject..."
                  value={composeData.subject}
                  onChange={(e) => setComposeData(p => ({ ...p, subject: e.target.value }))}
                  data-testid="subject-input"
                />
              </div>

              <div className="space-y-1">
                <Label className="text-xs font-semibold text-slate-600 uppercase">Message</Label>
                <Textarea
                  placeholder="Write your message... Use {first_name} for personalization."
                  className="min-h-[180px] resize-none"
                  value={composeData.body}
                  onChange={(e) => setComposeData(p => ({ ...p, body: e.target.value }))}
                  data-testid="body-input"
                />
                <p className="text-xs text-slate-400">Merge fields: {'{first_name}'}, {'{last_name}'}, {'{church_name}'}</p>
              </div>

              <div className="space-y-1">
                <Label className="text-xs font-semibold text-slate-600 uppercase">Schedule (Optional)</Label>
                <Input
                  type="datetime-local"
                  value={composeData.scheduled_at}
                  onChange={(e) => setComposeData(p => ({ ...p, scheduled_at: e.target.value }))}
                  data-testid="schedule-input"
                />
              </div>

              <div className="flex items-center gap-2 pt-2">
                <Button
                  onClick={handleSend}
                  disabled={sending}
                  className="btn-primary"
                  data-testid="send-btn"
                >
                  {sending ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Send className="w-4 h-4 mr-1" />}
                  {composeData.scheduled_at ? 'Schedule' : 'Send Now'}
                </Button>
              </div>
            </div>

            {/* Quick Templates sidebar */}
            <div className="space-y-4">
              <div className="bg-white border border-slate-200 p-4 rounded-lg">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Quick Templates</h3>
                <div className="space-y-1.5">
                  {templates.slice(0, 4).map((tpl) => (
                    <button
                      key={tpl.id}
                      onClick={() => loadTemplate(tpl)}
                      className="w-full p-2.5 text-left border border-slate-200 rounded-md hover:border-slate-300 hover:bg-slate-50 transition-colors"
                    >
                      <p className="text-sm font-medium text-slate-700">{tpl.name}</p>
                      <p className="text-xs text-slate-500">{tpl.description}</p>
                    </button>
                  ))}
                </div>
              </div>
              <div className="bg-white border border-slate-200 p-4 rounded-lg">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Quick Segments</h3>
                <div className="space-y-1.5">
                  {segments.slice(0, 4).map((seg) => (
                    <button
                      key={seg.id}
                      onClick={() => { setComposeData(p => ({ ...p, recipient_type: seg.name.toLowerCase().replace(/\s+/g, '_') })); }}
                      className="w-full p-2.5 text-left border border-slate-200 rounded-md hover:border-slate-300 hover:bg-slate-50 transition-colors flex items-center justify-between"
                    >
                      <span className="text-sm font-medium text-slate-700">{seg.name}</span>
                      <span className="text-xs font-mono text-slate-500">{seg.count.toLocaleString()}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Sent Tab */}
        <TabsContent value="sent">
          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Subject</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Channel</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Recipients</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Sent By</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Sent At</th>
                </tr>
              </thead>
              <tbody>
                {sentComms.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-12 text-slate-400">
                      <Mail className="w-8 h-8 mx-auto mb-2 opacity-40" />
                      <p className="text-sm">No messages sent yet</p>
                    </td>
                  </tr>
                ) : (
                  sentComms.map((comm) => (
                    <tr key={comm.id} className="border-b border-slate-100 hover:bg-slate-50" data-testid={`sent-row-${comm.id}`}>
                      <td className="px-4 py-3 font-medium text-slate-700">{comm.subject || '(No subject)'}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${comm.channel === 'sms' ? 'bg-purple-50 text-purple-700' : 'bg-blue-50 text-blue-700'}`}>
                          {comm.channel === 'sms' ? <MessageSquare className="w-3 h-3" /> : <Mail className="w-3 h-3" />}
                          {comm.channel?.toUpperCase() || 'EMAIL'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-500">{comm.recipient_type || 'All'}</td>
                      <td className="px-4 py-3 text-slate-500">{comm.sent_by || '--'}</td>
                      <td className="px-4 py-3 text-slate-500">{comm.sent_at ? new Date(comm.sent_at).toLocaleString() : '--'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </TabsContent>

        {/* Scheduled Tab */}
        <TabsContent value="scheduled" data-testid="scheduled-tab">
          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Subject</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Channel</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Recipients</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase">Scheduled For</th>
                </tr>
              </thead>
              <tbody>
                {scheduledComms.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="text-center py-12 text-slate-400">
                      <Clock className="w-8 h-8 mx-auto mb-2 opacity-40" />
                      <p className="text-sm">No scheduled messages</p>
                      <p className="text-xs mt-1">Use the compose tab to schedule future messages</p>
                    </td>
                  </tr>
                ) : (
                  scheduledComms.map((comm) => (
                    <tr key={comm.id} className="border-b border-slate-100 hover:bg-slate-50" data-testid={`scheduled-row-${comm.id}`}>
                      <td className="px-4 py-3 font-medium text-slate-700">{comm.subject || '(No subject)'}</td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700">
                          <Clock className="w-3 h-3" /> Scheduled
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-500">{comm.recipient_type || 'All'}</td>
                      <td className="px-4 py-3 text-slate-500">{comm.scheduled_at ? new Date(comm.scheduled_at).toLocaleString() : '--'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {templates.map((tpl) => (
              <div key={tpl.id} className="bg-white border border-slate-200 p-5 rounded-lg hover:border-slate-300 transition-colors">
                <FileText className="w-5 h-5 text-slate-400 mb-3" />
                <h3 className="text-sm font-semibold text-slate-800">{tpl.name}</h3>
                <p className="text-xs text-slate-500 mt-1 mb-3">{tpl.description}</p>
                <Button variant="outline" size="sm" onClick={() => loadTemplate(tpl)} className="text-xs">
                  Use Template <ChevronRight className="w-3 h-3 ml-1" />
                </Button>
              </div>
            ))}
            <button className="border border-dashed border-slate-300 p-5 rounded-lg hover:border-slate-400 transition-colors text-center">
              <Plus className="w-5 h-5 text-slate-400 mx-auto mb-2" />
              <p className="text-xs font-medium text-slate-600">Create Template</p>
            </button>
          </div>
        </TabsContent>

        {/* Segments Tab */}
        <TabsContent value="segments">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {segments.map((seg) => (
              <div key={seg.id} className="bg-white border border-slate-200 p-5 rounded-lg hover:border-slate-300 transition-colors">
                <div className="flex items-center justify-between mb-3">
                  <seg.icon className="w-5 h-5 text-slate-400" />
                  <span className="text-xl font-mono font-bold text-slate-900">{seg.count.toLocaleString()}</span>
                </div>
                <h3 className="text-sm font-semibold text-slate-800">{seg.name}</h3>
                <div className="flex items-center gap-2 mt-3">
                  <Button variant="outline" size="sm" className="text-xs flex-1">View</Button>
                  <Button
                    size="sm"
                    className="btn-primary text-xs flex-1"
                    onClick={() => { setComposeData(p => ({ ...p, recipient_type: seg.name })); setActiveTab('compose'); }}
                  >
                    <Mail className="w-3 h-3 mr-1" /> Email
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
