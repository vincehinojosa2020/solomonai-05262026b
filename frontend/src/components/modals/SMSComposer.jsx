import { useState, useEffect } from 'react';
import { X, MessageSquare, Users, Send, Loader2, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { API_URL } from '@/lib/utils';

export default function SMSComposer({ onClose, preselectedRecipient, preselectedGroup }) {
  const [mode, setMode] = useState('individual'); // individual, group
  const [recipientPhone, setRecipientPhone] = useState(preselectedRecipient?.phone || '');
  const [recipientName, setRecipientName] = useState(preselectedRecipient?.name || '');
  const [selectedGroup, setSelectedGroup] = useState(preselectedGroup || '');
  const [message, setMessage] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [templates, setTemplates] = useState([]);
  const [groups, setGroups] = useState([]);
  const [loading, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const MAX_SMS_LENGTH = 160;
  const remainingChars = MAX_SMS_LENGTH - message.length;

  useEffect(() => {
    // Fetch templates
    fetch(`${API_URL}/sms/templates`)
      .then(res => res.json())
      .then(data => setTemplates(data))
      .catch(err => console.error('Failed to fetch templates:', err));
    
    // Fetch groups
    fetch(`${API_URL}/groups`)
      .then(res => res.json())
      .then(data => setGroups(data))
      .catch(err => console.error('Failed to fetch groups:', err));
  }, []);

  const handleTemplateSelect = (templateId) => {
    setSelectedTemplate(templateId);
    const template = templates.find(t => t.id === templateId);
    if (template) {
      // Replace placeholders with defaults for preview
      let content = template.content;
      content = content.replace('{church_name}', 'Abundant Church');
      content = content.replace('{event_name}', 'Sunday Service');
      content = content.replace('{event_date}', 'this Sunday');
      content = content.replace('{group_name}', 'Your Group');
      content = content.replace('{day}', 'Wednesday');
      content = content.replace('{time}', '7:00 PM');
      content = content.replace('{amount}', '100.00');
      setMessage(content);
    }
  };

  const handleSend = async () => {
    if (!message.trim()) {
      setError('Please enter a message');
      return;
    }

    setSending(true);
    setError(null);

    try {
      if (mode === 'individual') {
        if (!recipientPhone.trim()) {
          setError('Please enter a phone number');
          setSending(false);
          return;
        }

        const response = await fetch(`${API_URL}/sms/send`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            recipient_phone: recipientPhone,
            message: message,
            person_id: preselectedRecipient?.id || null,
          }),
        });

        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'Failed to send SMS');
        }

        const data = await response.json();
        setResult(data);
      } else {
        // Bulk SMS
        if (!selectedGroup) {
          setError('Please select a group');
          setSending(false);
          return;
        }

        const response = await fetch(`${API_URL}/sms/bulk`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            group_id: selectedGroup,
            message: message,
          }),
        });

        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'Failed to send bulk SMS');
        }

        const data = await response.json();
        setResult(data);
      }

      setSent(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  };

  // Success state
  if (sent) {
    return (
      <div className="slide-panel-overlay" onClick={onClose}>
        <div className="slide-panel" onClick={e => e.stopPropagation()}>
          <div className="flex flex-col items-center justify-center h-full p-8">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Message Sent!</h3>
            <p className="text-sm text-slate-500 text-center mb-2">
              {mode === 'individual' 
                ? `SMS sent to ${recipientPhone}`
                : `SMS queued for ${result?.total_recipients || 0} recipients`
              }
            </p>
            {result?.mock && (
              <p className="text-xs text-amber-600 bg-amber-50 px-3 py-1.5 mb-4">
                Demo mode - Twilio not configured
              </p>
            )}
            <Button onClick={onClose} className="btn-primary">
              Done
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="slide-panel-overlay" onClick={onClose}>
      <div className="slide-panel" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="slide-panel-header">
          <div>
            <h2 className="slide-panel-title">Send SMS</h2>
            <p className="text-xs text-slate-500 mt-0.5">Text message communication</p>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="slide-panel-content space-y-5">
          {/* Error message */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Mode Toggle */}
          <div className="flex gap-2">
            <button
              onClick={() => setMode('individual')}
              className={`flex-1 flex items-center justify-center gap-2 p-3 border transition-colors ${
                mode === 'individual'
                  ? 'bg-blue-600 border-blue-600 text-white'
                  : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              Individual
            </button>
            <button
              onClick={() => setMode('group')}
              className={`flex-1 flex items-center justify-center gap-2 p-3 border transition-colors ${
                mode === 'group'
                  ? 'bg-blue-600 border-blue-600 text-white'
                  : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300'
              }`}
            >
              <Users className="w-4 h-4" />
              Group
            </button>
          </div>

          {/* Recipient */}
          {mode === 'individual' ? (
            <div className="form-group">
              <label className="form-label">Recipient</label>
              <input
                type="tel"
                value={recipientPhone}
                onChange={(e) => setRecipientPhone(e.target.value)}
                placeholder="+1 (555) 123-4567"
                className="form-input"
              />
              {recipientName && (
                <p className="text-xs text-slate-500 mt-1">{recipientName}</p>
              )}
            </div>
          ) : (
            <div className="form-group">
              <label className="form-label">Select Group</label>
              <select
                value={selectedGroup}
                onChange={(e) => setSelectedGroup(e.target.value)}
                className="form-input"
              >
                <option value="">Choose a group...</option>
                {groups.map(group => (
                  <option key={group.id} value={group.id}>
                    {group.name} ({group.member_count || 0} members)
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Template Selection */}
          <div className="form-group">
            <label className="form-label">Template (Optional)</label>
            <select
              value={selectedTemplate}
              onChange={(e) => handleTemplateSelect(e.target.value)}
              className="form-input"
            >
              <option value="">Select a template...</option>
              {templates.map(template => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
          </div>

          {/* Message */}
          <div className="form-group">
            <div className="flex items-center justify-between mb-1">
              <label className="form-label mb-0">Message</label>
              <span className={`text-xs font-mono ${remainingChars < 20 ? 'text-red-500' : 'text-slate-400'}`}>
                {remainingChars} chars remaining
              </span>
            </div>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value.slice(0, MAX_SMS_LENGTH))}
              placeholder="Type your message..."
              rows={4}
              className="form-input resize-none"
              style={{ height: 'auto' }}
            />
          </div>

          {/* Preview */}
          {message && (
            <div className="bg-slate-900 rounded p-4">
              <p className="text-xs text-slate-400 mb-2">Preview</p>
              <div className="bg-slate-800 rounded-lg p-3 max-w-[280px]">
                <p className="text-sm text-white whitespace-pre-wrap">{message}</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="slide-panel-footer">
          <Button variant="outline" onClick={onClose} className="btn-secondary">
            Cancel
          </Button>
          <Button 
            onClick={handleSend}
            disabled={loading || !message.trim()}
            className="btn-primary"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Sending...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Send {mode === 'group' ? 'to Group' : 'SMS'}
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
